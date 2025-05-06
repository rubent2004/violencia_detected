import cv2
from django.shortcuts import render, redirect
from .models import Video
from django.core.files.base import ContentFile
import numpy as np
import os

def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES['video']
        video = Video(user=request.user, file_path=video_file)
        video.save()  # Guarda el video antes de procesar la miniatura

        # Generar miniatura
        thumbnail = generate_thumbnail(video.file_path.path)  # Llama a la función para generar la miniatura
        video.thumbnail_url.save(f'thumbnail_{os.path.basename(video_file.name)}.jpg', thumbnail)  # Guarda la miniatura
        video.save()  # Guarda la miniatura

        return redirect('pagina_de_carga')  # Redirige a la página de carga

def generate_thumbnail(video_path):
    # Capturar el primer frame del video
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()

    if not ret:
        raise ValueError("No se pudo leer el video.")

    # Redimensionar el frame para que sea la miniatura
    thumbnail = cv2.resize(frame, (120, 80))
    
    # Convertir el frame a JPEG
    _, buffer = cv2.imencode('.jpg', thumbnail)
    thumb_file = ContentFile(buffer.tobytes(), name='thumbnail.jpg')

    cap.release()
    return thumb_file