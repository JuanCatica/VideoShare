from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .forms import ContestForm
from .models import Contest
from contestservice.models import Video
from videoshare.settings import *
import json

from django.db.models import Count, Sum

@login_required
def home(request):
    """
    Este método permite generar la visualización de los concursos para un usuario logueado.
    Donde se controla la vidualización para exponer unicamente los concursos asociados a cada
    usuario y donde además se visualizan las métricas generales.   

    - QUERY SQL:
        SELECT fk_contest_id, state, count(*), fk_contest_id
        FROM contestservice_video video
        INNER JOIN core_contest contest ON video.fk_contest_id = contest.id
        WHERE fk_user_id = {request.user.id}
        GROUP BY fk_contest_id, state
    """
    contests = Contest.objects.all().filter(fk_user=request.user)
    dic_stats = {}
    dic_count = {}
    #try:
    # ----------------------
    # QUERY : GET STATISTICS

    # DJANGO BUG | solution https://code.djangoproject.com/ticket/19493
    # Description: annotate(Count()) generate multiple outputs, it doesn´t really group and count
    # Solution: use .order_by() | some thing relatedto the pk
    lista = Video.objects.order_by().values('fk_contest','state').annotate(count=Count('state')).filter(fk_contest_id__fk_user=request.user)

    # -----------------------------------------
    # GENERACION DE DICCIONARIO DE ESTADISTICAS
    for row in lista:
        contest_id, state, count = row['fk_contest'], row['state'], row['count']
        if contest_id in dic_stats:
            dic_stats[contest_id].append(dict(text=state,values=[count]))
            dic_count[contest_id] += count
        else:
            dic_stats[contest_id] = [dict(text=state,values=[count])]
            dic_count[contest_id] = count
    #except:
    #    pass
    
    # ------------------------------------------------------------
    # ASIGNACION DE MÉTRICAS ASOCIADAS A CADA UNO DE LOS CONCURSOS
    zip_contests_stats = []
    for contest in contests:
        if contest.id in dic_stats:
            zip_contests_stats.append((contest, dic_count[contest.id], json.dumps(dic_stats[contest.id])))
        else:
            zip_contests_stats.append((contest, 0, []))
    
    # -----------------------
    # DICCIONARIO DE CONTEXTO
    context = {
        'username':request.user.username,
        'contests_stats':zip_contests_stats,
        'contest_form':ContestForm(),
        "instance_id":INTANCE_ID
    }
    return render(request, "core/home.html", context)

@login_required
def create_new_contest_view(request):
    """
    Este método permite generar la vista para exponer el formlario donde se registran
    nuevos concusos. 
    """
    context = {
        'username':request.user.username,
        'contest_form':ContestForm(),
        "instance_id":INTANCE_ID
    }
    return render(request, "core/newcontest.html", context)

@login_required
def create_new_contest_action(request):
    """
    Este método permite registrar un nuevo curso en la base de datos, donde cada concurso 
    queda asociado al usuario que lo ha creado.
    """
    context = {
        'username':request.user.username,
        'contest_form':ContestForm(),
        "instance_id":INTANCE_ID
    }
    if request.method == 'POST':
        contest_form = ContestForm(request.POST,request.FILES)

        url = request.POST.get('url',None)
        start_date = request.POST.get('start_date',None)
        end_date = request.POST.get('end_date',None)        
        
        # -----------------------------------------
        # SE ALMACENA EL NUEVO CONCURSO (FORMULARIO)
        if contest_form.is_valid():
            # ---------------------
            # CONTROL LÓGICO EN URL
            error, msn = error_consistencia_url(url)
            if error:
                context["meessage"] = msn
                return render(request,'core/newcontest.html', context)
            error, msn = error_existencia_url(url)
            if error:
                context["meessage"] = msn
                return render(request,'core/newcontest.html', context)

            # -------------
            # SAVE CONSTEST
            input_contest = contest_form.save(commit=False)
            input_contest.fk_user = request.user
            input_contest.save()
            
            #context["contests"] = Contest.objects.all().filter(fk_user=request.user)
            #return render(request,'core/home.html', context)
            return HttpResponseRedirect(reverse('home'))
        else:
            print(contest_form.errors)
            context["meessage"] = "Formulario no valido"
            context['contest_form'] = contest_form
            return render(request,'core/newcontest.html', context)
    else:
        return render(request,'core/newcontest.html', context)

