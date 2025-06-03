import requests

GLPI_URL = "http://soporteti.sutex.com/glpi/apirest.php"
API_TOKEN = "mkjpcCnyDJzIzC0PgHgDhOK7NT3Z7YMDnD4BEIuO"

def iniciar_sesion():
    headers = {
        "Authorization": f"user_token {API_TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.get(f"{GLPI_URL}/initSession", headers=headers)
    return r.json().get("session_token") if r.status_code == 200 else None

def cerrar_sesion(token):
    requests.get(f"{GLPI_URL}/killSession", headers={"Session-Token": token})

def diagnosticar_campos_equipo():
    token = iniciar_sesion()
    if not token:
        print("No se pudo iniciar sesión.")
        return

    headers = {"Session-Token": token, "Content-Type": "application/json"}

    # Construir URL para pedir todos los campos posibles (hasta 99)
    base_url = f"{GLPI_URL}/search/Computer?range=0-0"
    for i in range(100):
        base_url += f"&forcedisplay[{i}]={i}"

    r = requests.get(base_url, headers=headers)
    cerrar_sesion(token)

    if r.status_code != 200:
        print("Error al consultar los equipos.")
        return

    datos = r.json().get("data", [])
    if not datos:
        print("No se obtuvo ningún equipo.")
        return

    print("Campos del primer equipo encontrados:\n")
    for item in datos:
        for campo_id, valor in item.items():
            print(f"Campo {campo_id}: {valor}")

if __name__ == "__main__":
    diagnosticar_campos_equipo()
