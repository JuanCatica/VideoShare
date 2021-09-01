from django import forms
from acceso.models import UserProfileInfo
from django.contrib.auth.models import User


class UserForm(forms.ModelForm):
    """
    Formulario de registro, asociado a:
        Template: acceso/templates/acceso/register.html
        View:     acceso/views.register   [method]
        Url:      acceso/urls.py   |   register/
    """
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta():
        model = User
        fields = ('username','first_name','last_name','email','password')


class UserProfileInfoForm(forms.ModelForm):
    """
    Formulario de registro, asociado a: SIN CONECTAR
    """
    class Meta():
        model = UserProfileInfo
        fields = ('user_img',)