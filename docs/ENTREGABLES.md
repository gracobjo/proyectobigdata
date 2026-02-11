# Entregables del Proyecto Big Data

## Resultados obtenidos y forma de reproducirlos

Esta sección describe los **resultados concretos** del pipeline en modo standalone (un solo nodo) y los **pasos exactos** para llegar a ellos. Sirve como evidencia ejecutable y guía de verificación.

### Requisitos previos

- **Servicios activos:** HDFS (NameNode + al menos 1 DataNode), Kafka (KRaft), en `localhost` / `127.0.0.1`.
- **Directorios HDFS:** Ejecutar `bash scripts/setup/setup_hdfs_dirs.sh`.
- **Entorno Python:** `bash scripts/setup/setup_venv.sh` y, para análisis de grafos, `pip install graphframes-py setuptools` en el venv.

Verificación rápida:
```bash
jps   # NameNode, DataNode, Kafka
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092   # raw-data, filtered-data, alerts
hdfs dfs -ls /user/hadoop/
```

---

### R1. Tablas maestras (HDFS)

**Resultado:** Parquet en HDFS con rutas y vehículos de referencia.

| Recurso | Ubicación HDFS |
|--------|-----------------|
| Rutas  | `hdfs://localhost:9000/user/hive/warehouse/master_routes/` |
| Vehículos | `hdfs://localhost:9000/user/hive/warehouse/master_vehicles/` |

**Cómo reproducir:**
```bash
cd /home/hadoop/Documentos/ProyectoBigData
spark-submit --master "local[*]" --conf spark.driver.host=127.0.0.1 scripts/setup/create_tables_spark.py
```
Si `master_vehicles` queda vacío o falla por tipo DATE, ejecutar además:
```bash
spark-submit --master "local[*]" --conf spark.driver.host=127.0.0.1 scripts/setup/fix_master_vehicles.py
```

**Comprobar:**
```bash
hdfs dfs -ls /user/hive/warehouse/master_routes/
hdfs dfs -ls /user/hive/warehouse/master_vehicles/
```

---

### R2. Datos de prueba en Kafka (raw-data)

**Resultado:** Mensajes JSON (GPS simulados) en el topic `raw-data`.

**Cómo reproducir:**
```bash
source venv/bin/activate
python scripts/utils/generate_sample_data.py 100
# o: venv/bin/python scripts/utils/generate_sample_data.py 100
```

**Comprobar:** Consumer Python o que el siguiente paso (limpieza) consuma mensajes.

---

### R3. Limpieza de datos (raw-data → filtered-data)

**Resultado:** 
- Lectura desde Kafka `raw-data`, limpieza (normalización, nulos, duplicados, rangos) y escritura en Kafka `filtered-data`.
- Checkpoint en HDFS para recuperación del streaming.

| Recurso | Ubicación |
|--------|-----------|
| Salida Kafka | topic `filtered-data` |
| Checkpoint | `hdfs://localhost:9000/user/hadoop/checkpoints/cleaning` |

**Cómo reproducir:** En una terminal, dejar corriendo:
```bash
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/sql/data_cleaning.py
```
Opcional: para procesar desde el inicio del topic, borrar checkpoint y usar `startingOffsets: earliest` (por defecto en el script).

**Comprobar:** En los logs del job, batches con `numInputRows` > 0 y `numOutputRows` > 0; o consumir desde `filtered-data`.

---

### R4. Enriquecimiento (filtered-data → HDFS)

**Resultado:** Datos enriquecidos con tablas maestras (rutas, vehículos) y campo `is_delayed`, escritos en HDFS particionados por `route_id` y `partition_date`.

| Recurso | Ubicación HDFS |
|--------|-----------------|
| Datos enriquecidos | `hdfs://localhost:9000/user/hadoop/processed/enriched/` |
| Checkpoint | `hdfs://localhost:9000/user/hadoop/checkpoints/enrichment` |

Estructura de particiones: `.../enriched/route_id=R001/partition_date=YYYY-MM-DD/` (Parquet Snappy).

