# Arranque y control de la pila (stack)

Scripts en `scripts/stack/`: **start_stack.sh**, **status_stack.sh**, **stop_stack.sh**, **restart_stack.sh**. Orden: HDFS → YARN → Hive → MongoDB → Kafka → NiFi → Airflow. Variables por defecto en `stack_env.sh` (HADOOP_HOME=/usr/local/hadoop, etc.). Kafka: ejecutar una vez `scripts/setup/kafka_init_standalone.sh` si es la primera vez. Referencias: [CONFIGURATION.md](../guides/CONFIGURATION.md), [GETTING_STARTED.md](../GETTING_STARTED.md), [nifi-configuracion.md](../ingestion/nifi-configuracion.md).
