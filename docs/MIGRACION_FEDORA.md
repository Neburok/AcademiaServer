# Plan de migración: Mitzlia → Fedora Linux

> Migración desde Windows 11 (rubenpc) a Fedora Linux.
> Repositorio: https://github.com/Neburok/AcademiaServer.git

---

## Resumen de fases

| Fase | Descripción | Estimado |
|------|-------------|----------|
| 1 | Preparar Fedora | 20 min |
| 2 | Clonar y configurar el proyecto | 15 min |
| 3 | Instalar Ollama y modelos | 30–60 min (descarga) |
| 4 | Configurar CUDA (opcional, para Whisper GPU) | 30–60 min |
| 5 | Migrar datos y archivos | 10 min |
| 6 | Verificar que todo funciona | 20 min |
| 7 | Configurar servicios systemd | 20 min |
| 8 | Prueba final completa | 15 min |

---

## Fase 1 — Preparar Fedora

### 1.1 Actualizar el sistema

```bash
sudo dnf upgrade --refresh -y
```

### 1.2 Instalar dependencias del sistema

```bash
sudo dnf install -y \
    python3 python3-pip python3-venv \
    git \
    sqlite \
    gcc gcc-c++ \
    ffmpeg                  # requerido por faster-whisper para audio
```

> **Nota:** `ffmpeg` en Fedora requiere RPM Fusion si no está habilitado:
> ```bash
> sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm -y
> sudo dnf install ffmpeg -y
> ```

### 1.3 Verificar versión de Python

Mitzlia requiere Python 3.10+.

```bash
python3 --version
```

---

## Fase 2 — Clonar y configurar el proyecto

### 2.1 Clonar desde GitHub

```bash
cd ~
git clone https://github.com/Neburok/AcademiaServer.git
cd AcademiaServer
```

### 2.2 Crear entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Crear el archivo `.env`

El `.env` no está en el repositorio (está en `.gitignore`). Copiarlo desde Windows o crearlo desde cero:

```bash
cp /ruta/desde/windows/.env .env   # si tienes acceso vía red/USB
# o bien crearlo manualmente:
nano .env
```

Contenido mínimo funcional (ajustar valores reales):

```dotenv
DB_PATH=academia.db
TELEGRAM_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

AI_PROVIDER=hybrid
AI_CLOUD_PROVIDER=openai          # o claude
AI_ENABLE_CLOUD_FALLBACK=true
AI_CLOUD_ALLOW_SENSITIVE=false

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

OPENAI_API_KEY=tu_key_aqui
OPENAI_CHAT_MODEL=gpt-4o-mini

ANTHROPIC_API_KEY=                # dejar vacío si no usas Claude
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-20241022

WHISPER_MODEL=small
WHISPER_LANGUAGE=es
WHISPER_DEVICE=cpu                # cambiar a cuda si instalaste drivers NVIDIA
WHISPER_COMPUTE_TYPE=int8         # cambiar a float16 con CUDA

SCHEDULER_INTERVAL_SECONDS=60
LOG_DIR=logs
OUTPUTS_DIR=outputs
TEMPLATES_DIR=templates
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 2.4 Inicializar la base de datos

```bash
source venv/bin/activate   # si no está activo
alembic upgrade head
```

---

## Fase 3 — Instalar Ollama y modelos

### 3.1 Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Ollama se instala como servicio systemd automáticamente. Verificar:

```bash
systemctl status ollama
ollama list
```

### 3.2 Descargar los modelos necesarios

```bash
ollama pull qwen3:8b          # modelo de chat (~5 GB)
ollama pull nomic-embed-text  # modelo de embeddings (~274 MB)
```

> Estos modelos equivalen a los configurados en `OLLAMA_CHAT_MODEL` y `OLLAMA_EMBED_MODEL`.

### 3.3 Verificar Ollama

```bash
curl http://localhost:11434/api/tags
```

---

## Fase 4 — Configurar CUDA para Whisper GPU (opcional)

Omitir esta fase si se usará `WHISPER_DEVICE=cpu`.

### 4.1 Habilitar RPM Fusion non-free

```bash
sudo dnf install https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm -y
```

### 4.2 Instalar drivers NVIDIA

```bash
sudo dnf install akmod-nvidia -y
sudo dnf install xorg-x11-drv-nvidia-cuda -y
```

> Reiniciar después de instalar: `sudo reboot`

### 4.3 Verificar CUDA

```bash
nvidia-smi
```

### 4.4 Actualizar `.env` para CUDA

```dotenv
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

---

## Fase 5 — Migrar datos y archivos desde Windows

### 5.1 Transferir la base de datos

La BD contiene todas las notas e historial. Copiar `academia.db` desde Windows:

```bash
# Opción A: vía red (si ambas máquinas están en la misma red o Tailscale)
scp usuario@rubenpc:/Repositorios/AcademiaServer/academia.db ~/AcademiaServer/

# Opción B: vía USB — copiar el archivo y luego:
cp /ruta/usb/academia.db ~/AcademiaServer/academia.db
```

### 5.2 Verificar migraciones sobre la BD migrada

```bash
cd ~/AcademiaServer
source venv/bin/activate
alembic upgrade head
```

Si ya estaba al día, no hace nada. Si hay migraciones pendientes, las aplica.

### 5.3 Migrar archivos generados (opcional)