**Cómo reproducir:** Con el job de limpieza escribiendo en `filtered-data`, en otra terminal:
```bash
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/sql/data_enrichment.py
```

**Comprobar:**
```bash
hdfs dfs -ls -R /user/hadoop/processed/enriched/
# Debe verse route_id=R001..R007 y partition_date=...
```

---

### R5. Análisis de grafos (batch)

**Resultado:** Grafos de red de transporte (almacenes y rutas), con PageRank, grados y cuellos de botella, persistidos en HDFS.

| Recurso | Ubicación HDFS |
|--------|-----------------|
| PageRank | `hdfs://localhost:9000/user/hive/warehouse/network_pagerank` |
| Grados | `hdfs://localhost:9000/user/hive/warehouse/network_degrees` |
| Cuellos de botella | `hdfs://localhost:9000/user/hive/warehouse/network_bottlenecks` |

**Cómo reproducir:** En el venv con `graphframes-py` y `setuptools` instalados:
```bash
cd /home/hadoop/Documentos/ProyectoBigData
PYSPARK_PYTHON=./venv/bin/python spark-submit --master "local[*]" \
  --packages io.graphframes:graphframes-spark3_2.12:0.10.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/graphframes/network_analysis.py
```

**Comprobar:**
```bash
hdfs dfs -ls /user/hive/warehouse/network_pagerank
hdfs dfs -ls /user/hive/warehouse/network_degrees
hdfs dfs -ls /user/hive/warehouse/network_bottlenecks
```

---

### R5b. Análisis de retrasos (streaming)

**Resultado:** Agregados por ventana de 15 minutos (total_vehicles, avg_speed, delay_percentage, etc.) en HDFS y en el topic Kafka `alerts`. Lee de `filtered-data` (datos limpios); `is_delayed` se calcula heurísticamente (speed < 10).

| Recurso | Ubicación |
|--------|-----------|
| Agregados Parquet | `hdfs://localhost:9000/user/hive/warehouse/delay_aggregates/` (particionado por route_id) |
| Alertas | Kafka topic `alerts` |
| Checkpoints | `delay_hive`, `delay_kafka` en `/user/hadoop/checkpoints/` |

**Cómo reproducir:** Con datos llegando a `filtered-data` (p. ej. limpieza en marcha), en otra terminal:
```bash
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/streaming/delay_analysis.py
```

**Comprobar:**
```bash
hdfs dfs -ls /user/hive/warehouse/delay_aggregates/
# Ver mensajes del topic alerts (un mensaje):
venv/bin/python scripts/utils/kafka_consume_one.py alerts
# O varios con Kafka CLI:
# /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic alerts --from-beginning --max-messages 10 --timeout-ms 15000
```

---

### R5c. Persistencia MongoDB (opcional)

**Resultado:** Datos del pipeline escritos en MongoDB para consultas de baja latencia. Tres colecciones: `route_delay_aggregates` (agregados de retrasos), `vehicle_status` (estado de vehículos), `bottlenecks` (cuellos de botella).

| Recurso | Ubicación |
|--------|-----------|
| Agregados de retrasos | MongoDB: `transport_db.route_delay_aggregates` |
| Estado de vehículos | MongoDB: `transport_db.vehicle_status` |
| Bottlenecks | MongoDB: `transport_db.bottlenecks` |

**Requisitos:** MongoDB ejecutándose en `127.0.0.1:27017` y `pymongo` instalado en el venv.

**Cómo reproducir:**

1. **Instalar pymongo** (si no está):
   ```bash
   source venv/bin/activate
   pip install pymongo
   ```

2. **Consumir alerts → MongoDB** (en una terminal, con `delay_analysis.py` escribiendo en `alerts`):
   ```bash
   python storage/mongodb/kafka_to_mongodb_alerts.py
   ```

3. **Consumir filtered-data → MongoDB** (opcional, en otra terminal):
   ```bash
   python storage/mongodb/kafka_to_mongodb_vehicle_status.py
   ```

