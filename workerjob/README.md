# VIDEOSHARE WORKER

En esta guía se exponen los pasos a ejecutar para generar la AMI (Imagen) requerida durante conformación de la capa worker del servicio **VideoShare**.

Consideraciónes [es]:

    - Las siguientes lineas funciona para 'Debian 10 (HVM), SSD Volume Type - ami-07d02ee1eeb0c996c (64-bit x86) / ami-08b2293fdd2deba2a (64-bit Arm)'
    - El python para este proyecto de ser 3.5 o superior.

## 1. Linux

```bash
sudo apt-get update -y
sudo apt install libsm6 libxext6 libxrender-dev unzip -y
sudo apt-get install python3-pip python3-dev libpq-dev -y
sudo apt-get install ffmpeg libsm6 libxext6  -y
wget https://github.com/JuanCatica/VideoShare/archive/refs/heads/main.zip
unzip main.zip
rm main.zip
mv VideoShare-main/workerjob .
rm -rf VideoShare-main/
cd workerjob
```

## 2. Python virtual environment

```bash
pip3 install virtualenv
~/.local/bin/virtualenv vsvenv
source vsvenv/bin/activate
```

## 3. Pip dependencies

```bash
pip3 install requests opencv-python pillow pymysql cryptography boto3 apscheduler
deactivate
```

## 4. Set up cronjob

Abre el editor de texto para incorporar una tarea mediante:

```bash
crontab -e
```

Pega lo siguiente:

```bash
* * * * * bash /home/admin/workerjob/worker.sh
```