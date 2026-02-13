# Persistencia MongoDB

Scripts para escribir datos del pipeline en MongoDB.

## Colecciones

- **route_delay_aggregates**: desde topic `alerts`
- **vehicle_status**: desde `filtered-data`
- **bottlenecks**: importados con `import_bottlenecks.py`

Verificación: `python storage/mongodb/verify_data.py`. Detalle: [VERIFICACION_MONGODB_CARACTERISTICAS.md](../guides/VERIFICACION_MONGODB_CARACTERISTICAS.md).

## Scripts

- **kafka_to_mongodb_alerts.py** — alerts → route_delay_aggregates
- **kafka_to_mongodb_vehicle_status.py** — filtered-data → vehicle_status
- **import_bottlenecks.py** — HDFS Parquet → MongoDB
- **verify_data.py** — comprobar conteos

Ver [RUN_PIPELINE.md](../guides/RUN_PIPELINE.md) para orden de ejecución.
