import requests

# Configuración de la API de GLPI
GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php/"  # Cambia esto por la URL de tu GLPI
API_TOKEN = "0zlERIbYUdCuztwsQVSgybWQi47ZXc2DlxdQ28ks"  # Reemplaza con tu token

# Encabezados de la solicitud
headers = {
    "Authorization": f"user_token {API_TOKEN}",
    "Content-Type": "application/json"
}

# Intentar iniciar sesión en la API de GLPI
response = requests.get(f"{GLPI_URL}/initSession", headers=headers)

if response.status_code == 200:
    print("✅ Conexión exitosa a GLPI")
else:
    print(f"❌ Error al conectar: {response.status_code} - {response.text}")
