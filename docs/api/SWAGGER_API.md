# Swagger / OpenAPI y publicación de API REST

Aunque el proyecto no incluye por defecto un servidor REST, los datos en **MongoDB** (vehicle_status, route_delay_aggregates, bottlenecks) son idóneos para exponerlos mediante una **API REST** documentada con **Swagger (OpenAPI)** y publicarla para que frontends, dashboards o terceros consuman los datos sin acceder directamente a la base de datos.

## Objetivo

- **Documentar** la API con **OpenAPI 3** (Swagger) para que cualquier cliente sepa qué endpoints existen, parámetros y esquemas.
- **Publicar** la especificación (Swagger UI o servidor que sirva el JSON/YAML) y, opcionalmente, un **servidor REST** que consulte MongoDB y cumpla esa especificación.

## Probar Swagger con la API incluida

El proyecto incluye una implementación FastAPI en **api/main.py** que cumple la especificación y sirve **Swagger UI** en `/docs`.

1. **Requisitos:** MongoDB en marcha (`127.0.0.1:27017`), venv activado y dependencias instaladas (`pip install -r requirements.txt`).
2. **Arrancar:** Desde la raíz del proyecto, `uvicorn api.main:app --host 0.0.0.0 --port 5000`.
3. **Abrir en el navegador:** http://localhost:5000/docs (Swagger UI) y probar los endpoints.

Ver **api/README.md** para más detalle.

## Especificación OpenAPI incluida

En este repositorio se incluye una especificación OpenAPI 3.0 que describe la API de monitorización de transporte:

| Archivo | Descripción |
|---------|-------------|
| **docs/api/openapi.yaml** | Definición OpenAPI 3: endpoints, parámetros y esquemas (vehicles, delays, bottlenecks, health). |

Endpoints definidos:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /health | Estado del servicio y conexión MongoDB |
| GET | /vehicles | Listar último estado de vehículos (query: route_id, limit) |
| GET | /vehicles/{vehicle_id} | Último estado de un vehículo |
| GET | /delays | Agregados de retrasos (query: route_id, limit) |
| GET | /bottlenecks | Nodos cuello de botella |

Los esquemas (VehicleStatus, DelayAggregate, Bottleneck) están alineados con las colecciones de MongoDB descritas en **docs/api/API.md**.

## Cómo usar la especificación con Swagger

### 1. Ver la API en Swagger UI (sin implementar el servidor)

Puedes visualizar y probar la especificación con **Swagger Editor** o **Swagger UI**:

- **Swagger Editor (online):** https://editor.swagger.io → File → Import file → subir o pegar el contenido de `docs/api/openapi.yaml`.
- **Swagger UI con Docker:**
  ```bash
  docker run -p 8081:8080 -e SWAGGER_JSON=/openapi/openapi.yaml -v $(pwd)/docs/api:/openapi swaggerapi/swagger-ui
  ```
  Luego abrir http://localhost:8081 y asegurarse de que la URL del JSON/YAML apunte a `/openapi/openapi.yaml` (o servir el archivo por HTTP y poner esa URL en la UI).

- **Desde un servidor estático:** Sirve la carpeta `docs/api` (p. ej. con `python -m http.server 8000` en `docs/api`) y en Swagger UI configura la URL `http://localhost:8000/openapi.yaml`.

### 2. Implementar un servidor REST que cumpla la especificación

Dos opciones típicas:

#### Opción A: FastAPI (recomendado)

FastAPI genera **OpenAPI automáticamente** y sirve **Swagger UI** en `/docs` y ReDoc en `/redoc`. Puedes alinear tu implementación con `openapi.yaml` o dejar que FastAPI genere la spec desde el código y luego ajustar.

```bash
pip install fastapi uvicorn pymongo
```

Ejemplo mínimo (guardar como `api/main.py` o similar):

```python
from fastapi import FastAPI, Query, HTTPException
from pymongo import MongoClient

app = FastAPI(title="Transport Monitoring API", version="1.0.0")
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["transport_db"]

@app.get("/health")
def health():
    return {"status": "ok", "mongo": "connected" if client.server_info() else "error"}

@app.get("/vehicles")
def list_vehicles(route_id: str = None, limit: int = Query(20, le=100)):
    q = {} if not route_id else {"route_id": route_id}
    cursor = db.vehicle_status.find(q).sort("timestamp", -1).limit(limit)
    return list(cursor)

@app.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str):
    doc = db.vehicle_status.find_one({"vehicle_id": vehicle_id}, sort=[("timestamp", -1)])
    if not doc: raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return doc

@app.get("/delays")
def list_delays(route_id: str = None, limit: int = Query(50, le=200)):
    q = {} if not route_id else {"route_id": route_id}
    cursor = db.route_delay_aggregates.find(q).sort("window_start", -1).limit(limit)
    return list(cursor)

@app.get("/bottlenecks")
def list_bottlenecks():
    return list(db.bottlenecks.find().sort("degree", -1))
```

Servir:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 5000
```

Swagger UI quedará en **http://localhost:5000/docs** y la spec en **http://localhost:5000/openapi.json**.

#### Opción B: Flask + Flasgger

Flasgger permite definir la API con **YAML/OpenAPI** y exponer Swagger UI desde Flask:

```bash
pip install flask flasgger pymongo
```

En la app Flask se puede cargar `openapi.yaml` y registrar los endpoints según la spec; Flasgger sirve la UI en `/apidocs`. (Documentación: https://github.com/flasgger/flasgger.)

### 3. Publicar la API

- **Entorno local:** Ejecutar el servidor (FastAPI/Flask) y acceder a Swagger UI en `/docs` o `/apidocs`. La especificación se puede exportar desde ahí (OpenAPI JSON/YAML).
- **Publicación en red:** Exponer el servidor en un host/puerto (p. ej. nodo1:5000) y, si aplica, poner un **reverse proxy** (nginx) o un servicio en la nube. Asegurar que MongoDB sea accesible desde el servidor de la API.
- **Solo la documentación:** Publicar únicamente el archivo **openapi.yaml** (p. ej. en un sitio estático o en un repositorio) y usar Swagger Editor/UI para visualizarlo; la implementación del servidor puede ser aparte.

## Resumen

| Qué | Dónde / Cómo |
|-----|----------------|
| Especificación OpenAPI | **docs/api/openapi.yaml** |
| Consultas directas (Hive, MongoDB, Kafka) | **docs/api/API.md** |
| Servidor REST + Swagger UI | Implementar con FastAPI (recomendado) o Flask+Flasgger y consultar MongoDB |
| Publicar solo la doc | Servir openapi.yaml vía Swagger UI (Docker o estático) o desde FastAPI `/openapi.json` |

Así el proyecto queda con **documentación Swagger/OpenAPI** y guía para **publicar** tanto la especificación como una API REST que la implemente.
