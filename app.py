import os
import requests
from flask import Flask, jsonify, request

# 🔹 Configuración de GLPI
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = "mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO"

# 🔹 Mapeo de campos legibles
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

app = Flask(__name__)

# 🔹 Sesiones GLPI
def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}", "Content-Type": "application/json"}
    r = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    return r.json().get("session_token") if r.status_code == 200 else None

def cerrar_sesion(session_token):
    requests.get(f"{GLPI_URL}/killSession", headers={"Session-Token": session_token})

# 🔹 Ruta raíz
@app.route('/')
def home():
    return jsonify({"mensaje": "API GLPI funcionando correctamente desde Render"})

# 🔹 Ruta con paginación
@app.route('/todos-equipos')
def todos_equipos():
    try:
        inicio = int(request.args.get("inicio", 0))
        cantidad = int(request.args.get("cantidad", 50))
    except ValueError:
        return jsonify({"error": "Parámetros 'inicio' y 'cantidad' deben ser enteros"}), 400

    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión"}), 500

    headers = {"Session-Token": token, "Content-Type": "application/json"}
    url = (
        f"{GLPI_URL}/search/Computer/?range={inicio}-{inicio+cantidad-1}"
        "&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23"
        "&forcedisplay[3]=3&forcedisplay[4]=31&forcedisplay[5]=4"
        "&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6"
        "&forcedisplay[9]=70&forcedisplay[10]=80"
    )
    r = requests.get(url, headers=headers)
    cerrar_sesion(token)

    if r.status_code not in [200, 206]:
        return jsonify({"error": "No se pudo obtener el inventario"}), 500

    datos = r.json().get("data", [])
    equipos = [{CAMPOS_MAP.get(str(k), str(k)): v for k, v in item.items()} for item in datos]

    return jsonify({"equipos": equipos, "total": len(equipos)})

# 🔹 Buscar por usuario (nombre completo flexible)
@app.route('/buscar-por-usuario', methods=['GET'])
def buscar_usuario():
    nombre_completo = request.args.get("usuario", "").strip().lower()
    if not nombre_completo:
        return jsonify({"error": "Debe proporcionar el parámetro 'usuario'"}), 400

    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    headers = {"Session-Token": token, "Content-Type": "application/json"}
    url_usuarios = f"{GLPI_URL}/search/User?range=0-500&forcedisplay[0]=1&forcedisplay[1]=9&forcedisplay[2]=34"
    res_user = requests.get(url_usuarios, headers=headers)

    if res_user.status_code not in [200, 206]:
        cerrar_sesion(token)
        return jsonify({"error": "No se pudo obtener la lista de usuarios"}), 500

    usuarios = res_user.json().get("data", [])
    login = None

    for u in usuarios:
        campos = {i["field"]: i["value"] for i in u.get("items", [])}
        full_name = f"{campos.get(9, '').lower()} {campos.get(34, '').lower()}".strip()

        partes_nombre = nombre_completo.split()
        if all(p in full_name for p in partes_nombre):
            login = campos.get(1)
            break

    if not login:
        cerrar_sesion(token)
        return jsonify({"mensaje": "No se encontró ningún usuario con ese nombre."}), 404

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
        return jsonify({"total": len(equipos), "equipos": equipos}) if equipos else jsonify({"mensaje": "El usuario fue encontrado, pero no tiene equipos asignados."}), 404

    return jsonify({"error": f"La búsqueda por equipos asignados a {nombre_completo} falló debido a un problema al comunicarse con la API correspondiente."}), 500

# 🔹 Ejecutar app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
