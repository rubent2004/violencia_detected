from django.contrib import admin
from .models import CustomUser, Video, Feedback
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

class CustomUserAdmin(UserAdmin):
    # Especificamos los campos que queremos mostrar en el panel de administración
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    # Para el formulario de creación y edición
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),  # Incluimos username aquí
        ('Información Personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('is_active', 'is_staff')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff')}
        ),
    )
    # Removemos 'filter_horizontal' ya que 'groups' y 'user_permissions' no están definidos en CustomUser
    filter_horizontal = ()  # Asegúrate de que esto esté vacío

    # Define el método para usar en la vista de detalle
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('videos')

# Registra el modelo de usuario personalizado
admin.site.register(CustomUser, CustomUserAdmin)

# Registro de otros modelos
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file_path', 'prediction', 'analysis_status', 'created_at')
    list_filter = ('prediction', 'analysis_status', 'created_at')
    search_fields = ('user__email', 'file_path', 'user__username')
    ordering = ('-created_at',)  # Orden descendente para ver los videos más recientes primero
    readonly_fields = ('created_at',)
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="auto" />', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Miniatura'

# Personalización del administrador para Feedback
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('video', 'is_correct', 'created_at', 'thumbnail_preview')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('video__file_path', 'video__user__email')
    ordering = ('-created_at',)  # Orden descendente para ver los comentarios más recientes primero

    # Método para mostrar la miniatura en la interfaz de administración
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="auto" />', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Miniatura'
    readonly_fields = ('thumbnail_preview',)

    fieldsets = (
        (None, {'fields': ('video', 'is_correct', 'created_at')}),
        ('Miniatura', {'fields': ('thumbnail', 'thumbnail_preview')}),
    )