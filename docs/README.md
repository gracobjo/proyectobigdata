# Documentación del proyecto BigData

Índice de la documentación agrupada en **docs/**.

## Inicio rápido

- [GETTING_STARTED.md](GETTING_STARTED.md) — Por dónde empezar y fases del proyecto
- [ENTREGABLES.md](ENTREGABLES.md) — Resultados y entregables

## Ingesta

- [ingestion/nifi-configuracion.md](ingestion/nifi-configuracion.md) — Configuración NiFi y flujos GPS importables
- [ingestion/nifi-montar-flujo-manual.md](ingestion/nifi-montar-flujo-manual.md) — Montar el flujo NiFi a mano si falla la importación
- [guides/NIFI_FLUJOS.md](guides/NIFI_FLUJOS.md) — Procesadores, propiedades y conexiones NiFi/Kafka

## Datos

- [datos/gps-logs.md](datos/gps-logs.md) — Dataset de logs GPS (formato, generación)
- [guides/FUENTES_DATOS.md](guides/FUENTES_DATOS.md) — Fuentes de datos del proyecto

## Almacenamiento

- [storage/mongodb-persistencia.md](storage/mongodb-persistencia.md) — Persistencia en MongoDB (scripts, colecciones)
- [storage/cassandra-diseno-mongodb.md](storage/cassandra-diseno-mongodb.md) — Diseño lógico (MongoDB; carpeta cassandra)

## Componentes

- [componentes/api-rest.md](componentes/api-rest.md) — API REST y Swagger
- [componentes/recomendador-rutas.md](componentes/recomendador-rutas.md) — Recomendación de rutas (grafo, ML)
- [componentes/visualizacion-grafo.md](componentes/visualizacion-grafo.md) — Visualización del grafo (Streamlit)

## Scripts y operación

- [scripts/stack-arranque-pila.md](scripts/stack-arranque-pila.md) — Arrancar/parar la pila (HDFS, YARN, Kafka, NiFi, Airflow)
- [scripts/run-pipeline.md](scripts/run-pipeline.md) — Orden de ejecución del pipeline (run/)

## Docker y despliegue (pruebas)

- [docker/README.md](../docker/README.md) — Docker: stack completo, perfil ligero (Railway), **Vercel** (solo API), S3 y AWS
- [despliegue-colab-jupyter.md](despliegue-colab-jupyter.md) — **Colab, Jupyter, Binder, Kaggle**: alojar y probar el proyecto (notebooks, API con MongoDB Atlas)

## Orquestación

- [orchestration/airflow-dags.md](orchestration/airflow-dags.md) — DAGs de Airflow

## Arquitectura y configuración

- [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- [architecture/CLUSTER_SETUP.md](architecture/CLUSTER_SETUP.md)
- [guides/CONFIGURATION.md](guides/CONFIGURATION.md)
- [guides/INSTALLATION.md](guides/INSTALLATION.md)
- [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)

## Guías adicionales (guides/)

- AIRFLOW.md, USAGE.md, RUN_PIPELINE.md, START_PIPELINE.md
- ENRIQUECIMIENTO_DATOS.md, IA_RUTAS.md, HIVE_Y_ESTRUCTURA_PROYECTO.md
- VERIFICACION_MONGODB_CARACTERISTICAS.md, EXPLICACION_SCRIPTS.md
- Y el resto en [guides/](guides/)

## API

- [api/API.md](api/API.md) — Descripción de la API
- [api/SWAGGER_API.md](api/SWAGGER_API.md) — Swagger y OpenAPI
- [api/openapi.yaml](api/openapi.yaml) — Especificación OpenAPI
