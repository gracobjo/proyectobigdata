# Guía de Troubleshooting

## Problemas Comunes y Soluciones

### 1. Kafka no inicia

**Síntoma**: Error al iniciar Kafka en modo KRaft

**Solución**:
```bash
# Verificar que el cluster-id esté configurado
cd $KAFKA_HOME
bin/kafka-storage.sh format -t $(uuidgen | tr -d '-') -c config/kraft/server.properties

# Verificar puertos disponibles
netstat -tulpn | grep 9092
netstat -tulpn | grep 9093
```

### 2. Kafka: "No readable meta.properties files found" al arrancar

**Síntoma**: Al ejecutar `kafka-server-start.sh` aparece `Exiting Kafka due to fatal exception` y `No readable meta.properties files found`.

**Causa**: En modo KRaft el storage de metadatos debe formatearse una vez (o se borró/corrompió).

**Solución**:
```bash
cd /home/hadoop/Documentos/ProyectoBigData
bash scripts/setup/kafka_init_standalone.sh
```
Luego arrancar Kafka: `$KAFKA_HOME/bin/kafka-server-start.sh -daemon $KAFKA_HOME/config/server.properties`  
Y crear los topics: `bash ingestion/kafka/create_topics.sh`

### 3. Kafka: consumer recibe 0 mensajes (TimeoutException)

**Síntoma**: `kafka-console-consumer.sh --topic raw-data --from-beginning` termina con `Processed a total of 0 messages` o TimeoutException, aunque el producer haya enviado mensajes.

**Causa**: Si `advertised.listeners` está en `nodo1:9092` y en `/etc/hosts` nodo1 apunta a 192.168.56.1, los clientes intentan conectarse a esa IP para leer y no pueden.

**Solución**:
1. Editar el **server.properties que usa Kafka** (p. ej. `/opt/kafka/config/server.properties`):
   ```bash
   # Cambiar
   advertised.listeners=PLAINTEXT://nodo1:9092
   # por
   advertised.listeners=PLAINTEXT://localhost:9092
   ```
2. Reiniciar Kafka (parar el proceso y volver a arrancarlo).
3. Opcional: copiar la config del proyecto:
   ```bash
   cp /home/hadoop/Documentos/ProyectoBigData/config/kafka/server.properties /opt/kafka/config/server.properties
   ```
   y reiniciar Kafka.
4. Volver a generar datos y probar el consumer:
   ```bash
   python scripts/utils/generate_sample_data.py 20
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
     --topic raw-data --from-beginning --max-messages 3 --timeout-ms 10000
   ```

### 4. Spark falla al conectarse a YARN

**Síntoma**: `ApplicationMaster` no puede conectarse

**Solución**:
```bash
# Verificar que YARN esté ejecutándose
jps | grep ResourceManager
jps | grep NodeManager

# Verificar configuración de Spark
cat $SPARK_HOME/conf/spark-defaults.conf | grep master

# Ver logs de YARN
yarn logs -applicationId <app-id>
```

### 5. NiFi no puede escribir en HDFS

**Síntoma**: Error de permisos al escribir en HDFS

**Solución**:
```bash
# Verificar permisos de HDFS
hdfs dfs -ls /user/hadoop

# Crear directorio si no existe
hdfs dfs -mkdir -p /user/hadoop/raw
hdfs dfs -chmod 777 /user/hadoop/raw

# Verificar usuario de NiFi
# Editar nifi.properties y configurar nifi.user
```

### 6. GraphFrames no encuentra el paquete

**Síntoma**: `ModuleNotFoundError: No module named 'graphframes'`

**Solución**:
```bash
# Instalar GraphFrames via Spark packages
spark-submit --packages graphframes:graphframes:0.8.2-spark3.5-s_2.12 \
  processing/spark/graphframes/network_analysis.py

# O añadir al spark-defaults.conf:
spark.jars.packages graphframes:graphframes:0.8.2-spark3.5-s_2.12
```

### 7. Airflow DAG no aparece

**Síntoma**: DAG no visible en la interfaz web

**Solución**:
```bash
# Verificar sintaxis del DAG
python3 orchestration/airflow/dags/transport_monitoring_dag.py

# Verificar permisos del archivo
ls -la ~/airflow/dags/

# Verificar logs de Airflow
tail -f ~/airflow/logs/scheduler/latest/*.log

# Reiniciar scheduler
pkill -f airflow-scheduler
airflow scheduler &
```

### 8. Hive no puede crear tablas

**Síntoma**: Error al crear tablas en Hive

**Solución**:
```bash
# Verificar que Metastore esté ejecutándose
jps | grep RunJar

# Iniciar Metastore si no está corriendo
hive --service metastore &

# Verificar permisos del warehouse
hdfs dfs -ls /user/hive/warehouse
hdfs dfs -chmod 777 /user/hive/warehouse
```

### 9. Cassandra no acepta conexiones

**Síntoma**: `NoHostAvailableException`

**Solución**:
```bash
# Verificar que Cassandra esté ejecutándose
jps | grep CassandraDaemon

# Verificar configuración
cat $CASSANDRA_HOME/conf/cassandra.yaml | grep listen_address
cat $CASSANDRA_HOME/conf/cassandra.yaml | grep rpc_address

# Probar conexión
cqlsh localhost
```

### 10. Spark Streaming no procesa mensajes

**Síntoma**: No hay output del streaming

**Solución**:
```bash
# Verificar que Kafka tenga mensajes
kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic filtered-data --from-beginning

# Verificar checkpoints
hdfs dfs -ls /user/hadoop/checkpoints/

# Limpiar checkpoints si es necesario (cuidado: perderá estado)
hdfs dfs -rm -r /user/hadoop/checkpoints/delay_analysis
```

### 11. Memoria insuficiente en Spark

**Síntoma**: `OutOfMemoryError`

**Solución**:
```bash
# Aumentar memoria del executor
spark-submit --executor-memory 4g --driver-memory 2g \
  processing/spark/sql/data_cleaning.py

# O modificar spark-defaults.conf:
spark.executor.memory 4g
spark.driver.memory 2g
```

### 12. Puerto ya en uso

**Síntoma**: `Address already in use`

**Solución**:
```bash
# Encontrar proceso usando el puerto
sudo lsof -i :9092
sudo lsof -i :8080
sudo lsof -i :8443

# Matar proceso si es necesario
kill -9 <PID>

# O cambiar puerto en configuración
```

## Verificación de Salud del Sistema

Ejecutar el script de verificación:
```bash
./scripts/setup/verify_installation.sh
```

## Logs Importantes

- **NiFi**: `$NIFI_HOME/logs/nifi-app.log`
- **Kafka**: `$KAFKA_HOME/logs/server.log`
- **Spark**: `$SPARK_HOME/work/` o logs de YARN
- **Airflow**: `~/airflow/logs/`
- **Cassandra**: `$CASSANDRA_HOME/logs/system.log`
- **Hive**: `$HIVE_HOME/logs/`

## Comandos Útiles

```bash
# Ver todos los servicios activos
jps

# Ver uso de recursos
top
htop

# Ver espacio en disco
df -h

# Ver espacio en HDFS
hdfs dfsadmin -report

# Ver aplicaciones YARN
yarn application -list

# Ver topics de Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092

# Ver mensajes en un topic
kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic raw-data --from-beginning --max-messages 10
```
