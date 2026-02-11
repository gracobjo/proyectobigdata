# API REST Transport Monitoring (Swagger)

API de lectura sobre MongoDB para probar **Swagger UI**. Documentación en **docs/api/SWAGGER_API.md** y especificación en **docs/api/openapi.yaml**.

## Probar Swagger

1. **Requisitos:** MongoDB en marcha en `127.0.0.1:27017` con datos (vehicle_status, route_delay_aggregates, bottlenecks). Dependencias: `pip install fastapi uvicorn pymongo` (o `pip install -r requirements.txt`).

2. **Arrancar la API** (desde la raíz del proyecto):
   ```bash
   source venv/bin/activate
   uvicorn api.main:app --host 0.0.0.0 --port 5000
   ```

3. **Abrir Swagger UI:** http://localhost:5000/docs  
   - Probar los endpoints (health, vehicles, delays, bottlenecks) desde el navegador.

4. **OpenAPI JSON:** http://localhost:5000/openapi.json
