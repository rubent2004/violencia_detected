# deteccion_violencia/predit.py

import os
import cv2
import tensorflow as tf
import numpy as np

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile

from .models import Video

# Variables globales para caché
_model_cnn = None
_model_base = None

def _cargar_modelos():
    """
    Carga los modelos H5 sólo la primera vez. 
    Lanza ImproperlyConfigured si faltan los archivos.
    """
    global _model_cnn, _model_base

    if _model_cnn is not None and _model_base is not None:
        return _model_cnn, _model_base

    # Rutas a los archivos
    ruta1 = os.path.join(settings.MEDIA_ROOT, 'models', 'model.Copy.h5')
    ruta2 = os.path.join(settings.MEDIA_ROOT, 'models', 'base.h5')

    # Verificar existencia
    faltantes = [p for p in (ruta1, ruta2) if not os.path.exists(p)]
    if faltantes:
        raise ImproperlyConfigured(
            f"Modelos no encontrados en disco: {', '.join(faltantes)}. "
            "Ejecuta la descarga o súbelos a media/models."
        )

    # Carga
    _model_cnn = tf.keras.models.load_model(ruta1)
    _model_base = tf.keras.models.load_model(ruta2)
    return _model_cnn, _model_base


def leer_video(ruta):
    frames = []
    vidcap = cv2.VideoCapture(ruta)
    if not vidcap.isOpened():
        print(f"Error: No se pudo abrir el video en {ruta}")
        return frames
    exito, imagen = vidcap.read()
    if not exito:
        print(f"Error: No se pudo leer el primer frame del video en {ruta}")
        return frames
    while exito:
        imagen = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        frames.append(cv2.resize(imagen, (224, 224)))
        exito, imagen = vidcap.read()
    vidcap.release()
    if not frames:
        print(f"Error: No se capturaron frames del video en {ruta}.")
    return frames


def extraer_caracteristicas_imagen(frames):
    _, model_base = _cargar_modelos()
    conv_features = model_base.predict(np.array(frames))
    return np.array(conv_features)


def redimensionar_con_ceros(img_features, max_frames):
    rows, cols = img_features.shape
    if rows > max_frames:
        return img_features[:max_frames, :]
    zero_mat = np.zeros((max_frames - rows, cols))
    return np.concatenate((img_features, zero_mat), axis=0)


def detectar_y_aprender(video_path, threshold=0.5, maxFrames=190):
    # Asegurarse de tener los modelos cargados o lanzar error
    model_cnn, _ = _cargar_modelos()

    frames = leer_video(video_path)
    if not frames:
        raise ValueError("El video no pudo ser leído o está vacío.")

    img_features = extraer_caracteristicas_imagen(frames)
    img_features = redimensionar_con_ceros(img_features, maxFrames)

    prediction = model_cnn.predict(np.array([img_features]))[0][0]

    # Guardar en BD
    video_name = os.path.basename(video_path)
    video_path_in_db = f'videos/{video_name}'
    try:
        video = Video.objects.get(file_path=video_path_in_db)
        video.prediction = prediction >= threshold
        video.analysis_status = 'completed'
        video.save()
    except Video.DoesNotExist:
        raise ValueError("El video no existe en la base de datos.")

    return prediction


def actualizar_modelo_con_retroalimentacion(video_path, label, maxFrames):
    model_cnn, _ = _cargar_modelos()

    frames = leer_video(video_path)
    img_features = extraer_caracteristicas_imagen(frames)
    img_features = redimensionar_con_ceros(img_features, maxFrames)
    label = np.array([label])

    optimizer = tf.keras.optimizers.Adam()
    model_cnn.compile(optimizer=optimizer,
                      loss='binary_crossentropy',
                      metrics=['accuracy'])
    model_cnn.fit(np.array([img_features]),
                  label,
                  epochs=1,
                  verbose=1)


def generate_thumbnail(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("No se pudo abrir el video.")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        raise ValueError("No se pudo leer el frame del video.")

    h, w = frame.shape[:2]
    max_size = 500
    if w > h:
        new_w = max_size
        new_h = int(h * (max_size / w))
    else:
        new_h = max_size
        new_w = int(w * (max_size / h))
    thumbnail = cv2.resize(frame, (new_w, new_h))
    thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
    success, buffer = cv2.imencode('.jpg', thumbnail,
                                   [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise ValueError("No se pudo codificar la miniatura.")

    return ContentFile(buffer.tobytes())
