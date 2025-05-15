import requests
from flask import Flask, jsonify, request

# 🔹 Configuración de GLPI
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"  # Cambia esto a la URL de tu GLPI
API_TOKEN = "mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO"  # Reemplázalo con tu API Token

# 🔹 Iniciar sesión en GLPI
def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    if response.status_code == 200:
        return response.json().get("session_token", None)
    return None

# 🔹 Obtener el inventario de computadoras
def obtener_inventario(session_token):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/search/Computer/?range=0-50"
    response = requests.get(url, headers=headers)

    if response.status_code in [200, 206]:
        datos = response.json()
        return datos.get("data", [])  # Devuelve solo la lista de computadoras
    return None

# 🔹 Cerrar sesión en GLPI
def cerrar_sesion(session_token):
    headers = {"Session-Token": session_token}
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

# 🔹 Crear la API con Flask
app = Flask(__name__)

@app.route('/inventario', methods=['GET'])
def obtener_datos():
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    inventario = obtener_inventario(session_token)
    cerrar_sesion(session_token)

    if inventario:
        return jsonify({"total_equipos": len(inventario), "equipos": inventario})
    return jsonify({"error": "No se encontraron equipos"}), 404

# 🔹 Iniciar el servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

