# Ejecutar el pipeline (modo standalone)

Orden recomendado tras tener HDFS y Kafka en marcha.

## 0. Dependencias Python (para generate_sample_data.py)

En sistemas con Python “externally managed” (PEP 668) no se puede usar `pip install` a nivel sistema. Usa un **entorno virtual** en el proyecto:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
bash scripts/setup/setup_venv.sh
```

Luego ejecuta los scripts Python con el intérprete del venv:

```bash
# Opción A: activar el venv y usar python
source venv/bin/activate
python scripts/utils/generate_sample_data.py

# Opción B: sin activar
venv/bin/python scripts/utils/generate_sample_data.py
```

## 1. Comprobar servicios

```bash
jps   # Debe haber NameNode, DataNode, Kafka (y opcional SecondaryNameNode)
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
# Debe listar: raw-data, filtered-data, alerts
```

## 2. Crear directorios en HDFS

```bash
cd /home/hadoop/Documentos/ProyectoBigData
bash scripts/setup/setup_hdfs_dirs.sh
```

## 3. Crear tablas maestras (Spark)

El script ya fuerza `spark.driver.host=127.0.0.1` y desactiva la Spark UI para evitar errores de bind cuando `nodo1` resuelve a 192.168.56.1.

```bash
spark-submit --master "local[*]" scripts/setup/create_tables_spark.py
```

Comprueba: `hdfs dfs -ls /user/hive/warehouse/`

## 4. Generar datos de prueba (Kafka)

```bash
# Usar el Python del venv (tras haber ejecutado setup_venv.sh)
venv/bin/python scripts/utils/generate_sample_data.py
# o: source venv/bin/activate && python scripts/utils/generate_sample_data.py
```

Opcional: reducir mensajes editando `NUM_MESSAGES` en el script (por defecto 1000).

## 5. Pipeline de procesamiento

### 5.1 Limpieza (streaming: raw-data → filtered-data)

Si cambias configuración de particiones (p. ej. `spark.sql.shuffle.partitions`) y quieres que se aplique, borra el checkpoint y reinicia una vez:  
`hdfs dfs -rm -r /user/hadoop/checkpoints/cleaning`

En una terminal, deja corriendo:

```bash
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/sql/data_cleaning.py
```

### 5.2 Enriquecimiento (streaming: filtered-data → HDFS)

Asegúrate de haber ejecutado antes `create_tables_spark.py` (tablas maestras en HDFS) y `setup_hdfs_dirs.sh`. En otra terminal (con el job de limpieza ya escribiendo en `filtered-data`):

```bash
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/sql/data_enrichment.py
```

### 5.3 Análisis de grafos (batch, una sola ejecución)

**Requisitos:** En el venv del proyecto instalar GraphFrames (Python) y setuptools:
```bash
source venv/bin/activate
pip install graphframes-py setuptools
```

Ejecutar (usar el Python del venv para que encuentre el módulo graphframes):
```bash
cd /home/hadoop/Documentos/ProyectoBigData
PYSPARK_PYTHON=./venv/bin/python spark-submit --master "local[*]" \
  --packages io.graphframes:graphframes-spark3_2.12:0.10.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/graphframes/network_analysis.py
```

Resultados en HDFS: `.../user/hive/warehouse/network_pagerank`, `network_degrees`, `network_bottlenecks`.

### 5.4 Análisis de retrasos (streaming)

Lee de `filtered-data` (datos limpios; no requiere enriquecimiento). Calcula agregados por ventana de 15 min (total_vehicles, avg_speed, delay_percentage con is_delayed = speed < 10) y escribe en HDFS y en el topic `alerts`. Checkpoints: `delay_hive`, `delay_kafka`.

```bash
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/streaming/delay_analysis.py
```

Salidas: `hdfs://.../user/hive/warehouse/delay_aggregates/` (Parquet por route_id), topic Kafka `alerts`, y consola.

## 6. Comprobar resultados

```bash
# HDFS
hdfs dfs -ls /user/hadoop/processed/enriched
hdfs dfs -ls /user/hive/warehouse/
hdfs dfs -ls /user/hive/warehouse/delay_aggregates/

# Kafka (consumir mensajes)
# raw-data o filtered-data:
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic raw-data --from-beginning --max-messages 5 --timeout-ms 10000
# topic alerts (agregados de retrasos, JSON por ventana y ruta):
venv/bin/python scripts/utils/kafka_consume_one.py alerts
# o: kafka-console-consumer.sh ... --topic alerts --from-beginning --max-messages 10 --timeout-ms 15000
```

## Notas

- **YARN**: Si usas `--master yarn`, asegúrate de que ResourceManager y NodeManager estén activos y que `spark.driver.host=127.0.0.1` esté configurado.
- **Hive**: Los scripts están adaptados para standalone sin Hive; las tablas maestras y resultados usan rutas HDFS directas (Parquet).
- **Topic alerts**: Si el topic se llama `delay-alerts`, créalo con `create_topics.sh` o cambia en `delay_analysis.py` la opción `topic` a `delay-alerts`.
