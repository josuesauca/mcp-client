from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import time
import csv
from fpdf import FPDF
from PyPDF2 import PdfReader
import json

# Importar Gemini
from google import genai
client = genai.Client(api_key="")

# Inicializar servidor MCP
mcp = FastMCP("WebQuoteProcessor")

# --- Funciones auxiliares ---

def clean_text(text):
    replacements = {
        "\u201c": '"',  # Comilla abierta
        "\u201d": '"',  # Comilla cerrada
        "\u2018": "'",  # Comilla simple abierta
        "\u2019": "'",  # Comilla simple cerrada
        "\u2013": "-",  # En dash
        "\u2026": "...", # Elipsis
        "\u00e1": "a",   # Letras acentuadas
        "\u00e9": "e",
        "\u00ed": "i",
        "\u00f3": "o",
        "\u00fa": "u",
        "\u00c1": "A",
        "\u00c9": "E",
        "\u00cd": "I",
        "\u00d3": "O",
        "\u00da": "U",
        "\u00f1": "n",
        "\u00d1": "N"
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


# --- Herramienta: Extraer citas de la web ---
@mcp.tool()
def fetch_web_content(url: str) -> dict:
    try:
        edge_options = EdgeOptions()
        edge_options.add_argument("--start-maximized")
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=edge_options)
        driver.get(url)
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        quotes = []
        for quote_div in soup.find_all("div", class_="quote"):
            text = quote_div.find("span", class_="text").get_text(strip=True)
            author = quote_div.find("small", class_="author").get_text(strip=True)
            tags = [tag.get_text(strip=True) for tag in quote_div.find("div", class_="tags").find_all("a", class_="tag")]
            quotes.append({
                "text": clean_text(text),
                "author": clean_text(author),
                "tags": ", ".join(tags)
            })

        driver.quit()
        return {"status": "ok", "quotes": quotes}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Herramienta: Guardar en CSV ---
@mcp.tool()
def save_to_csv(quotes: list, filename: str = "contenido.csv") -> dict:
    try:
        with open(filename, mode="w", newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Cita", "Autor", "Etiquetas"])
            for quote in quotes:
                writer.writerow([quote["text"], quote["author"], quote["tags"]])
        return {"status": "ok", "message": f"Guardado en {filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Herramienta: Guardar en PDF ---
@mcp.tool()
def save_to_pdf(quotes: list, filename: str = "contenido.pdf") -> dict:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)

        for quote in quotes:
            pdf.multi_cell(0, 10, f"Cita: {quote['text']}")
            pdf.multi_cell(0, 10, f"Autor: {quote['author']}")
            pdf.multi_cell(0, 10, f"Etiquetas: {quote['tags']}\n\n")

        pdf.output(filename)
        return {"status": "ok", "message": f"Guardado en {filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Herramienta: Leer texto del PDF ---
@mcp.tool()
def leer_texto_pdf(ruta_pdf: str) -> dict:
    try:
        with open(ruta_pdf, "rb") as f:
            reader = PdfReader(f)
            texto = ""
            for pagina in reader.pages:
                texto += pagina.extract_text() + "\n"
            return {"status": "ok", "texto": texto[:4000]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Herramienta: Consultar a Gemini ---
@mcp.tool()
def ask_gemini(instruccion: str) -> dict:
    try:
        prompt = f"""
        Eres un asistente claro y conciso.
        Lee el siguiente contenido y dime qué piensas del mismo:

        "{instruccion}"
        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return {"status": "ok", "respuesta": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Prompt principal: Ejecutar flujo completo ---
@mcp.prompt()
def process_quotes(url: str) -> str:
    result_fetch = fetch_web_content(url)
    if result_fetch["status"] != "ok":
        return json.dumps({"error": result_fetch["message"]}, indent=2)

    quotes = result_fetch["quotes"]

    result_csv = save_to_csv(quotes)
    result_pdf = save_to_pdf(quotes)

    result_read = leer_texto_pdf("contenido.pdf")
    if result_read["status"] != "ok":
        gemini_response = "No se pudo extraer el texto del PDF."
    else:
        result_gemini = ask_gemini(result_read["texto"])
        gemini_response = result_gemini.get("respuesta", "Sin respuesta de Gemini.")

    return json.dumps({
        "status": "ok",
        "csv_result": result_csv,
        "pdf_result": result_pdf,
        "gemini_opinion": gemini_response
    }, indent=2)


# --- Iniciar servidor MCP ---
if __name__ == "__main__":
    print("Iniciando servidor MCP...")
    mcp.run(transport='stdio')