4. **Importar bottlenecks desde HDFS** (una vez, tras ejecutar análisis de grafos):
   ```bash
   spark-submit --master "local[*]" --conf spark.driver.host=127.0.0.1 storage/mongodb/import_bottlenecks.py
   ```

**Comprobar:**
```bash
# Conectar a MongoDB
mongosh "mongodb://127.0.0.1:27017/transport_db"

# Consultar agregados
db.route_delay_aggregates.find().sort({ window_start: -1 }).limit(5)

# Consultar vehículos
db.vehicle_status.find({ vehicle_id: "V001" }).sort({ timestamp: -1 }).limit(1)

# Consultar bottlenecks
db.bottlenecks.find().sort({ degree: -1 })
```

Ver más consultas y detalles en: **storage/mongodb/README.md**.

**Formato de los mensajes en el topic `alerts`:** cada mensaje es un JSON con una fila de agregados por ventana de 15 minutos y ruta. Campos:

| Campo | Tipo | Significado |
|-------|------|-------------|
| `window_start` | ISO 8601 | Inicio de la ventana de 15 min. |
| `window_end` | ISO 8601 | Fin de la ventana. |
| `route_id` | string | Identificador de la ruta (ej. R001, R004). |
| `total_vehicles` | int | Número de registros (vehículos) en esa ventana y ruta. |
| `avg_speed` | double | Velocidad media (km/h) en la ventana. |
| `delayed_count` | int | Vehículos considerados en retraso (velocidad &lt; 10 km/h). |
| `delay_percentage` | double | Porcentaje en retraso: (delayed_count / total_vehicles) × 100. |
| `max_speed`, `min_speed` | double | Velocidad máxima y mínima en la ventana. |
| `analysis_timestamp` | ISO 8601 | Momento en que Spark escribió el agregado. |

**Ejemplo de mensaje:**
```json
{"window_start":"2026-02-11T00:00:00.000+01:00","window_end":"2026-02-11T00:15:00.000+01:00","route_id":"R004","total_vehicles":22,"avg_speed":18.39,"delayed_count":17,"delay_percentage":77.27,"max_speed":90.49,"min_speed":0.0,"analysis_timestamp":"2026-02-11T01:43:36.089+01:00"}
```
Interpretación: en la ventana 00:00–00:15, ruta R004, 22 registros; 17 con velocidad &lt; 10 km/h (77,27 % en retraso); velocidad media 18,39 km/h. Estos mensajes pueden consumirse desde dashboards, microservicios o MongoDB para alertas o reporting en tiempo real.

---

### R6. Resumen de flujo y documentos de referencia

| Fase | Entrada | Salida / Resultado | Guía detallada |
|------|---------|--------------------|----------------|
| Tablas maestras | — | HDFS: master_routes, master_vehicles | `scripts/setup/create_tables_spark.py`, `fix_master_vehicles.py` |
| Datos de prueba | — | Kafka: raw-data | `scripts/utils/generate_sample_data.py` |
| Limpieza | Kafka raw-data | Kafka filtered-data + checkpoint | `processing/spark/sql/data_cleaning.py` |
| Enriquecimiento | Kafka filtered-data + HDFS master_* | HDFS processed/enriched | `processing/spark/sql/data_enrichment.py` |
| Análisis de grafos | Grafo en memoria (almacenes/rutas) | HDFS network_pagerank, _degrees, _bottlenecks | `processing/spark/graphframes/network_analysis.py` |
| Análisis de retrasos | Kafka filtered-data | HDFS delay_aggregates + Kafka alerts | `processing/spark/streaming/delay_analysis.py` |
| Persistencia MongoDB | Kafka alerts + filtered-data + HDFS bottlenecks | MongoDB: route_delay_aggregates, vehicle_status, bottlenecks | `storage/mongodb/kafka_to_mongodb_*.py`, `import_bottlenecks.py` |

Orden recomendado de ejecución y más detalle: **docs/guides/RUN_PIPELINE.md**.  
Solución de problemas (HDFS, Kafka, Spark): **docs/guides/TROUBLESHOOTING.md** y **docs/guides/CURRENT_STATUS.md**.

