# 🛡️ Sistema de Detección de Violencia en Videos – Django + TensorFlow

Este proyecto es un sistema web desarrollado en Django que permite subir videos y detectar automáticamente si contienen contenido violento utilizando modelos de inteligencia artificial (IA) previamente entrenados con TensorFlow.

## 🚀 Requisitos

- Python 3.8 o superior  
- pip  
- Git (opcional para clonar el repositorio)  
- Virtualenv (recomendado)

---

## ⚙️ Instalación y Configuración

Sigue los pasos a continuación para levantar el proyecto localmente:

### 1. Crear un entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 2. Instalar las dependencias del proyecto

```bash
pip install -r requirements.txt
```

---

### 3. Aplicar migraciones a la base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 4. Crear un superusuario (opcional)

```bash
python manage.py createsuperuser
```

---

### 5. Descargar los modelos de IA

Abre el siguiente enlace en tu navegador para descargar automáticamente los modelos necesarios:

```
http://127.0.0.1:8000/descargar_modelos/
```

---

### 6. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

---

### 7. Acceder a la aplicación

Abre tu navegador y visita:

```
http://127.0.0.1:8000/
```

---

## 🧠 Descripción del Sistema

- Permite subir uno o varios videos a la vez.
- Cada video es procesado por un modelo de IA que determina si contiene violencia o no.
- Se generan miniaturas de los videos para facilitar su visualización.
- Los usuarios pueden confirmar si el análisis fue correcto.
- Una vez confirmados, los videos se marcan como “analizados correctamente” y se conservan como evidencia optimizando el uso del almacenamiento.
- El panel de administración está disponible para usuarios con cuenta de superusuario.

---

## 📁 Estructura del Proyecto

- `media/`: Carpeta donde se almacenan los videos subidos.  
- `static/`: Archivos estáticos como CSS o JS.  
- `templates/`: Archivos HTML de la interfaz.  
- `modelo/`: Ruta del modelo entrenado en TensorFlow (`.h5`) descargado automáticamente.

---

## 📌 Notas Adicionales

- Asegúrate de tener conexión a internet durante la descarga del modelo.  
- Este sistema está orientado a fines educativos, pero puede adaptarse a entornos productivos con configuraciones adecuadas.  
- Para entornos de producción se recomienda el uso de Gunicorn y Nginx, así como bases de datos robustas como PostgreSQL.

---

## 👨‍💻 Autor

**Rubén Alejandro Torres Sánchez**  
Estudiante de Ingeniería en Sistemas y Computación  
Universidad Dr. Andrés Bello

  
