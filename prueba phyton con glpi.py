import requests

# 🔹 Configuración
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php/"  # Reemplaza con la URL de tu GLPI
API_TOKEN = "mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO"  # Inserta tu API Token generado en GLPI

# 🔹 Iniciar sesión y obtener un token de sesión
def iniciar_sesion():
    headers = {
        "Authorization": f"user_token {API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    
    if response.status_code == 200:
        return response.json()["session_token"]
    else:
        print(f"❌ Error iniciando sesión: {response.status_code} - {response.text}")
        return None

# 🔹 Obtener la lista de computadoras usando getAllItems
def obtener_inventario(session_token):
    headers = {
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }
    url = f"{GLPI_URL}/getAllItems/Computer"  # Usamos getAllItems para obtener todos los equipos
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Devuelve los equipos en formato JSON
    else:
        print(f"❌ Error al obtener inventario: {response.status_code} - {response.text}")
        return None

# 🔹 Cerrar sesión en la API
def cerrar_sesion(session_token):
    headers = {
        "Session-Token": session_token
    }
    requests.get(f"{GLPI_URL}/killSession", headers=headers)

# 🔹 Ejecutar consulta
if __name__ == "__main__":
    session_token = iniciar_sesion()
    if session_token:
        inventario = obtener_inventario(session_token)
        cerrar_sesion(session_token)  # Cerrar sesión después de la consulta

        if inventario:
            print("✅ Inventario obtenido correctamente:")
            for equipo in inventario:
                print(f"ID: {equipo['id']} - Nombre: {equipo.get('name', 'Sin nombre')}")
        else:
            print("⚠️ No se encontraron equipos en el inventario.")
