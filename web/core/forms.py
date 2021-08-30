from django import forms
from acceso.models import UserProfileInfo
from django.contrib.auth.models import User
from django.forms import DateTimeField
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Contest

class ContestForm(forms.ModelForm):
    """
    Formulrio de Concurso
    """

    name_contest = forms.CharField(label="name_contest", required=True, widget=forms.TextInput(    
        attrs={'class':'form-control', 'placeholder':'Nombre del Concurso'},
    ))

    url = forms.CharField(label="url", required=True, widget=forms.TextInput(
       attrs={'class':'form-control', 'placeholder':'URL'}
    ))

    description = forms.CharField(label="description", required=True, widget=forms.Textarea(
        attrs={'class':'form-control', 'placeholder':'Explica como es tu grandioso concurso', 'rows':3}
    ))

    image = forms.ImageField(label="image", required=False)  

    start_date = forms.DateTimeField(label="start_date", required=True)

    end_date = forms.DateTimeField(label="end_date", required=True)          

    class Meta:
        model = Contest
        fields = ('name_contest','url','description','image','start_date','end_date')            


