# VIDEOSHARE WEB (web-ami)

En esta guía se exponen los pasos a ejecutar para generar la AMI (Imagen) requerida durante conformación de la capa web del servicio **VideoShare**.

Consideraciónes [es]:

    - Las siguientes lineas funciona para 'Debian 10 (HVM), SSD Volume Type - ami-07d02ee1eeb0c996c (64-bit x86) / ami-08b2293fdd2deba2a (64-bit Arm)'
    - El python para este proyecto de ser 3.5 o superior.

## 1. Linux

```bash
sudo apt-get update -y
sudo apt install libsm6 libxext6 libxrender-dev unzip -y
sudo apt-get install python3-pip python3-dev libpq-dev nginx -y
wget https://github.com/JuanCatica/VideoShare/archive/refs/heads/main.zip
unzip main.zip
rm main.zip
mv VideoShare-main/web .
mv web videoshare
rm -rf VideoShare-main/
cd videoshare
```

## 2. Python virtual environment

```bash
pip3 install virtualenv
~/.local/bin/virtualenv vsvenv
source vsvenv/bin/activate
```

## 3. Pip dependencies

```bash
pip3 install django gunicorn requests opencv-python pillow pymysql cryptography boto3
```

## 4. Django init

```bash
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
```

## 5. Gunicorn & Nginx configuration

For more information about Gunicorn & Nginx [Check this.](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04)

Se puede verficicar la funcionalidad de la web mediante el siguiente comando:

```bash
gunicorn --bind 0.0.0.0:8000 videoshare.wsgi
```

Una vez se encuente ejecutando, se puede ingresar a la página web mediante la IP Publica asignada a la instancias EC2 en la que se encuentra en este instante. Accediendo a: ```http://<IP-Publica-EC2>:8000```

Una vez se ha verificado el acceso a la app es conveniente desactivar el entorno virtual de python. 

```bash
deactivate
```

### 5.1 Gunicorn socket

```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Paste this:

```toml
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

### 5.2 Gunicorn service

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Paste this:

```toml
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=admin
Group=www-data
WorkingDirectory=/home/admin/videoshare
ExecStart=/home/admin/videoshare/vsvenv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    videoshare.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5.3 Start and Test Gunicorn

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl status gunicorn.socket
file /run/gunicorn.sock

# En caso de error
# sudo journalctl -u gunicorn
```

```bash
sudo systemctl status gunicorn
curl --unix-socket /run/gunicorn.sock localhost
sudo systemctl status gunicorn

# En caso de error
# sudo journalctl -u gunicorn

# En caso de ejecutar cambios
#sudo systemctl daemon-reload
#sudo systemctl restart gunicorn
```

```bash
sudo nano /etc/nginx/sites-available/videoshare
```

Paste this:

```js
server {
    listen 8080;
    server_name <EC2-Private-IP>; 

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/admin/videoshare;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

### Link

```bash
sudo ln -s /etc/nginx/sites-available/videoshare /etc/nginx/sites-enabled
```

### Config Nginx to upload lagger files

Add the next line in the ```http``` section of the '/etc/nginx/nginx.conf' file.

```bash
sudo nano /etc/nginx/nginx.conf
```

```js
    client_max_body_size 100M;
```

### Restart Nginx

```bash
sudo nginx -t
sudo systemctl restart nginx
```

---------------------------

#### If you need to stop

```bash
sudo systemctl stop nginx
sudo systemctl stop gunicorn
```