import requests
from flask import Flask, jsonify, request

# 🔹 Configuración de GLPI
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = "mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO"

# 🔹 Mapeo de números de campo a nombres entendibles
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

# 🔹 Iniciar sesión en GLPI
def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    if response.status_code == 200:
        return response.json().get("session_token", None)
    return None

# 🔹 Cerrar sesión en GLPI
def cerrar_sesion(session_token):
    headers = {"Session-Token": session_token}
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

# 🔹 Obtener inventario con rango dinámico
def obtener_inventario(session_token, rango):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/search/Computer/?range=0-{rango}&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"

    response = requests.get(url, headers=headers)
    if response.status_code in [200, 206]:
        datos = response.json()
        equipos = datos.get("data", [])
        equipos_formateados = [{CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()} for equipo in equipos]
        return equipos_formateados
    return None

# 🔹 Obtener un solo equipo por ID
def obtener_equipo_por_id(session_token, equipo_id):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/Computer/{equipo_id}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        equipo = response.json()
        equipo_formateado = {CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()}
        return equipo_formateado
    return None

# 🔹 Buscar equipos por nombre de usuario
def buscar_por_usuario(session_token, nombre_usuario):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/search/Computer?criteria[0][field]=9&criteria[0][searchtype]=contains&criteria[0][value]={nombre_usuario}&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        datos = response.json()
        equipos = datos.get("data", [])
        equipos_formateados = [{CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()} for equipo in equipos]
        return equipos_formateados
    return None

# 🔹 Crear API con Flask
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"mensaje": "API de GLPI funcionando correctamente"}), 200

@app.route('/inventario', methods=['GET'])
def obtener_datos():
    print("📌 Se recibió una solicitud en /inventario")
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    rango = request.args.get("rango", default=180, type=int)
    print(f"📌 Consultando {rango} equipos en GLPI...")

    inventario = obtener_inventario(session_token, rango)
    cerrar_sesion(session_token)

    if inventario:
        return jsonify({"total_equipos": len(inventario), "equipos": inventario})
    return jsonify({"error": "No se encontraron equipos"}), 404

@app.route('/todos-equipos', methods=['GET'])
def todos_equipos():
    return obtener_datos()

@app.route('/inventario/<equipo_id>', methods=['GET'])
def obtener_equipo(equipo_id):
    print(f"📌 Se recibió una solicitud en /inventario/{equipo_id}")
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    equipo = obtener_equipo_por_id(session_token, equipo_id)
    cerrar_sesion(session_token)

    if equipo:
        return jsonify({"equipo": equipo})
    return jsonify({"error": f"No se encontró el equipo con ID {equipo_id}"}), 404

@app.route('/buscar-por-usuario', methods=['GET'])
def buscar_usuario():
    nombre_usuario = request.args.get("usuario")
    if not nombre_usuario:
        return jsonify({"error": "Debe proporcionar el parámetro 'usuario'"}), 400

    print(f"📌 Buscando equipos asignados a: {nombre_usuario}")
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    equipos = buscar_por_usuario(session_token, nombre_usuario)
    cerrar_sesion(session_token)

    if equipos:
        return jsonify({"total_encontrado": len(equipos), "equipos": equipos})
    return jsonify({"mensaje": "No se encontraron equipos asignados a ese usuario."}), 404

# 🔹 Iniciar el servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
