from django.db import models
from core.models import Contest

# Create your models here.
class Video(models.Model):
    """
    Clase implementada para modelar los videos cargados por los participantes.
    """
    EN_PROCESO = "En Proceso"
    CONVERTIDO  = "Convertido"
    STATE = [
        (EN_PROCESO,"En Proceso"),
        (CONVERTIDO,"Convertido"),
    ]
    #id_video = models.IntegerField(verbose_name="Id Video", primary_key=True, unique=True, auto_created=True, editable=False) 
    #id = models.IntegerField(verbose_name="Id Video", primary_key=True, unique=True, auto_created=True, serialize=False, editable=False) # Este cambio no funcionó 
    fk_contest = models.ForeignKey(Contest, on_delete=models.CASCADE, verbose_name="Concurso", related_name="concurso")
    title = models.CharField(verbose_name="Título", max_length=200)
    first_name_competitor = models.CharField(verbose_name="Nombre Competidor", max_length=200)
    last_name_competitor = models.CharField(verbose_name="apellido Competidor", max_length=200)
    email_competitor = models.CharField(verbose_name="e-mail Competidor", max_length=200)
    description = models.TextField(verbose_name="Descripción")
    state = models.CharField(verbose_name="Estado Video", default=EN_PROCESO, choices=STATE, max_length=12)
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(verbose_name="Imagen", upload_to="videos_image", null=True , blank=True, ) 
    videofile= models.FileField(verbose_name="Video", upload_to='videos')
    videofile_format = models.FileField(verbose_name="Video Formateado", upload_to='videos_ffmpeg')
    positives = models.IntegerField(verbose_name="Positivos", default=0)
    negatives = models.IntegerField(verbose_name="Negativos", default=0)
    load_date = models.DateTimeField(verbose_name="Fecha Carga", auto_now_add=True) 
    updated = models.DateTimeField(verbose_name="Fecha Modificación", auto_now=True)

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-load_date']

    def __str__(self):
        return self.title