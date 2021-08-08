import os
import pymysql.cursors
import smtplib 
from datetime import datetime
import time 
import configparser 
import requests

# ------
# STATES
EN_PROCESO = "En Proceso"
CONVERTIDO  = "Convertido"

# ----------------------------------------
# DIRECCIONES ASOCIADAS LOS ARCHIVOS MEDIA

# DIRECCION BASE DE ARCIVOS MEDIA
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
LOG_ERR = os.path.join(BASE_DIR, "workerjob/logs/errs.log")
LOG_TRANS = os.path.join(BASE_DIR, "workerjob/logs/trans.log")


# -----------------------------------
# LECTURA DE ARCHIVO DE CONFIGURACIÓN
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, "config.conf"))
HOST = config.get("DATABASE","host")
PORT = config.getint("DATABASE","port")
USER = config.get("DATABASE","user")
PASS = config.get("DATABASE","pass")
DB = config.get("DATABASE","db")
CHARSET = config.get("DATABASE","charset")
EMAIL = config.get("MAIL","email")
EPASS = config.get("MAIL","epass")
FFMPEG = config.get("FFMPEG","ffmpeg")
FFMPEG_ARGS = config.get("FFMPEG","ffmpeg_args", fallback='')
SERVICE_PORT = config.get("SERVICE","port")

# URL DEL SERVICIO
URL_WEB = None
URL_WEB_CONCURSOS = None
try:
    r = requests.get("http://169.254.169.254/latest/meta-data/public-hostname",timeout=0.5)
    URL_WEB = "{}:{}".format(r.text,SERVICE_PORT)
    URL_WEB_CONCURSOS = "{}/concurso/".format(URL_WEB)
except Exception as e:
    pass

def create_connection():
    """ 
    Metodo para la generacion de conexion con la Base de Datos MySQL.
    """
    conn = None    
    try:
        conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASS, db=DB, 
                                    charset=CHARSET, cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        log_trans("CONEXION ERROR")
        log_err("CONN:",e)  

    return conn


def get_one_active_process(conn):
    """
    Este metodo entrega uno de los registros de videos en estado activo (En proceso).
    """
    active_video = {}
    try:
        with conn.cursor() as cursor:
            # ------------------------------
            # CATCH A VIEDEO
            sql = """SELECT video.id, videofile, email_competitor, first_name_competitor, title, url
                    FROM contestservice_video video
                    INNER JOIN   core_contest contest ON video.fk_contest_id = contest.id
                    WHERE state='{}'
                    LIMIT 1""".format(EN_PROCESO)
            cursor.execute(sql)
            active_video = cursor.fetchone()

            if active_video:
                # -----------------------------
                # UDATE THE STATE OF THE VIEDEO
                id_video = active_video["id"]
                sql_update = """UPDATE contestservice_video SET state='{}' WHERE id={};""".format(ASIGNADO,id_video)
                cursor.execute(sql_update)
                conn.commit()
    except Exception as e:
        log_trans("ERROR: get_one_active_process")
        log_err("GETP:",e)
    return active_video

def update_state_after_failure(conn, id_video):
    """
    Este metodo entrega uno de los registros de videos en estado activo (En proceso).
    """
    try:
        with conn.cursor() as cursor:
            # -----------------------------
            # UDATE THE STATE OF THE VIEDEO
            sql_update = """UPDATE contestservice_video SET state='{}' WHERE id={};""".format(EN_PROCESO,id_video)
            cursor.execute(sql_update)
            conn.commit()
    except Exception as e:
        log_trans("ERROR: update_state_after_failure")
        log_err("GETP:",e)

@DeprecationWarning
def get_all_active_process(conn):
    """
    Este metodo entrega todos los registros de videos en estado activo (En proceso).
    - NOTA:
        Si en algun punto existe una cantidad muy elevada de videos a procesar
        Es mejor retornar el cursor y obtener registro a registro.
    """
    active_videos = []
    try:
        with conn.cursor() as cursor:
            sql = """SELECT video.id, videofile, email_competitor, first_name_competitor, title, url
                    FROM contestservice_video video
                    INNER JOIN core_contest contest ON video.fk_contest_id = contest.id
                    WHERE state='{}'""".format(EN_PROCESO)
            cursor.execute(sql)
            active_videos = cursor.fetchall()
    except Exception as e:
        log_trans("QUERY ERROR")
        log_err("GETP:",e)
    return active_videos


def update_state(conn, id, url):
    """
    Metodo para actualizar los registros procesados.
    """
    try:
        with conn.cursor() as cursor:
            id_int=str(id)
            sql_update_query = """UPDATE contestservice_video SET state='{}', videofile_format = '{}' WHERE id={};""".format(CONVERTIDO,url,id)
            cursor.execute(sql_update_query)
            conn.commit()
            log_trans("UPDATE OK",2)
            return True
    except Exception as e:
        log_trans("UPDATE ERROR",2)
        log_err("UPDT:",e)
    return False
    
