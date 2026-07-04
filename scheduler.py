import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

HORA_ENVIO = "22:10"
SCRIPT_ENVIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_sender.py")
PYTHON_PATH = sys.executable

def enviar_whatsapp():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Ejecutando envio de mensajes...")

    try:
        result = subprocess.run(
            [PYTHON_PATH, SCRIPT_ENVIO],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"[ERROR] {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[ERROR] El envio tardo mas de 5 minutos.")
    except Exception as e:
        print(f"[ERROR] {e}")

schedule.every().day.at(HORA_ENVIO).do(enviar_whatsapp)

print(f"Programador iniciado. Los mensajes se enviaran diariamente a las {HORA_ENVIO}")
print(f"Python: {PYTHON_PATH}")
print("Mantenga esta ventana abierta. Presione Ctrl+C para detener.")

try:
    while True:
        schedule.run_pending()
        time.sleep(30)
except KeyboardInterrupt:
    print("\nProgramador detenido por el usuario.")
