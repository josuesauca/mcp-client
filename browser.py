
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time

# Opciones del navegador (puedes dejarlo vacío si quieres que se vea la ventana)
options = Options()
# options.add_argument("--headless")  # Quita este comentario si NO quieres ver el navegador

# Inicializa el navegador Edge
driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)

# Muestra que se abre el navegador
print("Abriendo navegador...")

# Abre la URL
url = "https://www.ejemplo.com"
driver.get(url)
print(f"Ingresando a {url}...")

# Espera unos segundos para que puedas ver la interacción
time.sleep(5)

# Cierra el navegador
driver.quit()
print("Navegador cerrado.")
