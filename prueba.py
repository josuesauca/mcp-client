from mcp.server.fastmcp import FastMCP
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import json

# Crear el servidor MCP
mcp = FastMCP("WebInfoExtractor")

# Configuración del servidor SMTP
SMTP_SERVER = "server.smtp.com"
SMTP_PORT = 54
EMAIL_ADDRESS = "example@gmail.com"
EMAIL_PASSWORD = "codigoprueba"

# Función para truncar el contenido si es demasiado largo
def truncate_content(content: str, max_length: int = 5000) -> str:
    if len(content) > max_length:
        content = content[:max_length] + "\n\n[Contenido truncado debido a su longitud]"
    return content


# Herramienta para descargar el contenido de una página web
@mcp.tool()
def fetch_web_content(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            markdown_content = f"# Contenido de {url}\n\n{response.text[:1000]}..."
            return markdown_content

        except requests.RequestException as e:
            print(f"Intento {attempt + 1} fallido: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return f"Error al descargar el contenido: {str(e)}"

    return "No se pudo descargar el contenido después de varios intentos."

# Herramienta para enviar correos electrónicos
@mcp.tool()
def send_email(to_email: str, subject: str, body: str) -> str:
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())

        return f"Correo enviado exitosamente a {to_email}"
    except smtplib.SMTPAuthenticationError:
        return "Error de autenticación: verifica tus credenciales de correo."
    except smtplib.SMTPException as e:
        return f"Error al conectar al servidor SMTP: {str(e)}"
    except Exception as e:
        return f"Error inesperado al enviar el correo: {str(e)}"

# Prompt para guiar la interacción con Claude
@mcp.prompt()
def extract_and_send_info(url: str, to_email: str) -> str:
    """
    Extrae información de una página web y la envía por correo electrónico.
    """
    # Paso 1: Descargar el contenido de la página
    content = fetch_web_content(url)

    if "Error" in content:
        return content  # Devolver el error si no se pudo descargar el contenido

    # Paso 2: Truncar el contenido si es demasiado largo
    content = truncate_content(content)

    # Paso 3: Enviar el contenido por correo electrónico
    subject = f"Información extraída de {url}"
    email_result = send_email(to_email, subject, content)

    return json.dumps({
        "to_email": to_email,
        "subject": subject,
        "body": content,
        "result": email_result
    }, ensure_ascii=False, indent=2)

# Ejecutar el servidor MCP
if __name__ == "__main__":
    print("Iniciando servidor MCP...")
    mcp.run(transport='stdio')
