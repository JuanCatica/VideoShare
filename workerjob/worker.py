# ---------------------------------
# SCRIPT WORKER
#   Se emplea para el desarrllo de las diferentes tareas asociadas a la transformación de videos.

import os
import shutil
import cv2
import json
import boto3
import time
import socket
import pymysql.cursors
import configparser 
import requests
from secrets import get_secret
from os import remove
from datetime import datetime
from botocore.exceptions import ClientError
from apscheduler.schedulers.blocking import BlockingScheduler

# ------
# STATES
EN_PROCESO = "En Proceso"
CONVERTIDO  = "Convertido"
ASIGNADO  = "Asignado"
# ----------------------------------------
# DIRECCIONES ASOCIADAS LOS ARCHIVOS MEDIA

# DIRECCION BASE DE ARCIVOS MEDIA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# DIRECCION DE LAS IMAGENES GENERADAS A PARTIR DE LOS VIDEOS
MEDIA_IMG_VIDEO = "/videos_image/"
MEDIA_IMG_VIDEO_ROOT = os.path.join(MEDIA_ROOT, "videos_image")

# DIRECCION DE VIDEOS CARGADOS
MEDIA_VIDEO = "/videos/"
MEDIA_VIDEO_ROOT = os.path.join(MEDIA_ROOT, "videos")

# DIRECCION DE VIDEOS TRANSFORMADOS
MEDIA_VIDEO_FFMPEG = "/videos_ffmpeg/"
MEDIA_VIDEO_FFMPEG_ROOT = os.path.join(MEDIA_ROOT, "videos_ffmpeg")

# -------------------------------------------------
# LOGS PARA EL ALMACENAMIENTO DE ERRORES Y PTOCESOS
LOG_ERR = os.path.join(BASE_DIR, "logs/errs.log")

# --------------------
# CONSTANTES DE ESTADO
STATUS_OK = "OK"
STATUS_FAIL = "FAIL"
STATUS_NO_MSN = "NO_MSN"

# -------------------------------------------------
# METODO X
#  - SX : ESTATUS DEL METODO X
#  - TX : TIEMPO EMPLEADO PARA EJECUTAR EL METODO X
#  - MSN : MENSAJE DE ERROR
#  - ERR_POS : POSICION DEL ERROR

# --------
# METODO 0
def read_params():
    """
    Lectura de archivo de configuración.
    """
    DATA = {}
    STAT = {}
    CONFIGS = {}
    STAT["INIT"] = datetime.now().timestamp()
    init = time.time()

    # -----------------------------------
    # LECTURA DE ARCHIVO DE CONFIGURACIÓN
    config = configparser.ConfigParser()
    config.read(os.path.join(BASE_DIR, "config.conf"))
    SECRET_NAME = config.get("SECRETS","name")
    REGION_NAME = config.get("SECRETS","region")
    FFMPEG = config.get("FFMPEG","ffmpeg")
    FFMPEG_ARGS = config.get("FFMPEG","ffmpeg_args", fallback='')
    CONFIGS = get_secret(SECRET_NAME, REGION_NAME)

    if CONFIGS is not None:
        STAT["S0"] = STATUS_OK
        CONFIGS["_region"] = REGION_NAME
        CONFIGS["_ffmpeg"] = FFMPEG
        CONFIGS["_ffmpeg_args"] = FFMPEG_ARGS
    else:
        STAT["S0"] = STATUS_FAIL
        STAT["ERR"] = "M0. SECRETS NOT FOUND"
    STAT["JOB"] = STAT["S0"]
    STAT["T0"] = time.time() - init
    return DATA, STAT, CONFIGS