def send_mail(TO,name,name_video, url_video, id_video):
    """
    Metodo para envio de mensajes.
    """
    print(TO)
    try:
        # SE CREA LA SESION 'SMTP' Y SE INICIA 'TLS' POR SEGURIDAD. 
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls() 
        
        # AUTENTICACION | ORIGEN-DESTINO
        s.login(EMAIL, EPASS) 
        FROM = EMAIL

        # PARAMETROS DEL MENSAJE
        SUBJECT = "Video disponible :D"
        hi = """
Hola {},
        
Te informamos que tu video {} ha sido transformado satisfactoriamente.
""".format(name, name_video)

        if URL_WEB_CONCURSOS is not None:
            info =  """
Puedes verlo en la siguiente URL: 
    {}{}/?video_id={}
""".format(URL_WEB_CONCURSOS, url_video, id_video)
        else:
            info =  """
Puedes ingresar a VideoShare para ver tu video.
            """
        
        chao = """
No olvides dsitrutar de ver los videos de los demás concursantes
y visitanos para conocer mas sobre nuestro SaaS.

Saludos,


Proyecto VideoShare
Visita: https://github.com/JuanCatica/VideoShare"""

        TEXT = hi + info + chao
        message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
        message = message.encode("utf-8")

        # SE ENVIA EL E-MAIL Y SE TERMINA LA SESSION
        s.sendmail(FROM, TO, message) 
        s.quit()

        log_trans("E-MAIL OK",2)
        return True
    except Exception as e:
        log_trans("E-MAIL ERROR",2)
        log_err("MAIL:",e)
    return False

def convert_video(url_video):
    try:
        input_video= os.path.join(MEDIA_ROOT,url_video)
        file_name = os.path.splitext(os.path.basename(url_video))[0]
        extension = "mp4"
        out_file = "{}.{}".format(file_name,extension)
        output_video = os.path.join(MEDIA_VIDEO_FFMPEG_ROOT,out_file)
        url_out = os.path.join(MEDIA_VIDEO_FFMPEG,out_file)

        comando = "{} -i {} {} {} -y".format(FFMPEG,input_video,FFMPEG_ARGS,output_video)
        log_trans("FFMPEG OK",2)
        return os.system(comando), url_out
    except Exception as e:
        log_trans("FFMPEG ERROR",2)
        log_err("CONV:",e)
    return 255, ""
 
def log_err(type_err, msn):
    """
    Metodo para almacenamiento de errores en las tareas de tranformacion.
    """
    date = datetime.now().strftime("%Y/%m/%m %H:%M:%S.%Z")
    full_msn = "> ERROR {} - {} \n\t MSN: {} \n\n".format(type_err, date, msn)
    try:
        f = open(LOG_ERR, "a")
        f.write(full_msn)
        f.close()
    except Exception as e:
        print("Error Fatal, No se pueden visualizar los mensajes en los Logs. ERROR:", e)

def log_trans(msn, indentation=0, nl=0, use_date=False):
    """
    Metodo para almacenamiento de mensajes asociados a los procesos ejectados 
    Durate la tranformacion de formatos.
    """
    indentation = indentation*"\t"
    nl = nl*"\n"
    if use_date:
        date = " - "+datetime.now().strftime("%Y/%m/%m %H:%M:%S.%Z")
    else:
        date = ""
    full_msn = "{}{}{}{}\n".format(nl ,indentation, msn, date)
    try:
        f = open(LOG_TRANS, "a")
        f.write(full_msn)
        f.close()
    except Exception as e:
        print("Error Fatal, No se pueden visualizar los mensajes en los Logs. ERROR:", e)


def main():
    try:
        # ------------------------------------------------
        # CREANDO CONEXION A LA BASE DE DATOS SI NO EXISTE
        conn = create_connection()
        x_video = get_one_active_process(conn)
        if x_video: 
            video_ok = False
            id_video, path, mail, name, name_video, url_video = x_video['id'],x_video['videofile'],x_video['email_competitor'],x_video['first_name_competitor'],x_video['title'],x_video['url']
            log_trans("INICIO VIDEO: {}".format(id_video),0,use_date=True)
            
            init_video = time.time()
            exit_code, path_out = convert_video(path)
            if exit_code == 0:
                if update_state(conn,id_video, path_out):
                    if send_mail(mail,name,name_video, url_video, id_video):
                        video_ok = True
            else:
                update_state_after_failure(conn, id_video)
            end_video = time.time()

            if video_ok:
                log_trans("VIDEO OK {0:.3f}s".format(end_video-init_video),0)
            else:
                log_trans("EXIT CODE {}s".format(exit_code),1)
                log_trans("VIDEO ERROR {0:.3f}s".format(end_video-init_video),1)
        conn.close()
    except Exception as e:
        print("Error Fatal durante la ejecución principal.")
        print("MAIN:",e)

if __name__ == '__main__':
    main()