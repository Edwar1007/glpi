import os
import unicodedata
import requests
import time
from flask import Flask, jsonify, request

GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = "mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO"

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

def obtener_equipo_por_id(session_token, equipo_id):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/Computer/{equipo_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        equipo = response.json()
        equipo_formateado = {CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()}
        return equipo_formateado
    return None

def buscar_por_usuario_iterativo(nombre_usuario):
    equipos_usuario = []
    cantidad = 100
    total_recorridos = 0

    while total_recorridos < 400:
        session_token = iniciar_sesion()
        if not session_token:
            break

        rango_glpi = f"{total_recorridos}-{total_recorridos + cantidad - 1}"
        headers = {"Session-Token": session_token, "Content-Type": "application/json"}
        url = f"{GLPI_URL}/search/Computer/?range={rango_glpi}&" + \
              "forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&" + \
              "forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&" + \
              "forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"

        response = requests.get(url, headers=headers)
        cerrar_sesion(session_token)

        if response.status_code not in [200, 206]:
            break

        datos = response.json()
        equipos = datos.get("data", [])
        if not equipos:
            break

        for equipo in equipos:
            campos = {CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()}
            if str(campos.get("Ubicación_Interna", "")).lower() == nombre_usuario.lower():
                equipos_usuario.append(campos)

        total_recorridos += cantidad

    return equipos_usuario

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"mensaje": "API de GLPI funcionando correctamente"}), 200

@app.route('/inventario/<equipo_id>', methods=['GET'])
def obtener_equipo(equipo_id):
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
    print(f"🔍 Buscando equipos asignados a: {nombre_usuario}")
    equipos = buscar_por_usuario_iterativo(nombre_usuario)
    if equipos:
        return jsonify({"total_encontrado": len(equipos), "equipos": equipos})
    return jsonify({"mensaje": "No se encontraron equipos asignados a ese usuario."}), 404

@app.route('/todos-equipos', methods=['GET'])
def alias_todos_equipos():
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    inicio = request.args.get("inicio", default=0, type=int)
    cantidad = request.args.get("cantidad", default=100, type=int)
    rango_glpi = f"{inicio}-{inicio + cantidad - 1}"

    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    url = f"{GLPI_URL}/search/Computer/?range={rango_glpi}&" + \
          "forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&" + \
          "forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&" + \
          "forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"

    response = requests.get(url, headers=headers)
    cerrar_sesion(session_token)

    if response.status_code in [200, 206]:
        datos = response.json()
        equipos = datos.get("data", [])
        equipos_formateados = [{CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()} for equipo in equipos]
        return jsonify({
            "equipos": equipos_formateados,
            "total": len(equipos_formateados)
        })

    return jsonify({"error": "No se encontraron equipos"}), 404

@app.route('/todos-equipos-todo', methods=['GET'])
def obtener_todo_el_inventario():
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    equipos_totales = []
    cantidad = 100
    inicio = 0

    while True:
        rango_glpi = f"{inicio}-{inicio + cantidad - 1}"
        headers = {"Session-Token": session_token, "Content-Type": "application/json"}
        url = f"{GLPI_URL}/search/Computer/?range={rango_glpi}&" + \
              "forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&" + \
              "forcedisplay[4]=31&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&" + \
              "forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"

        response = requests.get(url, headers=headers)
        if response.status_code not in [200, 206]:
            break

        datos = response.json()
        equipos = datos.get("data", [])
        if not equipos:
            break

        equipos_formateados = [{CAMPOS_MAP.get(str(k), f"Campo_{k}"): v for k, v in equipo.items()} for equipo in equipos]
        equipos_totales.extend(equipos_formateados)
        inicio += cantidad

    cerrar_sesion(session_token)
    return jsonify({"equipos": equipos_totales, "total": len(equipos_totales)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
