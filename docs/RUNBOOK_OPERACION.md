# Runbook de Operacion - Mitzlia (AcademiaServer)

Este documento describe como operar Mitzlia en entorno local y en mini-PC para ejecucion continua.

## 1. Requisitos

- Python 3.12+
- Entorno virtual (`venv`)
- Token de Telegram valido
- `TELEGRAM_CHAT_ID` del usuario destino

## 2. Variables de entorno

Archivo `.env` recomendado:

```env
INBOX_DIR=inbox
LOG_DIR=logs
TELEGRAM_TOKEN=<token_bot>
TELEGRAM_CHAT_ID=<chat_id_numerico>
SCHEDULER_INTERVAL_SECONDS=60
REMINDER_MAX_RETRIES=3
REMINDER_RETRY_DELAY_SECONDS=5
```

## 3. Arranque local

1. Activar entorno:
   - PowerShell: `.\venv\Scripts\Activate.ps1`
2. Instalar dependencias:
   - `pip install -r requirements.txt`
3. Ejecutar bot:
   - `python -m academiaserver.clients.telegram_bot`

Al iniciar, Mitzlia valida:
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`
- permisos de escritura en `INBOX_DIR`
- permisos de escritura en `LOG_DIR`

Si alguna validacion falla, el proceso se detiene con error explicito.

## 4. Verificacion operativa

1. Enviar nota por Telegram.
2. Confirmar respuesta `Nota guardada con ID: ...`.
3. Confirmar archivo JSON creado en `INBOX_DIR`.
4. Enviar recordatorio con hora cercana.
5. Confirmar envio del recordatorio y que `metadata.reminded=true`.

## 5. Logs estructurados

Los eventos se registran en `logs/activity.log` como JSON por linea.

Eventos relevantes:
- `bot_startup_validation_ok`
- `bot_note_saved`
- `bot_note_save_error`
- `scheduler_due_reminders_found`
- `bot_reminder_sent`
- `bot_reminder_send_failed`
- `bot_reminder_send_exhausted`
- `scheduler_reminder_marked`

## 6. Politica de reintentos

Para cada recordatorio vencido:
- se intenta enviar hasta `REMINDER_MAX_RETRIES`
- entre intentos espera `REMINDER_RETRY_DELAY_SECONDS`
- solo se marca como enviado si el envio fue exitoso

Esto evita perder recordatorios en fallos transitorios.

## 7. Reinicio seguro

El reinicio del bot es seguro porque:
- recordatorios ya enviados tienen `metadata.reminded=true`
- el scheduler ignora recordatorios ya marcados

Si un envio falla en todos los intentos, el recordatorio queda pendiente para el siguiente ciclo.

## 8. Operacion en mini-PC (Windows)

Recomendacion: ejecutar mediante Programador de tareas.

Configuracion sugerida:
- Trigger: al iniciar sesion o al arrancar el equipo
- Accion: ejecutar `powershell.exe`
- Argumentos:
  - `-ExecutionPolicy Bypass -File C:\Repositorios\AcademiaServer\run_mitzlia.ps1`

Script ejemplo `run_mitzlia.ps1`:

```powershell
Set-Location "C:\Repositorios\AcademiaServer"
.\venv\Scripts\Activate.ps1
python -m academiaserver.clients.telegram_bot
```

## 9. Recuperacion ante incidentes

Si no llegan recordatorios:
1. Revisar `logs/activity.log`.
2. Validar conectividad a Telegram.
3. Confirmar que `TELEGRAM_CHAT_ID` sea correcto.
4. Verificar que el JSON del recordatorio tenga `metadata.datetime` valido.
5. Reiniciar proceso del bot.

Si hay errores de escritura:
1. Confirmar permisos de `INBOX_DIR` y `LOG_DIR`.
2. Validar que no esten bloqueados por otro proceso.
