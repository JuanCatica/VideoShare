from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from videoshare.settings import *
from acceso.forms import UserForm,UserProfileInfoForm
from django.contrib.auth.models import User

# Create your views here.
def info_view(request):
    """
    Pagina de inicio.
    """
    return render(request, "acceso/info.html")

def login_view(request):
    """
    Pagina de login.
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    return render(request, "acceso/login.html")

def singin_view(request):
    """
    Visualización de la pagina de registro.
    """
    logout(request)
    return render(request, "acceso/singin.html")

def register(request):
    """
    Accion de registro de la pagina.
    """
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            registered = True
        else:
            print(user_form.errors)
    else:
        user_form = UserForm()
    return render(request,'acceso/register.html', {'user_form':user_form,'registered':registered})

def login_action(request):
    """
    Accion de entrada a la pagina para usuarios registrados.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except:
            return render(request, 'acceso/login.html',{'message':"Ese correo que nos diste no esta en nuestra base de datos :("})
        
        #user = authenticate(email=email, password=password)
        #if user:
        if user.check_password(password):
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect(reverse('home'))
            else:
                return render(request, 'acceso/login.html',{'message':"Eres un usuario inactivo :("})
        else:
            print("> PyMessge: Faild Login, username: {}, password: {}".format(email,password))
            return render(request, 'acceso/login.html',{'message':"Credenciales de Acceso Invalidas :("})
    else:
        return render(request, 'acceso/login.html',{})

def logout_action(request):
    """
    Acción de Salida de la pagina.
    """
    logout(request)
    return render(request, 'acceso/login.html')