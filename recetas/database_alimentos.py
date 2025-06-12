from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Configuración de la conexión a la base de datos
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=3307,
            database='pdfgemini',
            user='root',
            password=''
        )
        print("✅ Conexión a la base de datos exitosa")
        return connection
    except Error as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

# Ruta de prueba
@app.route('/')
def home():
    return "API Flask para guardar datos de PDFs funcionando ✅"

# Endpoint POST para guardar datos
@app.route('/cocina', methods=['POST'])
def guardar_datos():
    data = request.get_json()  # Recibe JSON del cliente

    # Acceder al objeto 'datos' anidado
    datos = data.get('datos')

    if not datos:
        return jsonify({"error": "El campo 'datos' es obligatorio"}), 400

    # Campos esperados dentro del objeto 'datos'
    nombre = datos.get('nombre') or ""
    ingredientes = datos.get('ingredientes') or ""
    preparacion = datos.get('preparacion') or ""
    categoria = datos.get('categoria') or ""

    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO recetas 
                (nombre, ingredientes, preparacion, categoria)
                VALUES (%s, %s, %s, %s)
            """
            values = (nombre, ingredientes, preparacion, categoria)
            print(f"Insertando receta: {nombre}, {ingredientes}, {preparacion}, {categoria}")
            cursor.execute(query, values)
            connection.commit()
            cursor.close()
            connection.close()

            return jsonify({
                "mensaje": "Datos guardados correctamente",
                "datos": datos
            }), 201
        else:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    except Error as e:
        return jsonify({"error": f"No se pudieron guardar los datos: {e}"}), 500

# Iniciar la app
if __name__ == '__main__':
    app.run(debug=True, port=5000)
