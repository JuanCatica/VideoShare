from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from videoshare.settings import *
from .models import Video
from .forms import VideoForm
from core.models import Contest
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
import os
import boto3
from datetime import datetime

def contest_home(request, url_contest, msn=None):
    """
    Este método permite visualizar los videos cargados en el concurso seleccionado.
    """
    contest = get_if_exists(Contest, url=url_contest)
    context = {'contest':contest, 'video_form':VideoForm(), "instance_id":INTANCE_ID}
    if contest:
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
            
            page = request.GET.get('page', 1)
            paginator = Paginator(videos, 10)
            try:
                videos_page = paginator.page(page)
            except PageNotAnInteger:
                videos_page = paginator.page(1)
            except EmptyPage:
                videos_page = paginator.page(paginator.num_pages)

            context['videos'] = videos_page
            context['page'] = page
        return render(request, "contestservice/home_contest.html", context)
    else:
        return render(request, "contestservice/no_url.html", context)

def upload_video_action(request, url_contest):
    """
    Este método pertmire cargar el video que se recibe al gestionar el formulario de nuevos videos para un concurso.
    """
    context = {'video_form':VideoForm(), "instance_id":INTANCE_ID}
    if request.method == 'POST':
        video_form = VideoForm(request.POST,request.FILES)
        
        contest = get_if_exists(Contest, url=url_contest)
        title = request.POST.get('title',None)
        vfile = request.FILES.get('videofile',None)
        _, extension = os.path.splitext(vfile.name)
        print(extension)
        exist = get_if_exists(Video, fk_contest=contest, title=title)
        if exist:
            msn = "El nombre del video que nos has proporcionado ya existe"
            return HttpResponseRedirect(reverse('contest_home_msn',args=(url_contest,msn)))

        if not extension.lower().endswith(("avi","flv","wmv","mp4")):
            msn = "El archivo que nos has proporcionado no es un video"
            return HttpResponseRedirect(reverse('contest_home_msn',args=(url_contest,msn)))

        if video_form.is_valid():
            input_video = video_form.save(commit=False)
            # ------------------------------
            # ALMACENAMIENTO DEL VIDEO EN S3
            key, video_name, video_extension, s3_cloudfront_video_url = save_video_s3(vfile, contest)
            input_video.fk_contest = contest
            input_video.videofile_s3_url = s3_cloudfront_video_url
            input_video.save()

            # ----------------------------------------------------------------------------
            # ENVIO DE MENSAJE A SQS PARA PROCESAMIENTO DEL VIDEO POR PARTE DE LOS WORKERS

            hora_carga =  str(datetime.now().timestamp())
            send_msn_SQS(key, video_name, video_extension, s3_cloudfront_video_url, input_video.id, input_video.title, input_video.first_name_competitor, input_video.email_competitor, contest.url, hora_carga)

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
    Entre un objeto(modelo) en caso de que este exista, si no se retorna el valor de None.
    """
    try:
        obj = model.objects.get(**kwargs)
    except model.DoesNotExist:  # Be explicit about exceptions
        obj = None
    return obj

def save_video_s3(video_file, contest):
    """
    Permite almacenar el video en S3 bajo una nomenclatura definida
    """
    video_name_ext = "{}-{}-{}".format(str(datetime.now().timestamp()).replace(".","-"), contest, video_file.name)
    video_name, video_extension = os.path.splitext(video_name_ext)
    key = 'videos/{}'.format(video_name)
    client = boto3.client('s3')
    
    stream = video_file.read()
    client.put_object(Body=stream, Bucket=CONFIGS["s3_url"] , Key=key, ACL = 'public-read') #BUCKET_NAME
    #f = io.BytesIO(stream)

    return key, video_name, video_extension, "https://{}.cloudfront.net/{}".format(CONFIGS["cf_url"], key) #CLOUDFRONT

def send_msn_SQS(key, video_name, video_extension, video_url_s3, video_id, video_title, user_name, user_email, video_web_url, hora_carga):
    """
    Permite enviar datos asociados a un video a una cola gestionada por AWS.
    """
    sqs = boto3.client('sqs',region_name=REGION_NAME) #SQS_REGION
    response = sqs.send_message(
        QueueUrl=CONFIGS["sqs_url"], #SQS_URL
        DelaySeconds=0,
        MessageAttributes={
            'key':{
                'DataType': 'String',
                'StringValue': key
            },
            'video_name':{
                'DataType': 'String',
                'StringValue': video_name
            },
            'video_extension':{
                'DataType': 'String',
                'StringValue': video_extension
            },
            'video_url_s3':{
                'DataType': 'String',
                'StringValue': video_url_s3
            },
            'video_id':{
                'DataType': 'String',
                'StringValue': '{}'.format(video_id)
            },
            'video_title':{
                'DataType': 'String',
                'StringValue': '{}'.format(video_title)
            },
            'user_name':{
                'DataType': 'String',
                'StringValue': '{}'.format(user_name)
            },
            'user_email':{
                'DataType': 'String',
                'StringValue': '{}'.format(user_email)
            },
            'video_web_url':{
                'DataType': 'String',
                'StringValue': '{}'.format(video_web_url)
            },
            'hora_carga':{
                'DataType': 'String',
                'StringValue': '{}'.format(hora_carga)
            }
        },
        MessageBody=video_name
    )