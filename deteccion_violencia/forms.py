from django import forms
from .models import Video

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['file_path']  # Cambia a 'file_path' si el campo se llama así en tu modelo
        widgets = {
            'file_path': forms.FileInput(attrs={'required': 'required'}),
        }