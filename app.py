import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# 🔐 Configuración
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = os.getenv("API_TOKEN")  # Desde variable de entorno en Render

# 🔹 Campos legibles
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

# 🔹 Autenticación
def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}", "Content-Type": "application/json"}
    r = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    return r.json().get("session_token") if r.status_code == 200 else None

def cerrar_sesion(token):
    headers = {"Session-Token": token}
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

# 🔹 Página raíz
@app.route('/')
def home():
    return "API GLPI funcionando correctamente desde Render"

# 🔹 Buscar por usuario (realname o firstname)
@app.route('/buscar-por-usuario', methods=['GET'])
def buscar_usuario():
    nombre_usuario = request.args.get("usuario", "").strip()
    if not nombre_usuario:
        return jsonify({"error": "Debe proporcionar el parámetro 'usuario'"}), 400

    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    headers = {"Session-Token": token, "Content-Type": "application/json"}

    # 🧠 Separar las palabras del nombre ingresado
    palabras = nombre_usuario.lower().split()

    # 🔍 Construir criterios dinámicos para buscar usuario
    criteria = ""
    for i, palabra in enumerate(palabras):
        criteria += f"criteria[{i * 2}][field]=9&criteria[{i * 2}][searchtype]=contains&criteria[{i * 2}][value]={palabra}&"
        criteria += f"criteria[{i * 2}][link]=OR&"
        criteria += f"criteria[{i * 2 + 1}][field]=34&criteria[{i * 2 + 1}][searchtype]=contains&criteria[{i * 2 + 1}][value]={palabra}&"
        if i < len(palabras) - 1:
            criteria += f"criteria[{i * 2 + 1}][link]=AND&"

    url_usuario = f"{GLPI_URL}/search/User?{criteria}range=0-10"
    res_user = requests.get(url_usuario, headers=headers)

    if res_user.status_code != 200 or not res_user.json().get("data"):
        cerrar_sesion(token)
        return jsonify({"mensaje": "No se encontró ningún usuario con ese nombre."}), 404

    # ✅ Obtener login del primer usuario encontrado
    user_data = res_user.json()["data"][0].get("items", [])
    login = ""
    for campo in user_data:
        if campo.get("field") == 1:
            login = campo.get("value")
            break

    if not login:
        cerrar_sesion(token)
        return jsonify({"error": "No se pudo extraer el nombre de usuario (login)"}), 500

    # 🔁 Buscar equipos asignados usando el login como valor del campo 9
    url_equipos = (
        f"{GLPI_URL}/search/Computer?"
        f"criteria[0][field]=9&criteria[0][searchtype]=contains&criteria[0][value]={login}"
        f"&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&forcedisplay[4]=31"
        f"&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"
    )
    res_eq = requests.get(url_equipos, headers=headers)
    cerrar_sesion(token)

    if res_eq.status_code == 200:
        data = res_eq.json().get("data", [])
        equipos = [{CAMPOS_MAP.get(str(k), str(k)): v for k, v in item.items()} for item in data]
        if equipos:
            return jsonify({"total": len(equipos), "equipos": equipos})
        else:
            return jsonify({"mensaje": "El usuario fue encontrado, pero no tiene equipos asignados."}), 404

    return jsonify({"error": "Error al comunicarse con GLPI"}), 500
# 🔎 Diagnóstico: ver cómo están guardados los usuarios
@app.route('/usuarios-debug', methods=['GET'])
def usuarios_debug():
    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión"}), 500

    headers = {"Session-Token": token, "Content-Type": "application/json"}
    
    url = f"{GLPI_URL}/search/User?range=0-50"
    res = requests.get(url, headers=headers)
    cerrar_sesion(token)

    if res.status_code in [200, 206]:
        try:
            datos = res.json()
            return jsonify({"usuarios_raw": datos})
        except Exception as e:
            return jsonify({"error": "No se pudo interpretar la respuesta", "detalle": str(e)}), 500
    else:
        return jsonify({"error": "No se pudo obtener la lista de usuarios", "codigo": res.status_code}), 500
# 🔸 Ejecutar localmente
if __name__ == '__main__':
    app.run(debug=True)
