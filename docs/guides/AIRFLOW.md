# Apache Airflow: instalación, uso y significado de la interfaz

## Para qué sirve Airflow

**Apache Airflow** es una plataforma de **orquestación de workflows**: programa, ejecuta y supervisa tareas en un orden definido (grafos dirigidos acíclicos, DAGs). En este proyecto sirve para:

- **Automatizar** el pipeline de Big Data (limpieza, enriquecimiento, análisis de retrasos, análisis de grafos, import a MongoDB) en lugar de lanzar cada script a mano.
- **Programar** ejecuciones (diarias, mensuales) y **reintentos** en caso de fallo.
- **Visualizar** el flujo de tareas (grafo del DAG) y el historial de ejecuciones (éxito/fallo).
- **Centralizar** logs y monitoreo en una única interfaz web.

Los DAGs del proyecto (`transport_monitoring_pipeline`, `monthly_model_retraining`) definen qué tareas se ejecutan y en qué orden; el **scheduler** las dispara según la programación y el **executor** (p. ej. SequentialExecutor) las ejecuta.

---

## Instalación completa

### Requisitos

- Python 3.10 o 3.11 (recomendado; 3.12 puede usar constraints de 3.11).
- Entorno virtual del proyecto activado.

### 1. Instalar Airflow

**Opción recomendada (script con constraints):**

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
bash scripts/setup/install_airflow.sh
```

**Opción manual con constraints (Python 3.11):**

```bash
pip install "apache-airflow==2.10.0" "apache-airflow-providers-apache-spark==4.9.0" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.0/constraints-3.11.txt"
```

**Opción simple (sin constraints):** `pip install -r requirements.txt` (incluye `apache-airflow==2.10.0`).

### 2. Inicializar base de datos y crear usuario

```bash
export AIRFLOW_HOME=~/airflow   # opcional si ya está en el entorno
airflow db init
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

(Introduce una contraseña cuando se solicite.)

### 3. Desactivar DAGs de ejemplo (evitar errores de import)

Los DAGs de ejemplo que instala Airflow pueden fallar (p. ej. `tutorial_objectstorage.py` con protocolo S3). Para cargar solo los DAGs del proyecto:

Editar `~/airflow/airflow.cfg` y poner:

```ini
load_examples = False
```

### 4. Copiar los DAGs del proyecto

```bash
mkdir -p ~/airflow/dags
cp /home/hadoop/Documentos/ProyectoBigData/orchestration/airflow/dags/* ~/airflow/dags/
```

### 5. Arrancar webserver y scheduler

**Opción recomendada (script del proyecto):**

```bash
cd /home/hadoop/Documentos/ProyectoBigData
bash scripts/utils/start_airflow.sh
```

**Opción manual:**

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
export AIRFLOW_HOME=~/airflow

