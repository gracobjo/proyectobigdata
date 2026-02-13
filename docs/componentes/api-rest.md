# API REST Transport Monitoring (Swagger)

API de lectura sobre MongoDB con Swagger UI. Especificación: [SWAGGER_API.md](../api/SWAGGER_API.md).

## Probar

1. MongoDB en marcha en `127.0.0.1:27017`. Dependencias: `pip install fastapi uvicorn pymongo`.
2. Arrancar: `uvicorn api.main:app --host 0.0.0.0 --port 5000` (desde la raíz, con venv activado).
3. Swagger UI: http://localhost:5000/docs
4. OpenAPI: http://localhost:5000/openapi.json
