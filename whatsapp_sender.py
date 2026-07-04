import pandas as pd
import time
import random
import logging
from datetime import datetime
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

ARCHIVO_CSV = "mensajes.csv"
PERFIL_CHROME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
ARCHIVO_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_envios.log")
TIMEOUT_LOGIN = 120
PAUSA_LARGA_CADA = 10
PAUSA_LARGA_SEG = 30

logging.basicConfig(
    filename=ARCHIVO_LOG,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def cargar_mensajes(archivo):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)
    if not os.path.exists(ruta):
        print(f"Error: No se encuentra el archivo '{ruta}'")
        return []

    try:
        df = pd.read_csv(ruta)
        df.columns = df.columns.str.strip()
        if "contacto" not in df.columns or "mensaje" not in df.columns:
            print(f"Error: El CSV debe tener las columnas 'contacto' y 'mensaje'")
            print(f"Columnas encontradas: {list(df.columns)}")
            return []
        return df.to_dict("records")
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return []


def formatear_numero(contacto):
    contacto = str(contacto).strip().replace(" ", "").replace("-", "")
    if not contacto.startswith("+"):
        contacto = "+" + contacto
    return contacto


def pausa_aleatoria(minimo, maximo):
    time.sleep(random.uniform(minimo, maximo))


def iniciar_driver():
    print("Iniciando Chrome...")
    opts = Options()
    opts.add_argument(f"--user-data-dir={PERFIL_CHROME}")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"Error al iniciar Chrome: {e}")
        sys.exit(1)


def esperar_login(driver):
    driver.get("https://web.whatsapp.com")
    print("\nEsperando inicio de sesion en WhatsApp Web...")

    if os.path.isdir(PERFIL_CHROME) and any(
        not item.startswith(".")
        for item in os.listdir(PERFIL_CHROME)
    ):
        print("(Perfil detectado, la sesion deberia restaurarse automaticamente)")

    print("Si ves un codigo QR, escanealo con tu telefono.")
    print("Esperando... (maximo 2 minutos)")
    sys.stdout.flush()

    selectores = [
        By.CSS_SELECTOR, '[contenteditable]',
        By.CSS_SELECTOR, '[role="textbox"]',
        By.CSS_SELECTOR, '[aria-label*="Chat list"]',
        By.CSS_SELECTOR, '[data-testid="chat-list"]',
    ]

    inicio = time.time()
    while time.time() - inicio < TIMEOUT_LOGIN:
        for i in range(0, len(selectores), 2):
            try:
                driver.find_element(selectores[i], selectores[i+1])
                print("Sesion iniciada correctamente.\n")
                return True
            except NoSuchElementException:
                continue
        time.sleep(2)

    print("Tiempo de espera agotado. No se pudo iniciar sesion en WhatsApp Web.")
    try:
        driver.save_screenshot("error_login.png")
        print("(Se guardo una captura de pantalla como 'error_login.png')")
    except:
        pass
    return False


def verificar_error_numero(driver):
    try:
        driver.find_element(
            By.XPATH,
            "//*[contains(text(),'no esta registrada') or contains(text(),\"isn't registered\") or contains(text(),'not registered')]",
        )
        return True
    except NoSuchElementException:
        return False


def enviar_mensaje_individual(driver, numero, mensaje):
    url = f"https://web.whatsapp.com/send?phone={numero}"
    driver.get(url)
    pausa_aleatoria(5, 8)

    if verificar_error_numero(driver):
        return False, "Numero no registrado en WhatsApp"

    try:
        caja = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[contenteditable][aria-placeholder]')
            )
        )
        caja.click()
        pausa_aleatoria(0.5, 1.5)
        caja.send_keys(mensaje)
        pausa_aleatoria(1, 2)
        caja.send_keys(Keys.ENTER)
        pausa_aleatoria(2, 4)

        return True, "Enviado correctamente"

    except TimeoutException:
        return False, "No se pudo acceder al chat"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


def enviar_mensajes(contactos):
    total = len(contactos)
    print(f"\n{'='*50}")
    print(f"Iniciando envio de {total} mensaje(s)...")
    print(f"{'='*50}")

    driver = iniciar_driver()
    if not esperar_login(driver):
        driver.quit()
        return

    enviados = 0
    fallidos = 0

    logging.info(f"Iniciando envio de {total} mensaje(s)")

    for i, item in enumerate(contactos):
        contacto = formatear_numero(item["contacto"])
        mensaje = str(item["mensaje"]).strip()
        numero_limpio = contacto.replace("+", "")

        print(f"[{i+1}/{total}] Enviando a {contacto}...", end=" ")
        sys.stdout.flush()

        exito, motivo = enviar_mensaje_individual(driver, numero_limpio, mensaje)

        if exito:
            logging.info(f"OK - {contacto}: {motivo}")
            print(f"OK - {motivo}")
            enviados += 1
        else:
            logging.warning(f"FALLO - {contacto}: {motivo}")
            print(f"FALLO - {motivo}")
            fallidos += 1

        pausa_aleatoria(3, 6)

        if (i + 1) % PAUSA_LARGA_CADA == 0 and (i + 1) < total:
            print(f"  Pausa de {PAUSA_LARGA_SEG}s para evitar deteccion...")
            time.sleep(PAUSA_LARGA_SEG)

    print(f"\n{'='*50}")
    print("Resumen final:")
    print(f"  Total procesados: {total}")
    print(f"  Enviados: {enviados}")
    print(f"  Fallidos: {fallidos}")
    print(f"{'='*50}")
    logging.info(f"Resumen - Total: {total} | Enviados: {enviados} | Fallidos: {fallidos}")

    driver.quit()


if __name__ == "__main__":
    contactos = cargar_mensajes(ARCHIVO_CSV)
    if not contactos:
        print("\nNo hay mensajes para enviar. Saliendo...")
        sys.exit(1)

    ahora = datetime.now()
    print(f"Hora actual: {ahora.strftime('%H:%M')}")
    enviar_mensajes(contactos)
