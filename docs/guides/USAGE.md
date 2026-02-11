# Guía de Uso

## Inicio del Sistema

### 1. Iniciar Servicios Base

```bash
# Iniciar HDFS y YARN
start-dfs.sh
start-yarn.sh

# Verificar estado
jps
```

### 2. Iniciar Kafka

```bash
# Iniciar Kafka en modo KRaft
cd $KAFKA_HOME
bin/kafka-storage.sh format -t <cluster-id> -c config/kraft/server.properties
bin/kafka-server-start.sh config/kraft/server.properties &
```

### 3. Iniciar NiFi

```bash
cd $NIFI_HOME
bin/nifi.sh start
```

Acceder a la interfaz web: http://localhost:8443/nifi

### 4. Iniciar MongoDB

En un entorno local típico (instalación por paquetes):

```bash
sudo systemctl start mongodb
sudo systemctl status mongodb
```

Si usas Docker (según el ejemplo de instalación):

```bash
docker start mongodb
```

### 5. Iniciar Airflow

```bash
# Iniciar webserver
airflow webserver --port 8080 &

# Iniciar scheduler
airflow scheduler &
```

Acceder a la interfaz web: http://localhost:8080

## Ejecución de Fases

### Fase I: Ingesta y Selección

1. **Importar flujo de NiFi**:
   - Acceder a NiFi UI
   - Importar template desde `ingestion/nifi/transport_monitoring_template.xml`

2. **Crear topics de Kafka**:
```bash
bin/kafka-topics.sh --create \
  --bootstrap-server nodo1:9092 \
  --topic raw-data \
  --partitions 3 \
  --replication-factor 1

bin/kafka-topics.sh --create \
  --bootstrap-server nodo1:9092 \
  --topic filtered-data \
  --partitions 3 \
  --replication-factor 1
```

3. **Iniciar flujo de NiFi**:
   - Activar todos los procesadores en el template

### Fase II: Preprocesamiento y Transformación

Ejecutar scripts de Spark:

```bash
# Limpieza de datos
spark-submit --master yarn \
  processing/spark/sql/data_cleaning.py

# Enriquecimiento
spark-submit --master yarn \
  processing/spark/sql/data_enrichment.py

# Análisis de grafos
spark-submit --master yarn \
  --packages graphframes:graphframes:0.8.2-spark3.5-s_2.12 \
  processing/spark/graphframes/network_analysis.py
```

### Fase III: Minería y Acción

Ejecutar streaming:

```bash
spark-submit --master yarn \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  processing/spark/streaming/delay_analysis.py
```

### Fase IV: Orquestación

1. **Copiar DAGs a Airflow**:
```bash
cp orchestration/airflow/dags/* ~/airflow/dags/
```

2. **Activar DAGs en la interfaz web de Airflow**

3. **Monitorear ejecuciones** desde la UI

## Monitoreo

### Ver logs de NiFi
```bash
tail -f $NIFI_HOME/logs/nifi-app.log
```

### Ver mensajes de Kafka
```bash
bin/kafka-console-consumer.sh \
  --bootstrap-server nodo1:9092 \
  --topic raw-data \
  --from-beginning
```

### Verificar datos en HDFS
```bash
hdfs dfs -ls /user/hadoop/raw
hdfs dfs -cat /user/hadoop/raw/part-00000 | head
```

### Consultar Hive
```bash
hive
> SHOW TABLES;
> SELECT * FROM transport_aggregates LIMIT 10;
```

### Consultar MongoDB

Con el shell de Mongo:

```bash
mongosh "mongodb://nodo1:27017/transport_db"
> db.vehicle_status.find().limit(10)
> db.route_delay_aggregates.find().limit(10)
```

## Troubleshooting

### Problemas comunes

1. **Puertos ocupados**: Verificar con `netstat -tulpn | grep [puerto]`
2. **Permisos HDFS**: Verificar con `hdfs dfs -ls /`
3. **Kafka no conecta**: Verificar configuración de `server.properties`
4. **Spark falla en YARN**: Verificar logs con `yarn logs -applicationId [app-id]`

## Detención del Sistema

```bash
# Detener Airflow
pkill -f airflow

# Detener NiFi
$NIFI_HOME/bin/nifi.sh stop

# Detener Kafka
pkill -f kafka

# Detener MongoDB (según instalación)
sudo systemctl stop mongodb || true
docker stop mongodb 2>/dev/null || true

# Detener YARN y HDFS
stop-yarn.sh
stop-dfs.sh
```
