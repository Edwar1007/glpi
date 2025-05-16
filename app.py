import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# 🔐 Configuración del API GLPI
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = os.getenv("API_TOKEN")  # tomado desde las variables de entorno

# 🔹 Mapeo de campos
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

# 🔹 Función para iniciar sesión
def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    if response.status_code == 200:
        return response.json().get("session_token")
    return None

# 🔹 Cerrar sesión
def cerrar_sesion(token):
    headers = {"Session-Token": token}
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

# 🔹 Obtener equipos del inventario
def obtener_inventario(token, rango=300):
    headers = {"Session-Token": token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/search/Computer/?range=0-{rango}&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"
    response = requests.get(url, headers=headers)
    if response.status_code in [200, 206]:
        data = response.json().get("data", [])
        return [{CAMPOS_MAP.get(str(k), str(k)): v for k, v in item.items()} for item in data]
    return []

# 🔹 Buscar equipos por nombre de usuario
def buscar_por_usuario(token, nombre_usuario):
    headers = {"Session-Token": token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/search/Computer?criteria[0][field]=9&criteria[0][searchtype]=contains&criteria[0][value]={nombre_usuario}&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", [])
        return [{CAMPOS_MAP.get(str(k), str(k)): v for k, v in item.items()} for item in data]
    return []

# 🔸 Ruta raíz
@app.route('/')
def home():
    return "API GLPI funcionando correctamente desde Render"

# 🔸 Ruta: /inventario
@app.route('/inventario', methods=['GET'])
def inventario():
    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500
    equipos = obtener_inventario(token)
    cerrar_sesion(token)
    return jsonify({"total": len(equipos), "equipos": equipos})

# 🔸 Ruta: /buscar-por-usuario
@app.route('/buscar-por-usuario', methods=['GET'])
def buscar_usuario():
    nombre_usuario = request.args.get("usuario")
    if not nombre_usuario:
        return jsonify({"error": "Debe proporcionar el parámetro 'usuario'"}), 400

    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    equipos = buscar_por_usuario(token, nombre_usuario)
    cerrar_sesion(token)

    if equipos:
        return jsonify({"total": len(equipos), "equipos": equipos})
    else:
        return jsonify({"mensaje": "No se encontraron equipos asignados a ese usuario."}), 404

# 🔸 Para desarrollo local
if __name__ == '__main__':
    app.run(debug=True)
