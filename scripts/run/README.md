# Scripts de Ejecución del Pipeline

Scripts listos para ejecutar en cada terminal.

## Orden de Ejecución

### Paso 0: Arrancar HDFS (IMPORTANTE - Primero)

```bash
bash scripts/run/00_start_hdfs.sh
```

**⚠️ CRÍTICO:** HDFS debe estar corriendo antes de ejecutar cualquier script de Spark. Si no está corriendo, verás errores de "Connection refused" en `localhost:9000`.

---

### Terminal 1: Generar datos (una vez)
```bash
bash scripts/run/01_generate_data.sh
```
**Qué hace:** Genera 100 mensajes de prueba en el topic `raw-data` de Kafka.
**Cuándo ejecutar:** Una vez al inicio, antes de ejecutar el pipeline.

---

### Terminal 2: Limpieza de datos (dejar corriendo)
```bash
bash scripts/run/02_data_cleaning.sh
```
**Qué hace:** Lee de `raw-data`, limpia los datos y escribe en `filtered-data`.
**Cuándo ejecutar:** Después de generar datos. **DEJAR CORRIENDO** hasta que termines de probar.

---

### Terminal 3: Análisis de retrasos (dejar corriendo)
```bash
bash scripts/run/03_delay_analysis.sh
```
**Qué hace:** Lee de `filtered-data`, calcula agregados de retrasos y escribe en `alerts` (Kafka) y HDFS.
**Cuándo ejecutar:** Después de que Terminal 2 haya procesado algunos batches (espera ~30 segundos). **DEJAR CORRIENDO**.

---

### Terminal 4: Consumidor MongoDB (dejar corriendo)
```bash
bash scripts/run/04_mongodb_consumer.sh
```
**Qué hace:** Lee de `alerts` (Kafka) y escribe en MongoDB (`route_delay_aggregates`).
**Cuándo ejecutar:** Después de que Terminal 3 haya generado algunos alerts (espera ~30 segundos). **DEJAR CORRIENDO**.

---

### Terminal 5: Verificar MongoDB (cuando quieras)
```bash
bash scripts/run/05_verify_mongodb.sh
```

---

### Siguientes pasos (opcionales)

**Terminal 6: Enriquecimiento** (filtered-data + tablas maestras -> HDFS):
```bash
bash scripts/run/06_data_enrichment.sh
```
Requisitos: tablas maestras en HDFS (`create_tables_spark.py`).

**Análisis de grafos** (batch, una vez):
```bash
bash scripts/run/07_network_analysis.sh
```
Requisitos: `pip install graphframes-py setuptools`.

**Importar bottlenecks a MongoDB** (después de 07):
```bash
bash scripts/run/08_import_bottlenecks.sh
```

---

## Comandos Completos (Copia y Pega)

### Terminal 1 (Generar datos):
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
python scripts/utils/generate_sample_data.py 100
```

### Terminal 2 (Limpieza):
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/sql/data_cleaning.py
```

### Terminal 3 (Análisis de retrasos):
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
spark-submit \
  --master "local[*]" \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --conf spark.driver.host=127.0.0.1 \
  --conf spark.driver.bindAddress=127.0.0.1 \
  --conf spark.sql.shuffle.partitions=4 \
  processing/spark/streaming/delay_analysis.py
```

### Terminal 4 (Consumidor MongoDB):
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
python storage/mongodb/kafka_to_mongodb_alerts.py
```

### Terminal 5 (Verificar):
```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
python storage/mongodb/verify_data.py
```

---

## Flujo Visual

```
Terminal 1: 01_generate_data.sh
    ↓ (genera raw-data)
    
Terminal 2: 02_data_cleaning.sh (DEJAR CORRIENDO)
    ↓ (lee raw-data → escribe filtered-data)
    
Terminal 3: 03_delay_analysis.sh (DEJAR CORRIENDO)
    ↓ (lee filtered-data → escribe alerts)
    
Terminal 4: 04_mongodb_consumer.sh (DEJAR CORRIENDO)
    ↓ (lee alerts → escribe MongoDB)
    
Terminal 5: 05_verify_mongodb.sh (cuando quieras)
    ↓ (muestra resultados)
```

---

## Notas Importantes

1. **Orden:** Ejecutar en secuencia: Terminal 1 → Terminal 2 → Terminal 3 → Terminal 4
2. **Esperar:** Entre cada terminal, espera ~30 segundos para que procese datos
3. **Dejar corriendo:** Terminales 2, 3 y 4 deben seguir ejecutándose
4. **Verificar:** Usa Terminal 5 para verificar el progreso en cualquier momento
