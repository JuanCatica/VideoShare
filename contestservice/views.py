from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from videoshare.settings import *
from .models import Video
from .forms import VideoForm
from .videotools import vtool
from core.models import Contest
from django.forms.models import model_to_dict
import os

def contest_home(request, url_contest, msn=None):
    """
    Este método permite visualizar los videos cargados en el concurso seleccionado.
    """
    contest = get_if_exists(Contest, url=url_contest)
    if contest:
        context = {'contest':contest, 'video_form':VideoForm()}
        if msn:
           context['meessage'] = msn
            
        if request.user.is_authenticated:
            context["username"] = request.user.username
            videos = Video.objects.all().filter(fk_contest=contest)
        else:
            videos = Video.objects.all().filter(fk_contest=contest, state=Video.CONVERTIDO)
            
        if videos:
            video_selected = None
            video_id = request.GET.get('video_id',None)
            if video_id != None:
                try:
                    video_id_int = int(video_id)
                    video_selected = get_if_exists(Video, id=video_id_int, fk_contest=contest)
                    if video_selected:
                        if video_selected.state == Video.CONVERTIDO:
                            context['video_selected'] = video_selected
                        else:
                            context['meessage'] = """El video que nos has solicidato se encuentra en proceso ..."""
                            context['video_selected'] = videos[0]
                    else:
                        context['meessage'] = """El video que nos has solicidato NO existe :("""
                        context['video_selected'] = videos[0]
                except:
                    context['meessage'] = """Hemos detectado una incosistencia en la forma en que nos has solicitado el video."""
            else:
                context['video_selected'] = videos[0]
            context['videos'] = videos
            return render(request, "contestservice/home_contest.html", context)
        else:
            return render(request, "contestservice/home_contest.html", context)
    else:
        return render(request, "contestservice/no_url.html", {'contest':contest,'meessage':"Error"})

def upload_video_action(request, url_contest):
    """
    Este método pertmire cargar el video que se recibe al gestionar el formulario de nuevos videos para un concurso.
    """
    context = {'video_form':VideoForm()}
    if request.method == 'POST':
        video_form = VideoForm(request.POST,request.FILES)
        
        contest = get_if_exists(Contest, url=url_contest)
        title = request.POST.get('title',None)
        vfile = request.FILES.get('videofile',None)
        
        exist = get_if_exists(Video, fk_contest=contest, title=title)
        if exist:
            msn = "El nombre del video que nos has proporcionado ya existe"
            return HttpResponseRedirect(reverse('contest_home_msn',args=(url_contest,msn)))

        if vfile and not str(vfile).lower().endswith(("avi","flv","wmv","mp4")):
            msn = "El archivo que nos has proporcionado no es un video"
            return HttpResponseRedirect(reverse('contest_home_msn',args=(url_contest,msn)))

        if video_form.is_valid():
            input_video = video_form.save(commit=False)
            input_video.fk_contest = contest
            input_video.save()
            
            # ---------------------------
            # GENERACION DE PATH CORRECTO
            path = os.path.join(BASE_DIR,*input_video.videofile.url.split(os.sep))
            image = vtool.get_image_from_video(path)

            # ---------------------------
            # DEFINICION DEL NOMBRE DEL ARCHIVO
            nombre = os.path.basename(input_video.videofile.url).split(".")[0]
            vtool.trim_reshape_save_image(image, MEDIA_IMG_VIDEO_ROOT, nombre)

            # ---------------------------
            # ESTABLECER IMAGEN EN LA INSTACIA DEL MODELO | UPDATE
            Video.objects.filter(id=input_video.id).update(image = os.path.join(MEDIA_IMG_VIDEO,"img_{}.jpg".format(nombre)))

            # PROCESO ADECUADO CUANDO SE IMOPLEMENTA UN ID PROPIO EN EL MODELO
            #contest_obj, created = Video.objects.update_or_create(
            #    id=input_video.id, 
            #    defaults= {'image':os.path.join(MEDIA_IMG_VIDEO,"img_{}.jpg".format(nombre))})
                
            msn = """Hemos recibido tu video y lo estamos procesando para que sea publicado. 
                Tan pronto el video quede publicado en la página del concurso te notificaremos por email. 
                Gracias por participar"""
            return HttpResponseRedirect(reverse('contest_home_msn',args=(url_contest,msn)))
        else:
            msn = "Error en el formulario"
            return HttpResponseRedirect(reverse('contest_home_msn',args=(url_contest,msn)))
    else:
        return HttpResponseRedirect(reverse('contest_home',args=(url_contest,)))

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

# -------------------------------
#      DEPRECIADOS

#def upload_video_view(request, url_contest):
#    """
#
#    """
#    contest = get_if_exists(Contest, url=url_contest)
#    if contest:
#        context = {'contest':contest, 'video_form':VideoForm()}
#        return render(request, "contestservice/newvideo.html", context)
#    else:
#        context = {'messge':"No hemos encontrado concusro con la URL {} :(".format(url_contest)}
#        return render(request, "contestservice/search_contest.html", context)