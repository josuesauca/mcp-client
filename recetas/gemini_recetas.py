import os
import requests
from google import genai
from google.genai import types
import pathlib
import json

# Configurar el cliente de GenAI
client = genai.Client(api_key="")

# Carpeta donde están los PDFs
pdf_folder = pathlib.Path('recetas')

# URL de la API Flask
api_url = "http://127.0.0.1:5000/cocina"

# Prompt para extraer información
prompt = """
Analiza cuidadosamente el documento proporcionado y extrae la siguiente información:

Nombre de la receta
Ingredientes (separados por comas)
Pasos de preparación (cada paso en una línea)
Categoría de la receta

Si algún campo no está disponible, déjalo como cadena vacía ("").
Solo devuelve el JSON, sin ningún otro texto adicional.
"""

def extraer_datos_con_llm(texto_pdf):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_bytes(data=texto_pdf.encode('utf-8'), mime_type='text/plain'),
            prompt
        ]
    )
    respuesta_gemini = response.text.strip()

    # Limpiar la respuesta
    if respuesta_gemini.startswith("```json"):
        respuesta_gemini = respuesta_gemini[7:]
    if respuesta_gemini.endswith("```"):
        respuesta_gemini = respuesta_gemini[:-3]

    try:
        datos_json = json.loads(respuesta_gemini)
        return datos_json
    except json.JSONDecodeError as e:
        print(f"Error al parsear JSON: {e}")
        return None

# Función para procesar un único PDF
def procesar_pdf(filepath):
    try:
        # Generar contenido utilizando GenAI
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=filepath.read_bytes(),
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )

        print(f"Respuesta de Gemini para {filepath.name}:")
        print(response.text)

        # Obtener la respuesta de Gemini
        respuesta_gemini = response.text

        # Limpiar la respuesta: eliminar ```json y ```
        respuesta_limpia = respuesta_gemini.strip()
        if respuesta_limpia.startswith("```json"):
            respuesta_limpia = respuesta_limpia[7:]  # Eliminar "```json"
        if respuesta_limpia.endswith("```"):
            respuesta_limpia = respuesta_limpia[:-3]  # Eliminar "```"

        # Intentar parsear a JSON
        try:
            datos_json = json.loads(respuesta_limpia)
            print(f"Datos extraídos de {filepath.name}:")
            print(json.dumps(datos_json, indent=2, ensure_ascii=False))

            # Validar que los datos no estén vacíos
            if not datos_json.get("Nombre de la receta") or \
               not datos_json.get("Ingredientes") or \
               not datos_json.get("Pasos de preparación"):
                print(f"❌ Datos incompletos para {filepath.name}. No se enviarán a la API.")
                return

            # Transformar los datos para que coincidan con la estructura esperada por la API Flask
            datos_para_api = {
                "datos": {
                    "nombre": datos_json.get("Nombre de la receta", ""),
                    "ingredientes": datos_json.get("Ingredientes", ""),
                    "preparacion": datos_json.get("Pasos de preparación", ""),
                    "categoria": datos_json.get("Categoría de la receta", "")
                }
            }

            # Realizar la solicitud POST a la API Flask
            response_api = requests.post(
                api_url,
                json=datos_para_api,
                headers={"Content-Type": "application/json"}
            )

            # Verificar la respuesta de la API
            if response_api.status_code == 201:
                print(f"Datos guardados correctamente en la API Flask para {filepath.name}.")
                print(response_api.json())
            else:
                print(f"Error al enviar datos a la API Flask para {filepath.name}. Código de estado: {response_api.status_code}")
                print(response_api.json())

        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON después de limpiar para {filepath.name}: {e}")
            print(f"Respuesta original de Gemini para {filepath.name}:")
            print(respuesta_gemini)

    except Exception as e:
        print(f"❌ Error al procesar {filepath.name}: {e}")

# Iterar sobre todos los PDFs en la carpeta
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        filepath = pdf_folder / filename
        print(f"Procesando archivo: {filepath}")
        procesar_pdf(filepath)
