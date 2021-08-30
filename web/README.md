# VIDEOSHARE WEB

En esta guía se exponen los pasos a ejecutar para generar la AMI (Imagen) requerida durante conformación de la capa web del servicio **VideoShare**.

Consideraciónes [es]:

    - Las siguientes lineas funciona para 'Debian 10 (HVM), SSD Volume Type - ami-07d02ee1eeb0c996c (64-bit x86) / ami-08b2293fdd2deba2a (64-bit Arm)'
    - El python para este proyecto de ser 3.5 o superior.

## 1. Linux

```bash
sudo apt-get update
sudo apt install ffmpeg libsm6 libxext6 libxrender-dev
sudo apt-get install python3-pip python3-dev libpq-dev nginx

sudo apt install gnupg
sudo apt update
wget https://dev.mysql.com/get/mysql-apt-config_0.8.13-1_all.deb
sudo dpkg -i mysql-apt-config*
sudo apt-get install mysql-server
rm mysql-apt-config*
```

Only if you need:

```bash
sudo systemctl status mysql
sudo systemctl start mysql
```

## 2. Python virtual environment

```bash
cd videoshare
pip3 install virtualenv
~/.local/bin/virtualenv vsvenv
source vsvenv/bin/activate
```

## 3. Pip dependencies

```bash
pip3 install django==2.0.5 gunicorn
pip3 install requests opencv-python pillow pymysql
pip3 install cryptography
```

## 4. Django init

```bash
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
deactivate
```

## 5. Gunicorn & Nginx configuration

For more information about Gunicorn & Nginx [Check this.](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04)

You can check gunicorn whit the next command:

```bash
gunicorn --bind 0.0.0.0:8000 videoshare.wsgi
```

### Gunicorn socket

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

### Gunicorn service

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
ExecStart=/home/admin/videoshare/vsvenv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/admin/videoshare/videoshare.sock videoshare.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start and Test Gunicorn

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
file /run/gunicorn.sock
curl --unix-socket /run/gunicorn.sock localhost
sudo systemctl status gunicorn
```

```bash
sudo nano /etc/nginx/sites-available/videoshare
```

Paste this:

```js
server {
    listen 8080;
    server_name 172.31.27.251; 

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

Add the next line in the http section of the '/etc/nginx/nginx.conf' file.

```js
    client_max_body_size 100M;
```

### Restart Nginx

```bash
sudo systemctl restart nginx
```

---------------------------

#### If you need to stop

```bash
sudo systemctl stop nginx
sudo systemctl stop gunicorn
```

#### If you need to restart

```bash
# sudo systemctl enable gunicorn.socket
sudo systemctl start gunicorn.socket
file /run/gunicorn.sock
curl --unix-socket /run/gunicorn.sock localhost
sudo systemctl status gunicorn
sudo nginx -t
sudo systemctl restart nginx
```

#### Stop and Start nginx and gunicorn

```bash
sudo systemctl stop nginx
sudo systemctl stop gunicorn
```

```bash
sudo systemctl start nginx
sudo systemctl start gunicorn
```