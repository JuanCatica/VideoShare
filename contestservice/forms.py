from django import forms
from acceso.models import UserProfileInfo
from django.contrib.auth.models import User
from django.forms import DateTimeField
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Video

class VideoForm(forms.ModelForm):
    """
    Formulrio de Carga de Video
    """

    EN_PROCESO = "En Proceso"
    CONVERTIDO  = "Convertido"
    STATE = [
        (EN_PROCESO,"En Proceso"),
        (CONVERTIDO,"Convertido"),
    ]

    title = forms.CharField(label="title", required=True, widget=forms.TextInput(    
        attrs={'class':'form-control', 'placeholder':'Título del Video'},
    ))

    first_name_competitor = forms.CharField(label="first_name_competitor", required=True, widget=forms.TextInput(
        attrs={'class':'form-control', 'placeholder':'Nombres'}
    ))

    last_name_competitor = forms.CharField(label="last_name_competitor", required=True, widget=forms.TextInput(
        attrs={'class':'form-control', 'placeholder':'apellidos'}
    ))

    email_competitor = forms.CharField(label="email_competitor", required=True, widget=forms.TextInput(
        attrs={'class':'form-control', 'placeholder':'e-mail'}, 
    ))

    description = forms.CharField(label="description", required=True, widget=forms.Textarea(
        attrs={'class':'form-control', 'placeholder':'diección del video', 'rows':3},
    ))

    state = forms.CharField(label="state", required=False, widget=forms.Select(
        choices=STATE, attrs={'class':'form-control', 'placeholder':'Descripción del evento'},
    ))

    videofile = forms.FileField(label="videofile", required=True,) 

    class Meta:
        model = Video
        fields = ('title','first_name_competitor','last_name_competitor','email_competitor','description','state','videofile')                            