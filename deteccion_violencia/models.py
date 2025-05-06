import os
from django.conf import settings
from django.db import models 
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError

# Gerenciador de usuario personalizado
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email debe ser proporcionado")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# Modelo de usuario personalizado
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, default='')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name'] 

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# Modelo para almacenar los videos subidos

class Video(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='videos')
    file_path = models.FileField(upload_to='videos/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    prediction = models.BooleanField(default=False)
    analysis_status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('completed', 'Completed')], 
        default='pending'
    )
    feedback_status = models.CharField(
        max_length=20,
        choices=[
            ('none', 'Sin feedback'),
            ('incorrect', 'Feedback incorrecto'),
            ('resolved', 'Feedback resuelto'),
        ],
        default='none'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_file_deleted = models.BooleanField(default=False)

    def delete_file(self):
        if self.file_path and os.path.exists(self.file_path.path):
            os.remove(self.file_path.path)
            self.file_path = None
            self.is_file_deleted = True
            self.save()

class Feedback(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField()
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('resolved', 'Resuelto'),
            ('failed', 'No resuelto')
        ],
        default='pending'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Feedback: {'Correcto' if self.is_correct else 'Incorrecto'} - Estado: {self.status}"