```bash
# Documentos generados (planeaciones, guiones, diapositivas)
scp -r usuario@rubenpc:/Repositorios/AcademiaServer/outputs ~/AcademiaServer/

# Templates personalizados (si los hay)
scp -r usuario@rubenpc:/Repositorios/AcademiaServer/templates ~/AcademiaServer/
```

---

## Fase 6 — Verificar funcionamiento básico

### 6.1 Ejecutar tests

```bash
cd ~/AcademiaServer
source venv/bin/activate
pytest
```

### 6.2 Probar la API manualmente

```bash
# Terminal 1 — arrancar la API
source venv/bin/activate
python run_api.py &

# Terminal 2 — probar un endpoint
curl http://localhost:8000/list
```

### 6.3 Probar el CLI

```bash
python main.py list
python main.py save --content "Nota de prueba en Fedora" --title "Test migración"
python main.py search "prueba"
```

### 6.4 Probar Whisper (si se usa voz)

```bash
python -c "
from academiaserver.ai.whisper_transcriber import WhisperTranscriber
t = WhisperTranscriber(model_name='small', language='es', device='cpu', compute_type='int8')
print('Whisper OK')
"
```

---

## Fase 7 — Configurar servicios systemd

Reemplaza el `start_mitzlia.bat` con servicios del sistema que arrancan automáticamente.

### 7.1 Servicio: API REST

```bash
sudo nano /etc/systemd/system/mitzlia-api.service
```

```ini
[Unit]
Description=Mitzlia — API REST (FastAPI)
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=TU_USUARIO
WorkingDirectory=/home/TU_USUARIO/AcademiaServer
EnvironmentFile=/home/TU_USUARIO/AcademiaServer/.env
ExecStart=/home/TU_USUARIO/AcademiaServer/venv/bin/python run_api.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.2 Servicio: Bot de Telegram

```bash
sudo nano /etc/systemd/system/mitzlia-bot.service
```

```ini
[Unit]
Description=Mitzlia — Bot de Telegram
After=network.target mitzlia-api.service
Wants=mitzlia-api.service

[Service]
Type=simple
User=TU_USUARIO
WorkingDirectory=/home/TU_USUARIO/AcademiaServer
EnvironmentFile=/home/TU_USUARIO/AcademiaServer/.env
ExecStart=/home/TU_USUARIO/AcademiaServer/venv/bin/python run_bot.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.3 Servicio: Scheduler de recordatorios

```bash
sudo nano /etc/systemd/system/mitzlia-scheduler.service
```

```ini
[Unit]
Description=Mitzlia — Scheduler de recordatorios
After=network.target mitzlia-api.service

[Service]
Type=simple
User=TU_USUARIO
WorkingDirectory=/home/TU_USUARIO/AcademiaServer
EnvironmentFile=/home/TU_USUARIO/AcademiaServer/.env
ExecStart=/home/TU_USUARIO/AcademiaServer/venv/bin/python run_scheduler.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.4 Habilitar e iniciar los servicios

```bash
sudo systemctl daemon-reload

sudo systemctl enable --now mitzlia-api.service
sudo systemctl enable --now mitzlia-bot.service
sudo systemctl enable --now mitzlia-scheduler.service
```

### 7.5 Verificar estado

```bash
systemctl status mitzlia-api
systemctl status mitzlia-bot
systemctl status mitzlia-scheduler
```

### 7.6 Ver logs en tiempo real

```bash
journalctl -u mitzlia-bot -f        # logs del bot
journalctl -u mitzlia-api -f        # logs de la API
journalctl -u mitzlia-scheduler -f  # logs del scheduler
```

### 7.7 Comandos de operación cotidiana

```bash
# Reiniciar un servicio (tras actualizar código)
sudo systemctl restart mitzlia-bot

# Detener todo Mitzlia
sudo systemctl stop mitzlia-api mitzlia-bot mitzlia-scheduler

# Arrancar todo Mitzlia
sudo systemctl start mitzlia-api mitzlia-bot mitzlia-scheduler
```

---

## Fase 8 — Prueba final completa

1. Enviar un mensaje de texto al bot de Telegram → verificar respuesta y que se guarda la nota.
2. Enviar una nota de voz → verificar transcripción y guardado.
3. Pedir una planeación didáctica → verificar que el agente responde y envía el `.md`.
4. Crear un recordatorio (ej. "recuérdame mañana a las 10:00 revisar el examen") → esperar que el scheduler lo dispare.
5. Consultar `python main.py list` → verificar que aparece la nota guardada desde el bot.

---

## Actualizar Mitzlia en el futuro

Una vez migrado, el flujo para actualizar desde GitHub es:

```bash
cd ~/AcademiaServer
git pull origin main
source venv/bin/activate
pip install -r requirements.txt          # si hay nuevas dependencias
alembic upgrade head                     # si hay nuevas migraciones
sudo systemctl restart mitzlia-api mitzlia-bot mitzlia-scheduler
```

---

## Equivalencias Windows → Linux

| Windows | Fedora Linux |
|---------|-------------|
| `start_mitzlia.bat` | `sudo systemctl start mitzlia-api mitzlia-bot mitzlia-scheduler` |
| `stop_mitzlia.bat` | `sudo systemctl stop mitzlia-api mitzlia-bot mitzlia-scheduler` |
| Tres ventanas cmd abiertas | Tres servicios systemd en background |
| `venv\Scripts\activate` | `source venv/bin/activate` |
| Logs en `logs/` | Logs en `logs/` + `journalctl -u mitzlia-*` |