# --------
# METODO 1
def get_mesage_SQS(DATA, STAT, CONFIGS):
    """
    Este metodo entrega uno de los registros de videos en estado activo (En proceso).
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
    
    try:
        sqs = boto3.client('sqs',region_name=CONFIGS["_region"])
        response = sqs.receive_message(
            QueueUrl=CONFIGS["sqs_url"],
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=30,
            WaitTimeSeconds=0
        )

        if 'Messages' in response.keys():
            message = response['Messages'][0]
            attrs = message['MessageAttributes']

            DATA["KEY"] = attrs['key']['StringValue']
            DATA["VIDEO_NAME"] = attrs['video_name']['StringValue']
            DATA["VIDEO_EXTENSION"] = attrs['video_extension']['StringValue']
            DATA["VIDEO_URL_S3"] = attrs['video_url_s3']['StringValue']
            DATA["VIDEO_ID"] = int(attrs['video_id']['StringValue'])
            DATA["VIDEO_TITLE"] = attrs['video_title']['StringValue']
            DATA["RECEIPT_HANDLE"] = message['ReceiptHandle']
            DATA["USER_NAME"] = attrs['user_name']['StringValue']
            DATA["USER_EMAIL"] = attrs['user_email']['StringValue']
            DATA["VIDEO_WEB_URL"] = attrs['video_web_url']['StringValue']
            DATA["VIDEO_NAME_EXT"] = "{}{}".format(DATA["VIDEO_NAME"],DATA["VIDEO_EXTENSION"])
            DATA["LOAD_DATETIME"] = float(attrs['hora_carga']['StringValue'])
            
            STAT["S1"] = STATUS_OK
        else:
            STAT["S1"] = STATUS_NO_MSN
    except Exception as e:
        STAT["S1"] = STATUS_FAIL
        STAT["MSN"] = "SQS READ ERROR"
        STAT["EXCEPTION"] = {
            "STEP":"S1",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S1"]
    STAT["T1"] = time.time() - init

# --------
# METODO 2
def download_video_from_S3(DATA, STAT, CONFIGS):
    """
    Método para descargar el video original desde el S3.
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return

    try:
        pass
        s3 = boto3.resource('s3')
        #temp_path = './media/videos/{}'.format(DATA["VIDEO_NAME_EXT"])
        temp_path = '{}/{}'.format(MEDIA_VIDEO_ROOT, DATA["VIDEO_NAME_EXT"])
        s3.Bucket(CONFIGS["s3_url"]).download_file(DATA["KEY"], temp_path)
        STAT["S2"] = STATUS_OK
    except Exception as e:
        STAT["S2"] = STATUS_FAIL
        STAT["MSN"] = "M2. S3 DOWNLOAD ERROR"
        STAT["EXCEPTION"] = {
            "STEP":"S2",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S2"]
    STAT["T2"] = time.time() - init

# --------
# METODO 3
def convert_video(DATA, STAT, CONFIGS):
    """
    Convertir video
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
        
    # -------> EJEMPLO
    # ffmpeg -i "https://d3rjwawu0g5wjw.cloudfront.net/videos/1586058232-937135-concursinit-test2.AVI" /Users/juancatica/Desktop/videos-test-out/salida-test.mp4
    # /Users/juancatica/Cloud/recursos/ffmpeg -i "https://d3rjwawu0g5wjw.cloudfront.net/videos/1586058232-937135-concursinit-test2.AVI" 
    # "https://d3rjwawu0g5wjw.cloudfront.net/videos_ffmpeg/1586058232-937135-concursinit-test2.AVI"
    try:
        video_path_in = "{}/{}".format(MEDIA_VIDEO_ROOT, DATA["VIDEO_NAME_EXT"])
        video_path_out = "{}/{}.mp4".format(MEDIA_VIDEO_FFMPEG_ROOT,DATA["VIDEO_NAME"])
        comando = "{} -i '{}' {} '{}' -y".format(CONFIGS["_ffmpeg"], video_path_in, CONFIGS["_ffmpeg_args"], video_path_out)
        print("COMANDO ...",comando)
        exit_code = os.system(comando)
        if exit_code == 0:
            STAT["S3"] = STATUS_OK
        else:
            STAT["S3"] = STATUS_FAIL
            STAT["MSN"] = "M3. FFMPEG EXIT CODE ERROR"
    except Exception as e:
        STAT["S3"] = STATUS_FAIL
        STAT["MSN"] = "M3. FFMPEG ERROR"
        STAT["EXCEPTION"] = {
            "STEP":"S3",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S3"]
    STAT["T3"] = time.time() - init

# --------
# METODO 4
def save_image_from_video(DATA, STAT, rate=1.5, width=220):
    """

    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
        
    try:
        video_file = "{}/{}.mp4".format(MEDIA_VIDEO_FFMPEG_ROOT, DATA["VIDEO_NAME"])
        vidcap = cv2.VideoCapture(video_file)
        success,image = vidcap.read()
        if success:
            output_shape=(width,int(width/rate))
            y, x, z = image.shape
            dx = dy = 0
            if float(x/y) >= rate:
                dx = int((x-(y*rate))/2.0)
            else:
                dy = int((y-(x/rate))/2.0)
            sliced_image = image[dy:y-dy, dx:x-dx, :]
            rechaped = cv2.resize(sliced_image, output_shape, interpolation = cv2.INTER_AREA)
            cv2.imwrite("{}/{}.jpg".format(MEDIA_IMG_VIDEO_ROOT, DATA["VIDEO_NAME"]), rechaped)
            STAT["S4"] = STATUS_OK
        else:
            STAT["S4"] = STATUS_FAIL
    except Exception as e:
        STAT["S4"] = STATUS_FAIL
        STAT["MSN"] = "M4. SAVE IMAGE ERROR" 
        STAT["EXCEPTION"] = {
            "STEP":"S4",
            "TEXT":str(e)
        }
    #STAT["JOB"] = STAT["S4"]
    STAT["T4"] = time.time() - init

# --------
# METODO 5
def upload_video_img_S3(DATA, STAT, CONFIGS):
    """
    Método para cargar el video transformado a S3.
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
        
    try:
        s3 = boto3.resource('s3')
        video_ffmpeg_file = "{}/{}.mp4".format(MEDIA_VIDEO_FFMPEG_ROOT, DATA["VIDEO_NAME"])
        video_ffmpeg_key = 'videos_ffmpeg/{}.mp4'.format(DATA["VIDEO_NAME"])
        s3.Object(CONFIGS["s3_url"], video_ffmpeg_key).put(Body=open(video_ffmpeg_file, 'rb'), ACL = 'public-read')

        video_img_file = "{}/{}.jpg".format(MEDIA_IMG_VIDEO_ROOT, DATA["VIDEO_NAME"])
        video_img_key = 'videos_image/{}.jpg'.format(DATA["VIDEO_NAME"])
        s3.Object(CONFIGS["s3_url"], video_img_key).put(Body=open(video_img_file, 'rb'), ACL = 'public-read')
        STAT["S5"] = STATUS_OK
    except Exception as e:
        STAT["S5"] = STATUS_FAIL
        STAT["MSN"] = "M5. S3 UPLOAD ERROR"   
        STAT["EXCEPTION"] = {
            "STEP":"S5",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S5"]
    STAT["T5"] = time.time() - init

# --------
# METODO 6
def update_db_state(DATA, STAT, CONFIGS):
    """
    Metodo para actualizar los registros procesados.
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
        
    try:
        conn = pymysql.connect(
            host=CONFIGS["rds_url"],
            port=int(CONFIGS["rds_port"]),
            user=CONFIGS["rds_user"],
            password=CONFIGS["rds_pass"],
            db=CONFIGS["rds_db"], 
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor)

        #client = MongoClient(host=CONFIGS["rds_url"], port=CONFIGS["rds_port"])
        #db = client[CONFIGS["rds_db"]]
        #collection = db["contestservice_video"]

        videofile_s3_url = "https://{}.cloudfront.net/videos/{}".format(CONFIGS["cf_url"], DATA["VIDEO_NAME_EXT"])
        videofile_format_s3_url = "https://{}.cloudfront.net/videos_ffmpeg/{}.mp4".format(CONFIGS["cf_url"], DATA["VIDEO_NAME"])
        image_s3_url = "https://{}.cloudfront.net/videos_image/{}.jpg".format(CONFIGS["cf_url"], DATA["VIDEO_NAME"])

        UPDATE_DIC = {
            "videofile_s3_url":videofile_s3_url,
            "videofile_format_s3_url":videofile_format_s3_url,
            "image_s3_url":image_s3_url,
            "state":CONVERTIDO
        }

        with conn.cursor() as cursor:
            # -----------------------------
            # UDATE THE STATE OF THE VIEDEO
            update_str = " ".join([f""" {k} = "{v}", """ for k,v in UPDATE_DIC.items()]).strip(" ").strip(",")
            sql_update = """UPDATE contestservice_video SET {} WHERE id={};""".format(update_str,DATA["VIDEO_ID"])
            cursor.execute(sql_update)
            conn.commit()
        #collection.update_one({"id":DATA["VIDEO_ID"]},{"$set":UPDATE_DIC}, upsert=False) ######### IMPORTANTE: CAMBIAR A MYSQL
        STAT["S6"] = STATUS_OK
    except Exception as e:
        STAT["S6"] = STATUS_FAIL
        STAT["MSN"] = "M6. UPDATE MONGO ERROR"  
        STAT["EXCEPTION"] = {
            "STEP":"S6",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S6"]
    STAT["T6"] = time.time() - init

# --------
# METODO 7
def delete_SQS_message(DATA, STAT, CONFIGS):
    """
    Método eliminar el mensaje recibido.
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
        
    try:
        sqs = boto3.client('sqs',region_name=CONFIGS["_region"])
        sqs.delete_message(QueueUrl=CONFIGS["sqs_url"],ReceiptHandle=DATA["RECEIPT_HANDLE"])
        STAT["S7"] = STATUS_OK
    except ClientError as e:
        STAT["S7"] = STATUS_FAIL
        STAT["MSN"] = "M7. DELETE SQS ERROR" 
        STAT["EXCEPTION"] = {
            "STEP":"S7",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S7"]
    STAT["T7"] = time.time() - init

# --------
# METODO 8
def delete_temp_files(STAT):
    """
    Método para eleminar los archivos temporales.
    """
    init = time.time()

    delete_a = delete_folder_content("./media/videos/")
    delete_b = delete_folder_content("./media/videos_ffmpeg/")
    delete_c = delete_folder_content("./media/videos_image/")

    if STAT["JOB"] == STATUS_OK:
        if not (delete_a and delete_b and delete_c):
            STAT["S8"] = STATUS_FAIL
        else:
            STAT["S8"] = STATUS_OK
        STAT["T8"] = time.time() - init

def delete_folder_content(folder):
    complete_delete = True
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if not filename.endswith(".gitignore"):
                try:
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    complete_delete = False
    else:
        complete_delete = False
    return complete_delete

# --------
# METODO 9
def send_mail_SES(DATA, STAT, CONFIGS):
    """
    Método para enviar correo.
    """
    init = time.time()
    if STAT["JOB"] != STATUS_OK:
        return
        
    WEB_URI = CONFIGS["web_url"]
    WEB_PORT = CONFIGS["web_port"]
    URL_WEB_CONCURSOS = "{}:{}/concurso/".format(WEB_URI,WEB_PORT)
    AWS_REGION = CONFIGS["_region"]
    
    SUBJECT = "Video disponible :D"
    BODY_TEXT = ("Video disponible :D\r\n"
                 "Este mensaje es para infromar que uno de los videos cargados en el sevicio SmartTools ha sido procesado")
    BODY_HTML = """
    <head></head>
    <body>
        <h1>Video convertido!</h1>
        <p>Hola {},</p>
        <p></p>    
        <p>Te informamos que tu video {} ha sido transformado satsfactoriamente.</p>
        <p>Puedes verlo en la siguiente URL: <a href='http:{}{}/?video_id={}'>{}</a></p>
        <p></p>
        <p>Dsitruta de ver los videos de los demas concursantes
        y visitanos para conocer mas sobre nuestro SaaS.</p>
        <p></p>
        <p>Saludos,</p>
        <p>Grupo 7</p>
    </body>""".format(DATA["USER_NAME"], DATA["VIDEO_TITLE"], URL_WEB_CONCURSOS,
     DATA["VIDEO_WEB_URL"], DATA["VIDEO_ID"], DATA["VIDEO_TITLE"])

    CHARSET = "UTF-8"
    client = boto3.client('ses',region_name=AWS_REGION)

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [DATA["USER_EMAIL"],],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=CONFIGS["ses_email"],
        )
        STAT["S9"] = STATUS_OK
    except ClientError as e:
        STAT["S9"] = STATUS_FAIL
        STAT["MSN"] = "M9. SES ERROR" 
        STAT["EXCEPTION"] = {
            "STEP":"S9",
            "TEXT":str(e)
        }
    STAT["JOB"] = STAT["S9"]
    STAT["T9"] = time.time() - init

# ----------------------------
# LOGS DE ERRORES
def log_err(type_err, msn, stat):
    """
    Metodo para almacenamiento de errores.
    """
    date = datetime.now().strftime("%Y/%m/%m %H:%M:%S.%Z")
    full_msn = "> ERROR {} - {} \n\t MSN: {} \n\t STAT: {} \n\n".format(type_err, date, msn, stat)
    try:
        f = open(LOG_ERR, "a")
        f.write(full_msn)
        f.close()
    except Exception as e:
        print("Error Fatal, No se pueden visualizar los mensajes en los Logs. ERROR:", e)


def run():
    #try:
    # ----------------------------
    # 0. LECTURA DE ARCIVO PARAMS
    data, stat, configs = read_params()
    
    # ----------------------------
    # 1. OBTENER EL MENSAJE DE SQS
    get_mesage_SQS(data,stat,configs)
    
    # ----------------------------
    # 2. DESCARGA DEL VIIDEO DE S3
    download_video_from_S3(data,stat,configs)
    
    # ----------------------------
    # 3. CANVIRTIENDO VIDEO
    convert_video(data,stat,configs)
    
    # ----------------------------
    # 4. EXTRAER Y GUARDAR IMAGEN
    save_image_from_video(data,stat)
    
    # ----------------------------
    # 5. CARGAR VIDEO S3
    upload_video_img_S3(data,stat,configs)
    
    # ----------------------------
    # 6. ACTUALIZAR MONGO
    update_db_state(data,stat,configs)
    
    # ----------------------------
    # 7. BORRAR EL MENSAJE DE SQS
    delete_SQS_message(data,stat,configs)
    
    # ----------------------------
    # 8. BORRAR ARCHIVOS TEMP
    delete_temp_files(stat)
    
    # ----------------------------
    # 9. ENVIO DE EMAIL
    send_mail_SES(data,stat,configs)

    # ----------------------------
    # INSTANCE ID
    try:
        r = requests.get("http://169.254.169.254/latest/meta-data/local-ipv4",timeout=1)
        INTANCE_ID = r.text
    except Exception as e:
        INTANCE_ID = "Sin Id :("
    
    stat["END"] = datetime.now().timestamp()
    read_time = stat["INIT"] - data["LOAD_DATETIME"] if "LOAD_DATETIME" in data else None
    process_time = stat["END"] - stat["INIT"]
    stat["DELTA_A"] = read_time
    stat["DELTA_B"] = process_time
    stat["DELTA_C"] = read_time + process_time if read_time else process_time
    stat["INTANCE_ID"] = INTANCE_ID
    stat["data"] = data
    
    # -----------------------
    # Envio de datos a splunk
    if stat["JOB"] != STATUS_NO_MSN:
        try:
            url = f'{configs["splunk_api_protocol"]}://{configs["splunk_api_url"]}:{configs["splunk_api_port"]}/services/collector/event'
            header = { "Authorization": f'Splunk {configs["splunk_api_token"]}' }
            data = { "index":configs["splunk_index"], "source": configs["splunk_source"], "sourcetype": configs["splunk_sourcetype"], "event": data }
            data = str(data).replace("'",'"')
            r = requests.post(url, headers=header, data=data, verify=False, timeout=5)
        except Exception as e:
            log_err("SPLUNK:",e,stat)

if __name__ == '__main__':
    run()
    #sched = BlockingScheduler()
    #@sched.scheduled_job('interval', seconds=20)
    #def timed_job():
    #    print("Ejecutando ...")
    #    run()
    #sched.start()