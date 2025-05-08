from mcp.server.fastmcp import FastMCP
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time

# Crear el servidor MCP
mcp = FastMCP("WebInfoExtractor")

# Configuración del servidor SMTP
SMTP_SERVER = "smtp.prueba.com"
SMTP_PORT = puertodado
EMAIL_ADDRESS = "correo_smtp@prueba.com"
EMAIL_PASSWORD = "clave_obtenida_gmail"

# Función para truncar el contenido si es demasiado largo
def truncate_content(content: str, max_length: int = 5000) -> str:
    if len(content) > max_length:
        content = content[:max_length] + "\n\n[Contenido truncado debido a su longitud]"
    return content

# Herramienta para descargar el contenido de una página web usando Selenium (Edge)
@mcp.tool()
def fetch_web_content(url: str, max_length: int = 2000) -> dict:
    # Configurar opciones de Edge
    edge_options = EdgeOptions()
    edge_options.add_argument("--start-maximized")  # Maximizar ventana
    edge_options.add_argument("--disable-infobars")  # Desactivar mensajes de Edge
    edge_options.add_argument("--disable-extensions")  # Desactivar extensiones
    # edge_options.add_argument("--headless")  # Quita este comentario si NO quieres ver el navegador

    try:
        # Iniciar el navegador Edge con WebDriver Manager
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=edge_options)
        driver.get(url)

        # Simular desplazamiento animado
        scroll_pause_time = 1  # Tiempo entre desplazamientos
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Extraer contenido HTML
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        # Truncar el contenido si excede la longitud máxima
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Contenido truncado debido a su longitud]"

        # Devolver un JSON con estado "ok" y el controlador del navegador
        return {
            "status": "ok",
            "message": "Contenido extraído correctamente.",
            "data": text,
            "driver": driver  # Mantener el controlador del navegador
        }

    except Exception as e:
        # Devolver un JSON con estado "error"
        return {
            "status": "error",
            "message": f"Error al descargar el contenido: {str(e)}",
            "data": None
        }

# Herramienta para enviar correos electrónicos
@mcp.tool()
def send_email(to_email: str, subject: str, body: str) -> str:
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Conectar al servidor SMTP y enviar el correo
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())

        return f"Correo enviado exitosamente a {to_email}"
    except smtplib.SMTPAuthenticationError:
        return "Error de autenticación: verifica tus credenciales de correo."
    except smtplib.SMTPException as e:
        return f"Error al conectar al servidor SMTP: {str(e)}"
    except Exception as e:
        return f"Error inesperado al enviar el correo: {str(e)}"

# Prompt para guiar la interacción con el servidor MCP
@mcp.prompt()
def extract_and_send_info(url: str, to_email: str) -> str:
    # Paso 1: Descargar el contenido de la página
    resultado = fetch_web_content(url)

    # Verificar si ocurrió un error
    if resultado["status"] == "error":
        return json.dumps({
            "status": "error",
            "message": resultado["message"]
        }, ensure_ascii=False, indent=2)

    # Paso 2: Truncar el contenido si es demasiado largo (ya se trunca dentro de fetch_web_content)
    content = resultado["data"]

    # Si el navegador se mantuvo abierto, cerrarlo aquí
    if "driver" in resultado and resultado["driver"]:
        resultado["driver"].quit()

    # Paso 3: Enviar el contenido por correo electrónico
    subject = f"Información extraída de {url}"
    email_result = send_email(to_email, subject, content)

    # Paso 4: Devolver un resumen en JSON
    return json.dumps({
        "status": "ok",
        "to_email": to_email,
        "subject": subject,
        "body": content,
        "result": email_result
    }, ensure_ascii=False, indent=2)

# Ejecutar el servidor MCP
if __name__ == "__main__":
    print("Iniciando servidor MCP...")
    mcp.run(transport='stdio')
