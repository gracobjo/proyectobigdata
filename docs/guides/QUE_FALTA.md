# Qué más puede faltar en el proyecto

Resumen de elementos opcionales o complementarios que el proyecto podría incorporar. No son obligatorios para el pipeline actual, pero mejoran la entrega o la operación.

## Documentación y API

| Elemento | Estado | Referencia |
|----------|--------|------------|
| **API REST + Swagger/OpenAPI** | Documentación y especificación incluidas; servidor no implementado por defecto | **docs/api/SWAGGER_API.md**, **docs/api/openapi.yaml** |
| Consultas Hive, MongoDB, Kafka | Documentado | **docs/api/API.md** |

Para exponer los datos (MongoDB) como API REST y publicar la documentación con Swagger, seguir **docs/api/SWAGGER_API.md** (especificación OpenAPI en `openapi.yaml`, opciones FastAPI o Flask+Flasgger, y publicación).

## Infraestructura y operación

| Elemento | Descripción |
|----------|-------------|
| **CI/CD** | Pipeline de integración/despliegue (GitHub Actions, Jenkins) para tests, build o despliegue en un entorno de pruebas. |
| **Contenedores** | Docker Compose o Dockerfiles para Kafka, MongoDB, NiFi, HDFS (opcional) para reproducir el entorno. |
| **Tests E2E** | Pruebas de extremo a extremo (generar datos → limpieza → MongoDB → verificación) automatizadas. |
| **Monitoreo** | Prometheus/Grafana o integración con Airflow para métricas del pipeline. |

## Datos y modelos

| Elemento | Estado | Descripción |
|----------|--------|-------------|
| **Más fuentes en NiFi** | Pendiente | Integrar más APIs o fuentes además de OpenWeather/FlightRadar24 y logs GPS. |
| **IA y mejora de rutas** | ✅ Implementado | Cuándo introducir IA y cómo mejorar rutas (con/sin ML): **docs/guides/IA_RUTAS.md**. |
| **Modelo de ML** | ✅ Implementado | Modelo de predicción de retrasos (entrenado con delay_aggregates); Airflow tiene DAGs de re-entrenamiento mensual (`monthly_model_retraining`) y semanal (`weekly_delay_model_training`). |
| **Alertas automáticas** | Pendiente | Reglas (p. ej. delay_percentage > umbral) y notificaciones (email, Slack) desde los agregados en MongoDB o desde la API. |
| **DAGs adicionales de Airflow** | ✅ Implementado | DAGs de mantenimiento (`system_maintenance`), calidad de datos (`data_quality_check`), generación continua (`simulation_data_stream`) y reportes ejecutivos (`executive_reporting`). Ver **docs/guides/AIRFLOW.md**. |

## Seguridad y producción

| Elemento | Descripción |
|----------|-------------|
| **Autenticación API** | Si se publica la API REST: API keys, JWT o OAuth según **SWAGGER_API.md**. |
| **Secrets** | Variables de entorno o gestor de secretos para API keys (OpenWeather, etc.) y conexiones. |
| **PostgreSQL/MySQL para Airflow** | Sustituir SQLite por BD externa para el metadata de Airflow en entornos compartidos o producción. |

## Resumen

- **Swagger y publicación de API:** cubierto con **docs/api/SWAGGER_API.md** y **docs/api/openapi.yaml**.
- El resto son mejoras opcionales (CI/CD, Docker, tests E2E, monitoreo, más fuentes NiFi, ML, alertas, seguridad). Se pueden priorizar según el alcance del proyecto o la asignatura.
