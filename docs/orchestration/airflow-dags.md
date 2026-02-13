# DAGs de Apache Airflow

DAGs que orquestan el pipeline de Big Data.

## DAGs disponibles

| DAG | Programación | Propósito |
|-----|--------------|-----------|
| **transport_monitoring_pipeline** | @daily | Pipeline principal (limpieza, enriquecimiento, análisis, reporte) |
| **monthly_model_retraining** | @monthly | Re-entrenamiento modelo grafos |
| **weekly_delay_model_training** | @weekly | Entrenamiento modelo predicción retrasos (ML) |
| **system_maintenance** | @weekly | Limpieza HDFS, checkpoints, logs |
| **data_quality_check** | @daily | Verificación calidad y consistencia Kafka/HDFS/MongoDB |
| **simulation_data_stream** | */15 * * * * | Generación datos GPS simulados (cada 15 min) |
| **executive_reporting** | @weekly | Reportes ejecutivos desde MongoDB |

## Instalación

```bash
mkdir -p ~/airflow/dags
cp orchestration/airflow/dags/*.py ~/airflow/dags/
airflow dags list
```

Activar DAGs desde http://localhost:8080.

## Configuración

- **AIRFLOW_HOME:** por defecto `~/airflow`
- Conexiones por defecto: MongoDB (`mongodb://127.0.0.1:27017/`), HDFS, Spark
- Email: configurar SMTP en `airflow.cfg` para notificaciones

## Referencias

- [AIRFLOW.md](../guides/AIRFLOW.md)
- [INSTALLATION.md](../guides/INSTALLATION.md)
- [USAGE.md](../guides/USAGE.md)
