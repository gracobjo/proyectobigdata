# DAGs de Apache Airflow

Este directorio contiene todos los DAGs (Directed Acyclic Graphs) que orquestan el pipeline de Big Data del proyecto.

## DAGs Disponibles

### 1. transport_monitoring_pipeline
- **Programación**: `@daily` (diaria)
- **Propósito**: Pipeline principal de monitorización de transporte
- **Tareas**:
  - Verificación de servicios (Hadoop, Kafka, NiFi)
  - Limpieza de datos (Spark SQL)
  - Enriquecimiento de datos
  - Análisis de red con GraphFrames
  - Análisis de retrasos (streaming)
  - Limpieza de tablas temporales
  - Generación de reporte diario

### 2. monthly_model_retraining
- **Programación**: `@monthly` (mensual)
- **Propósito**: Re-entrenamiento del modelo de análisis de grafos
- **Tareas**:
  - Backup del modelo actual
  - Re-entrenamiento con GraphFrames
  - Validación del nuevo modelo
  - Notificación de completación

### 3. weekly_delay_model_training
- **Programación**: `@weekly` (semanal, cada lunes)
- **Propósito**: Entrenamiento del modelo de predicción de retrasos (IA/ML)
- **Tareas**:
  - Verificar datos en MongoDB (`route_delay_aggregates`)
  - Backup del modelo anterior
  - Entrenar modelo (`routing/train_delay_model.py`)
  - Validar modelo (MAE, R²)
  - Notificar completación
- **Requisitos**: MongoDB con al menos 50 documentos en `route_delay_aggregates`

### 4. system_maintenance
- **Programación**: `@weekly` (semanal)
- **Propósito**: Mantenimiento y limpieza del sistema
- **Tareas**:
  - Limpiar datos raw en HDFS (>30 días)
  - Limpiar checkpoints de Spark (>7 días)
  - Rotar logs de Airflow (mantener últimos 30 días)
  - Identificar particiones Parquet pequeñas para optimización
  - Reporte de espacio liberado

### 5. data_quality_check
- **Programación**: `@daily` (diaria)
- **Propósito**: Verificación de calidad de datos y consistencia
- **Tareas**:
  - Ejecutar verificación MongoDB (`storage/mongodb/verify_data.py`)
  - Verificar umbrales (conteos mínimos, retrasos consistentemente en 0%)
  - Comparar consistencia HDFS vs MongoDB
  - Generar resumen de calidad
- **Alertas**: Detecta colecciones vacías, desincronizaciones y posibles fallos

### 6. simulation_data_stream
- **Programación**: `*/15 * * * *` (cada 15 minutos)
- **Propósito**: Generación continua de datos GPS simulados para desarrollo/demos
- **Tareas**:
  - Generar datos de prueba (`scripts/utils/generate_sample_data.py`)
- **Nota**: Desactivar en producción si no es necesario

### 7. executive_reporting
- **Programación**: `@weekly` (semanal)
- **Propósito**: Generación de reportes ejecutivos semanales
- **Tareas**:
  - Consultar tendencias semanales desde MongoDB
  - Generar informe HTML con métricas y tablas
  - Enviar reporte por email (requiere configuración SMTP)
- **Salida**: `/tmp/transport_report_YYYYMMDD.html`

## Instalación

1. Copiar los DAGs al directorio de Airflow:
```bash
mkdir -p ~/airflow/dags
cp orchestration/airflow/dags/*.py ~/airflow/dags/
```

2. Verificar que Airflow detecta los DAGs:
```bash
airflow dags list
```

3. Activar los DAGs desde la interfaz web (http://localhost:8080)

## Configuración

- **AIRFLOW_HOME**: Por defecto `~/airflow` (configurable en `airflow.cfg`)
- **Conexiones**: Los DAGs asumen conexiones por defecto a MongoDB (`mongodb://127.0.0.1:27017/`), HDFS y Spark
- **Email**: Para notificaciones por email, configurar SMTP en `airflow.cfg` o usar `EmailOperator` con conexión SMTP

## Referencias

- Documentación completa: **docs/guides/AIRFLOW.md**
- Guía de instalación: **docs/guides/INSTALLATION.md**
- Uso general: **docs/guides/USAGE.md**
