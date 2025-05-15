import requests

API_URL = "https://deeaf613-6495-4d6d-a676-7b2bf2493cd2-00-1y3b24fskjgmr.spock.replit.dev/inventario"

response = requests.get(API_URL)

if response.status_code == 200:
    datos = response.json()
    print(f"✅ Hay un total de {datos.get('total_equipos', 0)} equipos en el inventario.")
else:
    print(f"❌ Error al obtener datos: {response.status_code} - {response.text}")