---

## Lista de Entregables por Categoría

### 1. ARQUITECTURA DE INGESTA (NiFi + Kafka)

#### 1.1 Configuración de Apache NiFi
- **Archivo**: `ingestion/nifi/README.md`
- **Descripción**: Documentación de flujos de ingesta
- **Contenido**:
  - Configuración para consumir APIs públicas (OpenWeather, FlightRadar24)
  - Procesamiento de logs GPS simulados
  - Manejo de back-pressure y errores
  - Almacenamiento raw en HDFS

#### 1.2 Configuración de Apache Kafka
- **Archivo**: `config/kafka/server.properties`
- **Descripción**: Configuración de Kafka en modo KRaft para cluster distribuido
- **Script**: `ingestion/kafka/create_topics.sh`
- **Funcionalidad**:
  - Creación automática de topics: `raw-data`, `filtered-data`, `alerts`
  - Configuración de particiones y replicación
  - Integración con nodo1 del cluster

#### 1.3 Integración NiFi-Kafka-HDFS
- **Evidencia**: Flujo completo documentado que demuestra:
  - Ingesta desde fuentes externas → Kafka → HDFS (raw)
  - Separación de datos crudos y filtrados en topics diferentes
  - Persistencia para auditoría

---

### 2. PROCESAMIENTO SPARK (Fase II y III)

#### 2.1 Limpieza de Datos (Spark SQL)
- **Archivo**: `processing/spark/sql/data_cleaning.py`
- **Funcionalidades**:
  - Normalización de formatos
  - Gestión de nulos y valores inválidos
  - Eliminación de duplicados
  - Validación de rangos (coordenadas, velocidad)
  - Escritura a Kafka topic `filtered-data`

#### 2.2 Enriquecimiento de Datos
- **Archivo**: `processing/spark/sql/data_enrichment.py`
- **Funcionalidades**:
  - Cruce de streaming de Kafka con datos maestros (Parquet en HDFS)
  - Tablas maestras en HDFS: `master_routes`, `master_vehicles` (creadas con `create_tables_spark.py` / `fix_master_vehicles.py`)
  - Cálculo de campos derivados (is_delayed, partition_date)
  - Escritura a HDFS particionado por `route_id` y `partition_date` (`/user/hadoop/processed/enriched/`)

#### 2.3 Análisis de Grafos (GraphFrames)
- **Archivo**: `processing/spark/graphframes/network_analysis.py`
- **Funcionalidades**:
  - Modelado de red de transporte (nodos: almacenes, aristas: rutas)
  - Cálculo de grados de nodos
  - PageRank para identificar nodos críticos
  - Detección de triángulos y motifs
  - Identificación de cuellos de botella
  - Persistencia en HDFS (`network_pagerank`, `network_degrees`, `network_bottlenecks` en `/user/hive/warehouse/`)

#### 2.4 Análisis de Retrasos en Tiempo Real (Structured Streaming)
- **Archivo**: `processing/spark/streaming/delay_analysis.py`
- **Funcionalidades**:
  - Ventanas de tiempo de 15 minutos
  - Cálculo de medias de retrasos por ruta
  - Agregaciones (total_vehicles, avg_speed, delay_percentage)
  - Carga multicapa:
    - Hive: Datos agregados históricos
    - Kafka: Publicación para servicios externos (MongoDB)

---

### 3. PERSISTENCIA MULTICAPA

#### 3.1 Apache Hive / HDFS (SQL - Reporting Histórico)
- **Modo standalone:** Los datos se escriben en HDFS (Parquet) en rutas de warehouse; no se requiere Hive metastore. Las mismas rutas pueden usarse con Hive cuando esté configurado.
- **Archivos**:
  - `config/hive/hive-site.xml`: Configuración del metastore (si se usa Hive)
  - `storage/hive/daily_report.sql`: Scripts de reportes
  - `data/master/sample_master_data.sql`: Datos maestros de ejemplo
