# Guia de Instalação e Configuração da API Antecedentes

Este guia descreve os passos necessários para configurar e executar a API Antecedentes em um ambiente Ubuntu.

---

## 1. Instalar Dependências do Projeto

Atualize os pacotes do sistema e instale os componentes necessários:

```sh
sudo apt update
sudo apt install ubuntu-desktop
sudo apt install tightvncserver
sudo apt install gnome-panel gnome-settings-daemon metacity nautilus gnome-terminal
sudo apt install -y python3-venv
sudo apt install git
```

---

## 2. Instalar o Google Chrome e o ChromeDriver

```sh
sudo apt install curl apt-transport-https gdebi
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install chromium-chromedriver
sudo gdebi google-chrome
```

Após a instalação, abra o Google Chrome e instale a extensão **2captcha**:

[Configurar a extensão 2captcha](https://2captcha.com/pt/enterpage)

---

## 3. Clonar o Repositório da Aplicação

Navegue até a pasta desejada e clone o repositório:

```sh
cd /home/ubuntu
git clone https://github.com/RHamudi/AntecedentesAPI.git

cd AntecedentesAPI

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Configurar Serviços do Sistema

### 4.1 Configuração do Serviço da API

Crie e edite o arquivo de serviço:

```sh
sudo nano /etc/systemd/system/api.service
```

Adicione o seguinte conteúdo:

```ini
[Unit]
Description=API Antecedentes
After=network.target

[Service]
User=root
WorkingDirectory=/home/ubuntu/AntecedentesAPI
ExecStart=/bin/bash -c 'source /home/ubuntu/AntecedentesAPI/venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 80'
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4.2 Configuração do Serviço da Interface Gráfica

Crie e edite o arquivo de serviço:

```sh
sudo nano /etc/systemd/system/vncserver.service
```

Adicione o seguinte conteúdo:

```ini
[Unit]
Description=Start VNC Server at startup
After=network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/home/ubuntu/AntecedentesAPI
Environment=DISPLAY=:1
ExecStart=/usr/bin/vncserver :1 -geometry 1920x1080 -depth 24
ExecStop=/usr/bin/vncserver -kill :1
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4.3 Configuração do Celery (Sistema de Task)

Crie e edite o arquivo de serviço:

```sh
sudo nano /etc/systemd/system/celery.service
```

Adicione o seguinte conteúdo:

```ini
[Unit]
Description=API Antecedentes com Celery
After=network.target

[Service]
User=root
WorkingDirectory=/home/ubuntu/AntecedentesAPI
Environment=DISPLAY=:1
ExecStart=/bin/bash -c 'source /home/ubuntu/AntecedentesAPI/venv/bin/activate && celery -A task worker -l info --pool=solo'
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 5. Iniciar e Verificar os Serviços

Após configurar os serviços, execute os seguintes comandos:

```sh
sudo systemctl daemon-reload
sudo systemctl restart api.service
sudo systemctl status api.service
```

Para garantir que o Celery e o servidor VNC também estão rodando, use:

```sh
sudo systemctl restart celery.service
sudo systemctl status celery.service
sudo systemctl restart vncserver.service
sudo systemctl status vncserver.service
```

---

## Conclusão

Agora sua API Antecedentes está configurada e rodando no servidor! Se precisar fazer alterações ou resolver problemas, utilize `sudo systemctl status <serviço>` para verificar logs e `sudo journalctl -u <serviço> -f` para logs em tempo real.
