# Guía de Configuración

## Configuración de Componentes

### Apache NiFi

Archivo: `config/nifi/nifi.properties`

Configuraciones clave:
- `nifi.web.http.port=8443`
- `nifi.web.https.port=8443`
- `nifi.cluster.node.address=localhost`
- `nifi.cluster.node.protocol.port=8082`

### Apache Kafka (KRaft Mode)

Archivo: `config/kafka/server.properties`

Configuraciones clave:
```properties
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@nodo1:9093
listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
advertised.listeners=PLAINTEXT://nodo1:9092
log.dirs=/tmp/kafka-logs
```

### Apache Spark

Archivo: `config/spark/spark-defaults.conf`

Configuraciones clave:
```properties
spark.master=yarn
spark.executor.memory=2g
spark.executor.cores=2
spark.driver.memory=1g
spark.sql.warehouse.dir=hdfs://nodo1:9000/user/hive/warehouse
```

### Apache Airflow

Archivo: `config/airflow/airflow.cfg`

Configuraciones clave:
- `executor=LocalExecutor`
- `dags_folder=~/airflow/dags`
- `sql_alchemy_conn=sqlite:////home/hadoop/airflow/airflow.db`

### Apache Hive

Archivo: `config/hive/hive-site.xml`

Configuraciones clave:
- `hive.metastore.warehouse.dir`: Directorio HDFS para warehouse
- `javax.jdo.option.ConnectionURL`: URL de conexión a Metastore

### MongoDB

MongoDB puede ejecutarse con configuración por defecto para desarrollo. Los parámetros clave son:

- `bindIp`: interfaces donde escucha MongoDB (configurar como `0.0.0.0` o `nodo1` para acceso desde otros nodos)
- `port`: puerto de escucha (por defecto `27017`)
- `security.authorization`: modo de autenticación (puede quedar desactivado en local)

## Variables de Entorno

Añadir al `~/.bashrc`:

```bash
export HADOOP_HOME=/opt/hadoop
export NIFI_HOME=/opt/nifi
export KAFKA_HOME=/opt/kafka
export SPARK_HOME=/opt/spark
export HIVE_HOME=/opt/hive
export MONGO_URI="mongodb://nodo1:27017/transport_db"

export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export PATH=$PATH:$NIFI_HOME/bin
export PATH=$PATH:$KAFKA_HOME/bin
export PATH=$PATH:$SPARK_HOME/bin
export PATH=$PATH:$CASSANDRA_HOME/bin
export PATH=$PATH:$HIVE_HOME/bin
```

## Configuración de Red

Asegurar que los siguientes puertos estén disponibles:
- **HDFS NameNode**: 9000, 9870
- **HDFS DataNode**: 9864
- **YARN ResourceManager**: 8088
- **YARN NodeManager**: 8042
- **NiFi**: 8443
- **Kafka**: 9092, 9093
- **Spark**: 4040 (UI)
- **Airflow**: 8080
- **MongoDB**: 27017
- **Hive Metastore**: 9083

## Configuración de Seguridad

### HDFS

Configurar permisos:
```bash
hdfs dfs -chmod 755 /user/hadoop
```

### Kafka

Para producción, configurar SASL/SSL en `server.properties`

### Airflow

Configurar autenticación en `airflow.cfg`:
```ini
[webserver]
authenticate = True
auth_backend = airflow.contrib.auth.backends.password_auth
```