- **Tablas/datos en HDFS** (creados por Spark en standalone):
  - `master_routes`, `master_vehicles`: En `/user/hive/warehouse/`
  - `network_pagerank`, `network_degrees`, `network_bottlenecks`: Resultados de análisis de grafos en `/user/hive/warehouse/`
  - `delay_aggregates`: Agregados de retrasos (cuando se ejecuta delay_analysis)

#### 3.2 MongoDB (NoSQL - Consultas de Baja Latencia)
- **Archivo**: `storage/cassandra/schema.cql` (diseño lógico MongoDB)
- **Colecciones diseñadas**:
  - `vehicle_status`: Último estado conocido de cada vehículo
  - `route_delay_aggregates`: Agregados recientes de retrasos
  - `bottlenecks`: Cuellos de botella detectados
- **Índices**: Optimizados para consultas por vehicle_id, route_id, status

#### 3.3 HDFS (Almacenamiento Raw)
- **Estructura**:
  - `/user/hadoop/raw`: Datos sin procesar para auditoría
  - `/user/hadoop/processed/enriched`: Datos enriquecidos
  - `/user/hadoop/checkpoints`: Checkpoints de streaming
  - `/user/hive/warehouse`: Warehouse de Hive

---

### 4. ORQUESTACIÓN (Apache Airflow)

#### 4.1 DAG Principal del Pipeline
- **Archivo**: `orchestration/airflow/dags/transport_monitoring_dag.py`
- **Funcionalidades**:
  - Coordinación de todas las fases del pipeline
  - Verificación de servicios
  - Ejecución de limpieza, enriquecimiento, análisis de grafos y retrasos
  - Limpieza de tablas temporales
  - Generación de reportes diarios
  - Manejo de errores con reintentos (3 intentos, delay de 5 minutos)
  - Notificaciones por email en caso de fallos

#### 4.2 DAG de Re-entrenamiento Mensual
- **Archivo**: `orchestration/airflow/dags/monthly_model_retraining.py`
- **Funcionalidades**:
  - Backup del modelo actual antes de re-entrenar
  - Re-entrenamiento del modelo de grafos
  - Validación del nuevo modelo
  - Notificación de completación
  - Ejecución mensual automática

---

### 5. CONFIGURACIÓN DEL CLUSTER

#### 5.1 Archivos de Configuración
- **HDFS**: Configurado para cluster distribuido (nodo1: NameNode, nodo2: DataNode)
- **YARN**: ResourceManager en nodo1, NodeManager en nodo2
- **Kafka**: Broker y Controller en nodo1, accesible desde ambos nodos
- **Spark**: Configurado para usar YARN y HDFS del cluster
- **Hive**: Metastore apuntando a nodo1
- **MongoDB**: Configurado para ejecutarse en nodo1

#### 5.2 Scripts de Configuración y Verificación
- **Archivo**: `scripts/setup/configure_cluster.sh`
  - Verificación de conectividad entre nodos
  - Creación de directorios en HDFS
  - Verificación de servicios activos
- **Archivo**: `scripts/setup/verify_installation.sh`
  - Verificación de instalación de todos los componentes
  - Validación de variables de entorno

#### 5.3 Configuración Centralizada
- **Archivo**: `config/cluster.properties`
  - Variables centralizadas para configuración del cluster
  - URLs y hosts configurados para nodo1/nodo2

---

### 6. DOCUMENTACIÓN TÉCNICA

#### 6.1 Documentación Principal
- **README.md**: Visión general del proyecto, stack tecnológico, estructura
- **docs/architecture/ARCHITECTURE.md**: 
  - Diagrama de arquitectura completo
  - Descripción de componentes
  - Flujo de datos
  - Escalabilidad y seguridad

#### 6.2 Guías de Usuario
- **docs/architecture/CLUSTER_SETUP.md**: Configuración del cluster distribuido
- **docs/guides/INSTALLATION.md**: Instalación paso a paso de todos los componentes
- **docs/guides/CONFIGURATION.md**: Configuración detallada de cada servicio
- **docs/guides/USAGE.md**: 
  - Inicio del sistema
  - Ejecución de cada fase
  - Monitoreo y troubleshooting

