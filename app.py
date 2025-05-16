{
  "openapi": "3.1.0",
  "info": {
    "title": "Inventario GLPI",
    "version": "1.0.0",
    "description": "API pública para consultar inventario y buscar equipos por usuario desde GLPI."
  },
  "servers": [
    {
      "url": "https://glpi-jntn.onrender.com"
    }
  ],
  "paths": {
    "/inventario": {
      "get": {
        "operationId": "obtenerInventario",
        "summary": "Obtener el inventario completo de equipos",
        "responses": {
          "200": {
            "description": "Inventario consultado correctamente",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "equipos": {
                      "type": "array",
                      "items": {
                        "type": "object"
                      }
                    },
                    "total": {
                      "type": "integer"
                    }
                  }
                }
              }
            }
          },
          "500": {
            "description": "Error al iniciar sesión en GLPI"
          }
        }
      }
    },
    "/buscar-por-usuario": {
      "get": {
        "operationId": "buscarPorUsuario",
        "summary": "Buscar equipos asignados a un usuario",
        "parameters": [
          {
            "name": "usuario",
            "in": "query",
            "required": true,
            "description": "Nombre completo del usuario",
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Equipos encontrados"
          },
          "404": {
            "description": "Usuario no encontrado o sin equipos"
          },
          "500": {
            "description": "Error al comunicarse con GLPI"
          }
        }
      }
    }
  }
}