@login_required
def update_contest_view(request):
    """
    Este método permite la visualización del formulrio para la actualización de un concurso.
    Para la identificación del concurso deseado (localización en base de datos) desde 'home.html'
    de la aplicación se pasa el identificador (id).
    Este método pasa los valores antifuos del concurso mediante el diccionario de contexto,
    de esta forma cuando se visualiza el formulario ya se tienen los valores antiguos.
    """
    if request.method == 'POST':
        # --------------------------------------------------------------
        # OBTENCIÓN DEL CONCURSO A PARTIR DEL ID ENVIADO POR HTTP (POST)
        try:
            id_contest = int(request.POST.get('id_contest', '-1'))
        except:
            return HttpResponseRedirect(reverse('update_contest'))

        id_contest = int(request.POST.get('id_contest', '-1'))
        old_contest = get_object_or_404(Contest, id=id_contest)

        # ----------------------------------------------------------------
        # CONVERCIÓN DE LA INSTANCIA DEL MODELO DEL CONCURSO A DICCIONARIO
        # Y FORMATEO A TEXTO LAS FECHAS
        dic_contest = model_to_dict(old_contest)
        dic_contest['start_date'] = str(dic_contest['start_date'])
        dic_contest['end_date'] = str(dic_contest['end_date'])
        old_contest_form = ContestForm(initial = dic_contest)

        context = {
            'username':request.user.username,
            'contest_form':old_contest_form,
            'old_contest_id':id_contest,
            "instance_id":INTANCE_ID
        }
        return render(request, "core/updatecontest.html", context)
    return HttpResponseRedirect(reverse('home'))

@login_required
def update_contest_action(request):
    """
    Método empleado para la acción de actualización de un concurso.
    Este mmétodo recibe el identifcador del concurso y todos los parametros (campos) con o sin modificación
    De esta forma se reescribe cada uno de los campos asociados al concurso y se desarrolla la actualización.
    """
    context = {
        'username':request.user.username,
        "instance_id":INTANCE_ID
    }
    if request.method == 'POST':
        # --------------------------------------------------------------
        # OBTENCIÓN DEL CONCURSO A PARTIR DEL ID ENVIADO POR HTTP (POST)
        try:
            id_contest = int(request.POST.get('id_contest', '-1'))
        except:
            return HttpResponseRedirect(reverse('update_contest'))
        url = request.POST.get('url',None)

        contest_form = ContestForm(request.POST,request.FILES)
        if contest_form.is_valid():
            # ---------------------
            # CONTROL LÓGICO DE URL
            error, msn = error_consistencia_url(url)
            if error:
                context["meessage"] = msn
                return render(request,'core/updatecontest.html', context)
            
            # -----------------------------------------------------------------
            # ACTUALIZACIÓN DEL DICCIONARIO QEU DEFINE EL CONCURSO A ACTUALIZAR
            dic_contest = model_to_dict(contest_form.save(commit=False))
            dic_contest.pop('fk_user', None)
            dic_contest.pop('image', None)
            dic_contest['id'] = id_contest

            # UPDATE POR MEDIO DE DICCIONARIO | MULTIPLES ATRIBUTOS
            Contest.objects.filter(id=id_contest).update(**dic_contest)

            # PROCESO ADECUADO CUANDO SE IMOPLEMENTA UN ID PROPIO EN EL MODELO
            #contest_obj, created = Contest.objects.update_or_create(
            #    id=id_contest, 
            #    defaults=dic_contest)

            context["contests"] = Contest.objects.all().filter(fk_user=request.user)
            return HttpResponseRedirect(reverse('home'))
    return HttpResponseRedirect(reverse('home'))

@login_required
def delete_contest(request):
    """
    Método para eliminar un concurso.
    """
    if request.method == 'POST':
        id_contest = int(request.POST.get('id_contest', '-1'))
        query = Contest.objects.get(id=id_contest)
        query.delete()
    context = {
        'username':request.user.username,
        'contests':Contest.objects.all().filter(fk_user=request.user),
        'contest_form':ContestForm(),
    }
    return HttpResponseRedirect(reverse('home'))

@login_required
def test_post(request):
    """
    Este método se emplea apra el desarrollo de pruebas
    """
    print("-ID",request.POST.get('id_test', 'nada :('))
    return HttpResponseRedirect(reverse('home'))

# ------------------------------
#       METODOS AUXILIARES

def get_if_exists(model, **kwargs):
    """
    Entre un objeto(mdelo) en caso de que este existo, si no se retorna el valor de None.
    """
    try:
        obj = model.objects.get(**kwargs)
    except model.DoesNotExist:  # Be explicit about exceptions
        obj = None
    return obj

# ---------------------------
# CONTROL LÓGICO SOBRE LA URL
def error_consistencia_url(url):
    if " " in url:
        return True, "La url no debe contener espacios"
    return False, ""

def error_existencia_url(url):
    exist = get_if_exists(Contest, url=url)
    if exist:
        return True, "La url que especificaste ya existe, ingresa otra."
    return False, ""

# ---------------------------
# CONTROL LÓGICO SOBRE FECHAS
# PENDIENTE | SIN IMPLEMENTAR
def error_consistencia_fechas(fechaA,fechaB):
    return None

def error_orden_fechas(fechaA,fechaB):
    return None