#### 6.3 Documentación de API
- **docs/api/API.md**: 
  - Ejemplos de consultas Hive
  - Ejemplos de consultas MongoDB
  - Uso de topics Kafka
  - Schemas de datos

#### 6.4 Justificación del Ciclo KDD
La documentación demuestra cómo el proyecto implementa cada fase:
- **Selección**: NiFi + Kafka (Fase I)
- **Preprocesamiento**: Spark SQL - Limpieza (Fase II)
- **Transformación**: Enriquecimiento + GraphFrames (Fase II)
- **Minería**: Structured Streaming + Agregaciones (Fase III)
- **Interpretación**: Reportes Hive + MongoDB para consultas (Fase III)

---

### 7. SCRIPTS Y UTILIDADES

#### 7.1 Generación de Datos de Prueba
- **Archivo**: `scripts/utils/generate_sample_data.py`
- **Funcionalidad**: Genera datos GPS simulados para testing

#### 7.2 Scripts de Configuración
- `ingestion/kafka/create_topics.sh`: Creación automática de topics
- `scripts/setup/configure_cluster.sh`: Configuración del cluster
- `scripts/setup/verify_installation.sh`: Verificación de instalación

---

## Resumen de Entregables por Rúbrica

### Arquitectura de Ingesta (Excelente)
✅ NiFi y Kafka integrados con back-pressure y manejo de errores  
✅ Configuración para cluster distribuido  
✅ Separación de datos crudos y filtrados  
✅ Persistencia raw en HDFS

### Procesamiento Spark (Excelente)
✅ Uso avanzado de GraphFrames, SQL y Streaming  
✅ Optimización de joins y particionado  
✅ Análisis de grafos completo (PageRank, grados, triángulos)  
✅ Structured Streaming con ventanas de tiempo

### Persistencia (Excelente)
✅ Uso correcto de MongoDB (NoSQL) y Hive (SQL) según caso de uso  
✅ Diseño de esquemas optimizado  
✅ Carga multicapa implementada

### Orquestación Airflow (Excelente)
✅ DAGs complejos con reintentos, alertas y dependencias claras  
✅ Coordinación de workflows completos  
✅ Re-entrenamiento mensual automatizado

### Documentación (Excelente)
✅ Detalla cada etapa del KDD  
✅ Diagramas de flujo y arquitectura  
✅ Justificación técnica de decisiones  
✅ Guías completas de instalación, configuración y uso

---

## Estructura de Entrega Recomendada

```
ProyectoBigData/
├── README.md                          # Documento principal
├── docs/
│   ├── ENTREGABLES.md                # Este documento
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   └── CLUSTER_SETUP.md
│   ├── guides/
│   │   ├── INSTALLATION.md
│   │   ├── CONFIGURATION.md
│   │   └── USAGE.md
│   └── api/
│       └── API.md
├── ingestion/                         # Fase I
├── processing/                        # Fase II y III
├── storage/                           # Persistencia
├── orchestration/                     # Fase IV
├── config/                            # Configuraciones
└── scripts/                           # Utilidades
```

---

## Notas para la Evaluación

- Todos los scripts están documentados con docstrings
- Las configuraciones están adaptadas para cluster distribuido (nodo1/nodo2); en **modo standalone** se usan `127.0.0.1`/`localhost` en Kafka, HDFS y Spark para evitar problemas de resolución de nombres
- El proyecto sigue el ciclo KDD completo
- La arquitectura Lambda/Kappa está implementada
- Se utiliza el stack Apache 2026 especificado
- MongoDB reemplaza a Cassandra según requisitos del usuario
- **Evidencia reproducible:** La sección «Resultados obtenidos y forma de reproducirlos» (al inicio de este documento) describe cada resultado (R1–R5), su ubicación en HDFS/Kafka y los comandos exactos para reproducirlos; la guía detallada de orden de ejecución está en `docs/guides/RUN_PIPELINE.md`
