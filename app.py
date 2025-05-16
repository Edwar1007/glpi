import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = os.getenv("API_TOKEN")

CAMPOS_MAP = {
    "1": "ID",
    "19": "Fecha_Asignación",
    "23": "Marca",
    "3": "Ubicación",
    "31": "Estado",
    "4": "Tipo_Dispositivo",
    "40": "Modelo",
    "5": "Serial",
    "6": "Propietario",
    "70": "Ubicación_Interna",
    "80": "Entidad"
}

def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    if response.status_code == 200:
        return response.json().get("session_token")
    return None

def cerrar_sesion(token):
    headers = {"Session-Token": token}
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

@app.route('/')
def home():
    return "API GLPI funcionando correctamente desde Render"

@app.route('/buscar-por-usuario', methods=['GET'])
def buscar_usuario():
    nombre_usuario = request.args.get("usuario")
    if not nombre_usuario:
        return jsonify({"error": "Debe proporcionar el parámetro 'usuario'"}), 400

    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    headers = {"Session-Token": token, "Content-Type": "application/json"}

    # Diagnóstico: búsqueda en realname y firstname
    url_usuario = (
        f"{GLPI_URL}/search/User?"
        f"criteria[0][field]=9&criteria[0][searchtype]=contains&criteria[0][value]={nombre_usuario}"
        f"&criteria[0][link]=OR"
        f"&criteria[1][field]=34&criteria[1][searchtype]=contains&criteria[1][value]={nombre_usuario}"
    )

    res_user = requests.get(url_usuario, headers=headers)

    print("🔍 Resultado crudo del usuario:", res_user.text)

    cerrar_sesion(token)

    try:
        data = res_user.json()
        return jsonify({
            "mensaje": "Resultado de búsqueda crudo",
            "nombre_buscado": nombre_usuario,
            "respuesta_glpi": data
        })
    except Exception as e:
        return jsonify({"error": "No se pudo interpretar la respuesta del servidor", "detalle": str(e)}), 500

# Ejecutar localmente si es necesario
if __name__ == '__main__':
    app.run(debug=True)

    
