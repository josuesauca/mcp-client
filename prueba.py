from mcp.server.fastmcp import FastMCP
import requests

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import json


# Crear el servidor MCP
mcp = FastMCP("WebInfoExtractor")

# Configuración del servidor SMTP
SMTP_SERVER = "server.smtp.com"
SMTP_PORT = 111
EMAIL_ADDRESS = "prueba@gmail.com"
EMAIL_PASSWORD = "prueba123"

# Función para truncar el contenido si es demasiado largo
def truncate_content(content: str, max_length: int = 5000) -> str:
    if len(content) > max_length:
        content = content[:max_length] + "\n\n[Contenido truncado debido a su longitud]"
    return content


# Herramienta para descargar el contenido de una página web
@mcp.tool()
def fetch_web_content(url: str, max_length: int = 2000) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parsear el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        # Truncar el contenido si excede la longitud máxima
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Contenido truncado debido a su longitud]"

        # Devolver un JSON con estado "ok"
        return {
            "status": "ok",
            "message": "Contenido extraído correctamente.",
            "data": text
        }

    except requests.RequestException as e:
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

# Prompt para guiar la interacción con Claud
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

    # Paso 2: Truncar el contenido si es demasiado largo (ya se trunca dentro de fetch_web_content, así que podrías omitir esta parte si quieres)
    content = resultado["data"]

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


"""
from unittest.mock import patch, MagicMock
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Función para enviar correo (sin cambios)
def send_email(to_email: str, subject: str, body: str) -> str:
    SMTP_SERVER = "server.smtp.com"
    SMTP_PORT = 111
    EMAIL_ADDRESS = "prueba@gmail.com"
    EMAIL_PASSWORD = "prueba123"

    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Usar SMTP_SSL para el puerto 465
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Autenticación
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())  # Envío del correo

        return f"Correo enviado exitosamente a {to_email}"

    except smtplib.SMTPAuthenticationError:
        return "Error de autenticación: verifica tus credenciales de correo."
    except smtplib.SMTPException as e:
        return f"Error al conectar al servidor SMTP: {str(e)}"
    except Exception as e:
        return f"Error inesperado al enviar el correo: {str(e)}"


# Clase de prueba unitaria
if __name__ == "__main__":
    # Datos del correo
    to_email = "juan.d.carreno@unl.edu.ec"  # Cambia esto por el correo del destinatario
    subject = "Prueba de Envío de Correo Real"
    body = "Este es un mensaje de prueba enviado desde Python."

    # Intentar enviar el correo
    result = send_email(to_email, subject, body)

    # Mostrar el resultado
    print(result)
"""
