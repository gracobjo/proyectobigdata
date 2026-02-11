# Notas sobre el paso de Enriquecimiento (06)

## Mensajes que puedes ver

### 1. WARN AdminClientConfig

```
WARN AdminClientConfig: These configurations '[key.deserializer, value.deserializer, 
enable.auto.commit, max.poll.records, auto.offset.reset]' were supplied but are not used yet.
```

**Qué significa:** El conector Spark-Kafka recibe algunas opciones de consumidor que no utiliza (Spark usa su propia lógica de lectura). Es un aviso del cliente Kafka, no un error.

**Qué hacer:** Se puede ignorar. No afecta al funcionamiento del job. Si quieres reducir ruido en logs, no es necesario cambiar nada en tu código.

---

### 2. "Streaming query has been idle and waiting for new data more than 10000 ms"

```
INFO MicroBatchExecution: Streaming query has been idle and waiting for new data more than 10000 ms.
```

**Qué significa:** El job de enriquecimiento está corriendo y cada ~10 segundos hace un micro-batch. En ese intervalo no había **nuevos** mensajes en el topic `filtered-data`, así que no hay nada que procesar y el query queda “idle” (esperando datos).

**Es normal cuando:**
- Ya se procesaron todos los mensajes que había en `filtered-data` y no se está generando datos nuevos.
- El job de limpieza (`data_cleaning`) no está enviando datos nuevos a `filtered-data` en ese momento.

**Qué hacer:**
- **Nada** si solo quieres que el job siga en marcha: en cuanto lleguen nuevos mensajes a `filtered-data`, los procesará.
- **Ver actividad:** genera más datos de prueba para que `data_cleaning` escriba en `filtered-data` y el enriquecimiento deje de estar idle en los siguientes batches:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate
python scripts/utils/generate_sample_data.py 100
```

Tras unos 10–20 segundos deberías ver en los logs del enriquecimiento batches con `numInputRows > 0` y escrituras en HDFS.

---

## Comprobar que el enriquecimiento escribe en HDFS

Cuando haya procesado al menos un batch con datos:

```bash
hdfs dfs -ls /user/hadoop/processed/enriched/
```

Deberían aparecer directorios por fecha (por ejemplo `partition_date=2026-02-11/`) con ficheros Parquet.

---

## Resumen

| Mensaje | Tipo | Acción |
|--------|------|--------|
| AdminClientConfig ... were supplied but are not used | WARN | Ignorar |
| Streaming query has been idle and waiting for new data | INFO | Normal; opcional: generar más datos para ver actividad |

El paso 2 (enriquecimiento) está funcionando correctamente; está en modo “esperando nuevos datos” en `filtered-data`.
