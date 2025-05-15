from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# 🔹 CONFIGURAR DATOS DE GLPI 🔹
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php/"  # Reemplaza con tu URL de GLPI
API_TOKEN = "2qyjeCL5QTjhILHiHySmom746wIRrNOW9CJfnVUp"  # 🔴 Usa el token de usuario normal aquí

# 🔹 INICIO DE SESIÓN EN GLPI 🔹
def iniciar_sesion():
    headers = {"Authorization": f"user_token {API_TOKEN}"}
    response = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    
    if response.status_code == 200:
        return response.json().get("session_token")
    else:
        return None

@app.route('/inventario', methods=['GET'])
def obtener_inventario():
    session_token = iniciar_sesion()
    if not session_token:
        return jsonify({"error": "No se pudo iniciar sesión en GLPI"}), 401
    
    headers = {
        "Session-Token": session_token,
        "Authorization": f"user_token {API_TOKEN}"
    }
    
    response = requests.get(f"{GLPI_URL}/Computer", headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())  # Retorna el inventario en formato JSON
    else:
        return jsonify({"error": "No se pudo obtener el inventario"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
