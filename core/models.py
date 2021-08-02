from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Contest(models.Model):
    """
    Clase implementada para modelar los concursos.
    """

    #id_contest = models.IntegerField(verbose_name="Id Concurso", primary_key=True, unique=True, auto_created=True, serialize=False, editable=False)
    #id = models.IntegerField(verbose_name="Id Concurso", primary_key=True, unique=True, auto_created=True, serialize=False, editable=False) #
    fk_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario", related_name="usuario") ###
    name_contest = models.CharField(verbose_name="Nombre", max_length=200) # , unique=True | lanza una excepcion durante la acrualización
    url = models.CharField(verbose_name="URL", max_length=200)
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(verbose_name="Imagen", upload_to="contests", null=True , blank=True, ) 
    start_date = models.DateTimeField(verbose_name="Fecha Creación") 
    end_date = models.DateTimeField(verbose_name="Fecha Modificación") 
    created = models.DateTimeField(verbose_name="Fecha Creación", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Fecha Modificación", auto_now=True)

    class Meta:
        verbose_name = "Concurso"
        verbose_name_plural = "Concursos"
        ordering = ['-created']

    def __str__(self):
        return self.name_contest