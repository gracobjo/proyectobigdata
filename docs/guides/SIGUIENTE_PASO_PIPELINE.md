# Siguiente Paso en el Pipeline

## Estado actual (ya ejecutado)

| Paso | Script | Estado |
|------|--------|--------|
| 0 | 00_start_hdfs.sh | HDFS activo |
| 1 | 01_generate_data.sh | Datos en raw-data |
| 2 | 02_data_cleaning.sh | filtered-data |
| 3 | 03_delay_analysis.sh | alerts + HDFS delay_aggregates |
| 4 | 04_mongodb_consumer.sh | route_delay_aggregates en MongoDB |
| 5 | 05_verify_mongodb.sh | Verificación |

## Siguientes pasos posibles

### Opción A: Enriquecimiento de datos (recomendado siguiente)

**Qué hace:** Cruza los datos limpios (filtered-data) con las tablas maestras (rutas, vehículos) en HDFS y escribe datos enriquecidos en HDFS.

**Requisitos previos:** Tablas maestras en HDFS (create_tables_spark.py), directorios HDFS, data_cleaning escribiendo en filtered-data.

**Comando (nueva terminal):**
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
spark-submit --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_enrichment.py
```

**Salida:** HDFS processed/enriched (Parquet). Verificar: `hdfs dfs -ls /user/hadoop/processed/enriched/`

### Opción B: Análisis de grafos (batch)

**Qué hace:** Grafo de almacenes/rutas, PageRank, grados, bottlenecks. Escribe en HDFS.

**Requisitos:** `pip install graphframes-py setuptools` en el venv.

**Comando:**
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
PYSPARK_PYTHON=./venv/bin/python spark-submit --master "local[*]" \
  --packages io.graphframes:graphframes-spark3_2.12:0.10.0 \
  --conf spark.driver.host=127.0.0.1 \
  processing/spark/graphframes/network_analysis.py
```

**Salida:** network_pagerank, network_degrees, network_bottlenecks en HDFS.

### Opción C: Importar bottlenecks a MongoDB

**Qué hace:** Lee network_bottlenecks de HDFS e inserta en MongoDB bottlenecks.

**Requisitos:** Haber ejecutado antes el análisis de grafos (Opción B).

**Comando:**
```bash
spark-submit --master "local[*]" --conf spark.driver.host=127.0.0.1 \
  storage/mongodb/import_bottlenecks.py
```

### Opción D: Consumidor vehicle_status (opcional)

**Qué hace:** Consume filtered-data y mantiene estado de vehículos en MongoDB.

**Comando:** `python storage/mongodb/kafka_to_mongodb_vehicle_status.py`

## Orden recomendado

1. Enriquecimiento (A)
2. Análisis de grafos (B)
3. Import bottlenecks (C)
4. Vehicle status (D) opcional
