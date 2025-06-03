from flask import Flask, request, jsonify
import requests
import unicodedata

app = Flask(__name__)

GLPI_URL = 'http://soporteti.sutex.com/glpi/apirest.php'
API_TOKEN = 'mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO'

# Mapeo de campos para mostrar en la respuesta
CAMPOS_MAP = {
    '1': 'Nombre',
    '2': 'ID',
    '3': 'Tipo',
    '4': 'Modelo',
    '5': 'Número de serie',
    '6': 'Propietario',
    '19': 'Fecha de creación',
    '23': 'Fecha de modificación',
    '31': 'Ubicación',
    '40': 'Estado',
    '70': 'Estado de inventario',
    '80': 'Ubicación'
}

def normalizar(texto):
    """
    Normaliza un texto eliminando acentos y convirtiendo a minúsculas.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def iniciar_sesion():
    """
    Inicia una sesión en GLPI y devuelve el token de sesión.
    """
    headers = {
        'Content-Type': 'application/json',
        'App-Token': API_TOKEN
    }
    response = requests.get(f'{GLPI_URL}/initSession', headers=headers)
    if response.status_code == 200:
        return response.json().get('session_token')
    return None

def cerrar_sesion(token):
    """
    Cierra la sesión en GLPI.
    """
    headers = {
        'Content-Type': 'application/json',
        'App-Token': API_TOKEN,
        'Session-Token': token
    }
    requests.get(f'{GLPI_URL}/killSession', headers=headers)

@app.route('/buscar-por-usuario', methods=['GET'])
def buscar_usuario():
    nombre_completo = request.args.get("usuario", "").strip()
    if not nombre_completo:
        return jsonify({"error": "Debe proporcionar el parámetro 'usuario'"}), 400

    nombre_normalizado = normalizar(nombre_completo)

    token = iniciar_sesion()
    if not token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 500

    headers = {
        'Content-Type': 'application/json',
        'App-Token': API_TOKEN,
        'Session-Token': token
    }

    # Buscar usuarios en GLPI
    url_usuarios = f"{GLPI_URL}/search/User?range=0-500&forcedisplay[0]=1&forcedisplay[1]=9&forcedisplay[2]=34"
    res_user = requests.get(url_usuarios, headers=headers)

    if res_user.status_code not in [200, 206]:
        cerrar_sesion(token)
        return jsonify({"error": "No se pudo obtener la lista de usuarios"}), 500

    usuarios = res_user.json().get("data", [])
    login = None

    for u in usuarios:
        campos = {i["field"]: i["value"] for i in u.get("items", [])}
        full_name = f"{campos.get('9', '')} {campos.get('34', '')}"
        full_name_norm = normalizar(full_name)

        partes = nombre_normalizado.split()
        if all(p in full_name_norm for p in partes):
            login = campos.get('1')
            break

    if not login:
        cerrar_sesion(token)
        return jsonify({"mensaje": "No se encontró ningún usuario con ese nombre."}), 404

    # Buscar equipos por login en el campo Propietario (campo 6)
    url_equipos = (
        f"{GLPI_URL}/search/Computer?"
        f"criteria[0][field]=6&criteria[0][searchtype]=contains&criteria[0][value]={login}"
        f"&forcedisplay[0]=1&forcedisplay[1]=19&forcedisplay[2]=23&forcedisplay[3]=3&forcedisplay[4]=31"
        f"&forcedisplay[5]=4&forcedisplay[6]=40&forcedisplay[7]=5&forcedisplay[8]=6&forcedisplay[9]=70&forcedisplay[10]=80"
    )
    res_eq = requests.get(url_equipos, headers=headers)
    cerrar_sesion(token)

    if res_eq.status_code == 200:
        data = res_eq.json().get("data", [])
        equipos = [
            {CAMPOS_MAP.get(str(k), str(k)): v for k, v in item.items()}
            for item in data
        ]
        if equipos:
            return jsonify({"total": len(equipos), "equipos": equipos}), 200
        else:
            return jsonify({"mensaje": "El usuario fue encontrado, pero no tiene equipos asignados."}), 404

    return jsonify({"error": f"La búsqueda por equipos asignados a {nombre_completo} falló debido a un problema al comunicarse con la API correspondiente."}), 500

if __name__ == '__main__':
    app.run(debug=True)