airflow scheduler > ~/airflow/logs/scheduler.log 2>&1 &
airflow webserver --port 8080 > ~/airflow/logs/webserver.log 2>&1 &
```

**Importante**: El scheduler debe estar corriendo para que los DAGs se registren en la base de datos y puedas ejecutarlos. El script `start_airflow.sh` ejecuta automáticamente `airflow dags reserialize` para forzar el registro. Si inicias el scheduler manualmente, ejecuta `airflow dags reserialize` después de iniciarlo.

Abrir en el navegador: **http://localhost:8080** (o http://nodo1:8080 si accedes por red). Iniciar sesión con el usuario `admin` y la contraseña creada en el paso 2.

### Detener Airflow

**Opción recomendada (script del proyecto):**

```bash
bash scripts/utils/stop_airflow.sh
```

**Opción manual:**

```bash
pkill -f "airflow scheduler"
pkill -f "airflow webserver"
```

### Verificar que el scheduler está corriendo

```bash
ps aux | grep "airflow scheduler"
```

Si no está corriendo, los DAGs no se registrarán y comandos como `airflow dags trigger` fallarán con `DagNotFound`.

---

## Qué representa la interfaz (página DAGs)

### Lista de DAGs

En **DAGs** se listan los workflows definidos en `~/airflow/dags/`:

| Columna / elemento | Significado |
|--------------------|-------------|
| **Toggle (interruptor)** | Activa o pausa el DAG. Si está pausado (gris), el scheduler no lanzará nuevas ejecuciones. |
| **Tags** | Etiquetas del DAG (p. ej. `big-data`, `transport`, `graphframes`) para filtrar. |
| **Owner** | Usuario o equipo responsable (en el código del DAG). |
| **Schedule** | Frecuencia: `@daily`, `@monthly`, etc. |
| **Last Run / Next Run** | Última ejecución programada y próxima. |

### El “gráfico” de círculos (Recent Tasks)

La columna **Recent Tasks** no es el grafo del DAG (eso se ve entrando en cada DAG y pestaña “Graph”). Es una **línea de tiempo visual** de los **estados recientes de las tareas** de ese DAG:

- **Cada círculo** corresponde a una **tarea** (o a un conjunto de tareas) en ejecuciones recientes.
- **Color:**
  - **Verde:** la tarea terminó correctamente (éxito).
  - **Rojo:** la tarea falló.
  - **Amarillo:** omitida, upstream fallido o en reintento.
  - **Gris:** programada, en cola o en ejecución.
  - **Blanco / sin color:** sin estado aún o limpiado.

Los **números** dentro de algunos círculos indican cuántas tareas (o cuántas veces esa tarea) están en ese estado en el historial mostrado.

En resumen: esa fila de círculos te permite ver de un vistazo si las últimas ejecuciones del DAG están en verde (bien), en gris (en curso) o en rojo/amarillo (hay que revisar).

### Ver el grafo real del DAG

Para ver el **grafo del workflow** (cajas = tareas, flechas = dependencias):

1. Haz clic en el **nombre del DAG** (p. ej. `transport_monitoring_pipeline`).
2. Entra en la pestaña **Graph** (o **Grid** en versiones recientes).
3. Ahí se muestra el DAG como grafo: cada nodo es una tarea y las flechas indican el orden de ejecución.

---

## DAGs incluidos en el proyecto

| DAG | Descripción | Programación |
|-----|-------------|--------------|
| **transport_monitoring_pipeline** | Orquesta tareas del pipeline de transporte (limpieza, enriquecimiento, análisis de retrasos, etc.). | Diaria (@daily) |
| **monthly_model_retraining** | Re-entrenamiento o actualización del modelo de grafos (GraphFrames). | Mensual (@monthly) |
| **weekly_delay_model_training** | Entrenamiento semanal del modelo de predicción de retrasos (IA/ML) usando `route_delay_aggregates`. | Semanal (@weekly) |
| **system_maintenance** | Limpieza de datos antiguos en HDFS, rotación de logs y optimización de almacenamiento. | Semanal (@weekly) |
| **data_quality_check** | Verificación diaria de calidad de datos y consistencia entre Kafka, HDFS y MongoDB. | Diaria (@daily) |
| **simulation_data_stream** | Generación continua de datos GPS simulados para desarrollo/demos. | Cada 15 minutos |
| **executive_reporting** | Generación y envío de reportes ejecutivos semanales con tendencias y métricas. | Semanal (@weekly) |

Definiciones en: `orchestration/airflow/dags/`.

### Detalles de los DAGs adicionales

#### weekly_delay_model_training
- **Propósito**: Entrenar semanalmente el modelo de Machine Learning (`RandomForestRegressor`) para predecir retrasos.
- **Tareas**:
  1. Verificar que existen datos suficientes en MongoDB (`route_delay_aggregates`).
  2. Hacer backup del modelo anterior.
  3. Ejecutar `routing/train_delay_model.py`.
  4. Validar el nuevo modelo comparando precisión (MAE, R²).
  5. Notificar completación.
- **Requisitos**: MongoDB con al menos 50 documentos en `route_delay_aggregates`.

#### system_maintenance
- **Propósito**: Mantenimiento automático del sistema para liberar espacio y optimizar rendimiento.
- **Tareas**:
  1. Limpiar datos raw en HDFS con más de 30 días.
  2. Limpiar checkpoints de Spark con más de 7 días.
  3. Rotar logs de Airflow (mantener últimos 30 días).
  4. Identificar particiones Parquet pequeñas que podrían compactarse.
  5. Generar reporte de espacio liberado.

#### data_quality_check
- **Propósito**: Auditoría automática de calidad de datos para detectar anomalías temprano.
- **Tareas**:
  1. Ejecutar `storage/mongodb/verify_data.py`.
  2. Verificar umbrales (conteos mínimos, retrasos consistentemente en 0%).
  3. Comparar consistencia entre HDFS y MongoDB.
  4. Generar resumen de calidad.
- **Alertas**: Detecta colecciones vacías, desincronizaciones y posibles fallos en cálculos.

#### simulation_data_stream
- **Propósito**: Mantener el flujo de datos vivo automáticamente para desarrollo y demos.
- **Tareas**:
  1. Generar datos GPS simulados cada 15 minutos usando `scripts/utils/generate_sample_data.py`.
- **Nota**: Este DAG está pensado para entornos de desarrollo; desactívalo en producción si no es necesario.

#### executive_reporting
- **Propósito**: Generar reportes ejecutivos semanales con tendencias y métricas consolidadas.
- **Tareas**:
  1. Consultar tendencias semanales desde MongoDB (agregados por ruta, bottlenecks).
  2. Generar informe HTML con tablas y métricas.
  3. Enviar reporte por email (requiere configuración SMTP en Airflow).
- **Salida**: Archivo HTML en `/tmp/transport_report_YYYYMMDD.html`.

---

## Solución de problemas comunes

### Error: "Dag id X not found in DagModel"
**Causa**: El scheduler no está corriendo o no ha procesado los DAGs aún.
**Solución**: 
1. Iniciar el scheduler: `bash scripts/utils/start_airflow.sh`
2. Esperar 10-15 segundos para que procese los DAGs
3. Verificar: `airflow dags list`

### Error: "Could not import graphviz"
**Causa**: Falta el paquete Python `graphviz` para visualización de grafos.
**Solución**: `pip install graphviz` (ya incluido en `requirements.txt`)

### Los DAGs aparecen en `dags list` pero no se pueden ejecutar
**Causa**: El scheduler no está corriendo o los DAGs están pausados.
**Solución**: 
1. Verificar que el scheduler esté corriendo: `ps aux | grep "airflow scheduler"`
2. Activar los DAGs: `airflow dags unpause <dag_id>`

## Referencias

- Instalación de componentes: **docs/guides/INSTALLATION.md** (sección Airflow).
- Uso general del pipeline: **docs/guides/USAGE.md**.
- Solución de problemas: **docs/guides/TROUBLESHOOTING.md** (Airflow).
