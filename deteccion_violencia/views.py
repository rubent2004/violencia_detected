from django.http import JsonResponse
from django.utils import timezone
import os
import threading
from django.dispatch import receiver
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_out
import gdown
import requests

from Django_crud import settings
from .models import Video, Feedback
from .predit import detectar_y_aprender, actualizar_modelo_con_retroalimentacion
from django.core.exceptions import ValidationError
from django.db.models import Count
import cv2
from django.core.files.base import ContentFile
import numpy as np
import os

def generate_thumbnail(video_path):
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError("No se pudo abrir el video.")
    
    # Intentamos leer el frame del medio del video para una mejor miniatura
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames > 0:
        # Nos movemos a la mitad del video
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise ValueError("No se pudo leer el frame del video.")

    # Mantener la relación de aspecto
    height, width = frame.shape[:2]
    max_size = 500
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    thumbnail = cv2.resize(frame, (new_width, new_height))
    
    # Convertir de BGR a RGB
    thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
    
    # Codificar la miniatura a JPEG
    success, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise ValueError("No se pudo codificar la miniatura.")

    return ContentFile(buffer.tobytes())  # Devuelve el archivo de imagen como ContentFile

@login_required
def index(request):
    error = None

    if request.method == 'POST':
        video_files = request.FILES.getlist('video')
        if not video_files:
            error = "Por favor, selecciona al menos un archivo de video."
        else:
            for video_file in video_files:
                # Evita duplicados
                if Video.objects.filter(file_path='videos/' + video_file.name).exists():
                    error = f"El video '{video_file.name}' ya ha sido subido anteriormente."
                    continue

                # Guardar Video
                video = Video(
                    user=request.user,
                    file_path=video_file,
                    prediction=False,
                    analysis_status='pending'
                )
                try:
                    video.full_clean()
                    video.save()

                    # Generar y guardar miniatura
                    try:
                        thumb = generate_thumbnail(video.file_path.path)
                        thumbnail_name = f'thumbnail_{video.id}_miniatura.jpg'
                        video.thumbnail.save(thumbnail_name, thumb, save=True)
                    except Exception as e:
                        error = f"Error al generar la miniatura de '{video_file.name}': {e}"
                        continue

                except ValidationError as ve:
                    error = ', '.join(ve.messages)
                    continue

            if not error:
                return redirect('pagina_de_carga')

    # Calcular qué modelos faltan
    modelos_faltantes = []
    for nombre in settings.MODEL_DRIVE_LINKS:
        ruta = os.path.join(settings.MODEL_DIR, nombre)
        if not os.path.exists(ruta):
            modelos_faltantes.append(nombre)

    return render(request, 'violencia/index.html', {
        'error': error,
        'modelos_faltantes': modelos_faltantes,
    })


@login_required
def pagina_de_carga(request):
    videos = Video.objects.filter(user=request.user)  # Cargar todos los videos del usuario
    
    print(f"Videos pendientes: {[video.file_path.name for video in videos if video.analysis_status == 'pending']}")  # Verifica los videos

    is_processing = False  # Inicialmente no está procesando

    # Recorremos los videos para analizarlos si están pendientes
    for video in videos:    
        if video.analysis_status != 'pending':
            continue  # Salta si el video ya fue analizado
        
        is_processing = True  # Indica que se está procesando un video
        
        try:
            print(f"Ruta del video: {video.file_path.path}")  # Imprime la ruta del video
            prediction = detectar_y_aprender(video.file_path.path, threshold=0.5, maxFrames=190)
            print(f"Predicción para {video.file_path.name}: {prediction}")  # Imprimir el valor de predicción
            
            video.prediction = int(prediction > 0.5)  # Asignar predicción
            video.analysis_status = 'completed'  # Cambia el estado
            video.save()
            print(f"Estado del análisis para {video.file_path.name}: {video.analysis_status}")  # Confirmar estado
        except ValueError as e:
            print(f"Error en la predicción: {e}")  # Imprime el error en la predicción

    # Renderiza la página con los videos y el estado de procesamiento
    return render(request, 'violencia/pagina_de_carga.html', {'videos': videos, 'is_processing': is_processing})

def retroalimentar_video(request):
    if request.method == 'POST':
        video_id = request.POST.get('video_id')
        feedback_value = request.POST.get('feedback') == 'true'  # True si el feedback es correcto
        video = get_object_or_404(Video, id=video_id, user=request.user)

        # Verifica si ya existe un feedback para este video
        feedback = Feedback.objects.filter(video=video).first()

        if feedback is None:  # Si no existe el feedback, lo crea
            feedback = Feedback.objects.create(
                video=video,
                is_correct=feedback_value,
                status='pending',  # Estado inicial
                resolved_at=None  # No resuelto aún
            )
        
        # Si el feedback es correcto
        if feedback_value:
            feedback.status = 'resolved'
            video.feedback_status = 'resolved'
            feedback.resolved_at = timezone.now()  # Establece el timestamp de resolución
            feedback.save()  
            video.save()

        # Si el feedback es incorrecto
        else:
            feedback.status = 'failed'  # En la base de datos se guarda como 'failed'
            video.feedback_status = 'incorrect'  # Cambiar a 'incorrect' para que coincida con la plantilla
            feedback.save()  # Guarda el feedback como 'failed'
            video.save()

            try:
                # Actualiza el modelo con la retroalimentación incorrecta (por ejemplo, reentrenando con la información)
                actualizar_modelo_con_retroalimentacion(video.file_path.path, 1, maxFrames=190)

                # Vuelve a pasar el video por el modelo para verificar si el aprendizaje mejora
                prediction = detectar_y_aprender(video.file_path.path, threshold=0.5, maxFrames=190)
                video.prediction = int(prediction > 0.5)

                # Después de procesar, actualizamos el feedback a "resolved"
                feedback.status = 'resolved'
                feedback.resolved_at = timezone.now()
                feedback.save()

            except Exception as e:
                print(f"Error al actualizar el modelo: {e}")
                feedback.status = 'failed'
                video.feedback_status = 'failed'
                feedback.resolved_at = None
                feedback.save()  # Guarda el feedback con el estado 'failed' si ocurre un error
                video.save()
        
        # Guarda el video con la posible actualización de la predicción
        video.save()

    return redirect('pagina_de_carga')
def eliminar_videos(user):
    videos = Video.objects.filter(user=user)
    for video in videos:
        video.delete_file()  # Solo elimina los archivos físicos


@receiver(user_logged_out)
def eliminar_videos_al_cerrar_sesion(sender, request, user, **kwargs):
    # Llamar la función de eliminación de videos inmediatamente
    eliminar_videos(user)

    
@login_required
def estadisticas_view(request):
    correctos = Feedback.objects.filter(is_correct=True).count()
    incorrectos = Feedback.objects.filter(is_correct=False).count()
    print(f"Correctos: {correctos}, Incorrectos: {incorrectos}")  # Verificación
    context = {
        'correctos': correctos,
        'incorrectos': incorrectos,
    }
    return render(request, 'violencia/estadisticas.html', context)


@login_required
def descargar_modelos(request):
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    resultados = {}

    for nombre, url in settings.MODEL_DRIVE_LINKS.items():
        destino = os.path.join(settings.MODEL_DIR, nombre)

        if os.path.exists(destino):
            resultados[nombre] = 'ya existe'
            continue

        try:
            # gdown se encargará del confirm token si hace falta
            gdown.download(
                url,
                destino,
                quiet=False  # True para silencioso
            )
            resultados[nombre] = 'descargado'
        except Exception as e:
            resultados[nombre] = f'error: {e}'

    return JsonResponse(resultados)