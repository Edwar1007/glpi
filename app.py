from flask import Flask, jsonify, request
import os
import requests

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
        return response.json().get("session_token", None)
    return None

def cerrar_sesion(session_token):
    headers = {"Session-Token": session_token}
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

def obtener_inventario(session_token):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    equipos_totales = []
    inicio = 0
    paso = 100
    while True:
        url = (
            f"{GLPI_URL}/search/Computer/?range={inicio}-{inicio + paso - 1}"
            "&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3"
            "&forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5"
            "&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"
        )
        response = requests.get(url, headers=headers)
        if response.status_code not in [200, 206]:
            break
        data = response.json().get("data", [])
        if not data:
            break
        equipos_formateados = [
            {CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()}
            for equipo in data
        ]
        equipos_totales.extend(equipos_formateados)
        if len(data) < paso:
            break
        inicio += paso
    return equipos_totales

@app.route("/")
def home():
    return "API GLPI funcionando correctamente desde Render"

@app.route("/inventario")
def ruta_inventario():
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión"}), 500
    inventario = obtener_inventario(session_token)
    cerrar_sesion(session_token)
    if inventario:
        return jsonify({"total": len(inventario), "equipos": inventario})
    return jsonify({"mensaje": "No se encontraron equipos"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
