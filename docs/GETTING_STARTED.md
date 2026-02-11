# Guía de Inicio Rápido - Por Dónde Empezar

## 🚀 Roadmap de Ejecución del Proyecto

### FASE 0: Preparación del Entorno (Primera vez)

#### Paso 1: Verificar Instalaciones Base
```bash
# Verificar que Hadoop esté instalado y configurado
echo $HADOOP_HOME
hadoop version

# Verificar conectividad entre nodos
ping nodo1
ping nodo2
```

#### Paso 2: Configurar /etc/hosts (si no está hecho)
```bash
# En AMBOS nodos (nodo1 y nodo2)
sudo nano /etc/hosts

# Añadir las líneas (ajustar IPs según tu configuración):
<IP_nodo1>    nodo1
<IP_nodo2>    nodo2
```

#### Paso 3: Iniciar Servicios Base de Hadoop
```bash
# En nodo1 (donde está el NameNode)
start-dfs.sh
start-yarn.sh

# Verificar que los servicios estén activos
jps
# Deberías ver: NameNode, DataNode, ResourceManager, NodeManager

# Verificar desde nodo2 también
ssh nodo2
jps
# Deberías ver: DataNode, NodeManager
```

#### Paso 4: Configurar el Cluster
```bash
cd /home/hadoop/Documentos/ProyectoBigData

# Ejecutar script de configuración (crea directorios en HDFS)
./scripts/setup/configure_cluster.sh
```

---

### FASE 1: Configurar Ingesta (NiFi + Kafka)

#### Paso 5: Instalar y Configurar Kafka
```bash
# Si no está instalado, seguir docs/guides/INSTALLATION.md

# Copiar configuración del proyecto
cp config/kafka/server.properties $KAFKA_HOME/config/kraft/server.properties

# Iniciar Kafka en nodo1
cd $KAFKA_HOME
bin/kafka-storage.sh format -t $(uuidgen) -c config/kraft/server.properties
bin/kafka-server-start.sh config/kraft/server.properties &
```

#### Paso 6: Crear Topics de Kafka
```bash
cd /home/hadoop/Documentos/ProyectoBigData
./ingestion/kafka/create_topics.sh

# Verificar que se crearon
$KAFKA_HOME/bin/kafka-topics.sh --list --bootstrap-server nodo1:9092
```

#### Paso 7: Configurar NiFi (Opcional - si vas a usar)
```bash
# Si no está instalado, seguir docs/guides/INSTALLATION.md

# Iniciar NiFi en nodo1
cd $NIFI_HOME
bin/nifi.sh start

# Acceder a la interfaz web
# http://nodo1:8443/nifi
# Si existe template: importar desde ingestion/nifi/. Si no: montar flujos según docs/guides/NIFI_FLUJOS.md
```

---

### FASE 2: Preparar Datos Maestros (Hive)

#### Paso 8: Iniciar Hive Metastore
```bash
# En nodo1
cd $HIVE_HOME

# Copiar configuración
cp /home/hadoop/Documentos/ProyectoBigData/config/hive/hive-site.xml conf/

# Iniciar metastore
bin/hive --service metastore &
```

#### Paso 9: Crear Tablas Maestras
```bash
# Abrir Hive CLI
hive

# Ejecutar script de creación de tablas maestras
source /home/hadoop/Documentos/ProyectoBigData/data/master/sample_master_data.sql;

# Verificar tablas creadas
SHOW TABLES;
SELECT * FROM master_routes LIMIT 5;
SELECT * FROM master_vehicles LIMIT 5;
```

---

### FASE 3: Probar con Datos de Ejemplo

#### Paso 10: Generar Datos de Prueba
```bash
cd /home/hadoop/Documentos/ProyectoBigData

# Instalar dependencia si falta
pip3 install kafka-python

# Generar datos de ejemplo
python3 scripts/utils/generate_sample_data.py

# Verificar que llegaron a Kafka
$KAFKA_HOME/bin/kafka-console-consumer.sh \
  --bootstrap-server nodo1:9092 \
  --topic raw-data \
  --from-beginning \
  --max-messages 5
```

---

### FASE 4: Ejecutar Pipeline de Procesamiento

#### Paso 11: Ejecutar Limpieza de Datos (Fase II - Parte 1)
```bash
cd /home/hadoop/Documentos/ProyectoBigData

# En una terminal, ejecutar limpieza (se queda corriendo)
spark-submit --master yarn \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  processing/spark/sql/data_cleaning.py
```

#### Paso 12: Verificar Datos Filtrados
```bash
# En otra terminal, verificar que los datos filtrados lleguen a Kafka
$KAFKA_HOME/bin/kafka-console-consumer.sh \
  --bootstrap-server nodo1:9092 \
  --topic filtered-data \
  --from-beginning \
  --max-messages 5
```

#### Paso 13: Ejecutar Enriquecimiento (Fase II - Parte 2)
```bash
# En otra terminal
spark-submit --master yarn \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  processing/spark/sql/data_enrichment.py
```

#### Paso 14: Verificar Datos en HDFS
```bash
# Verificar que los datos enriquecidos se guardaron
hdfs dfs -ls /user/hadoop/processed/enriched
hdfs dfs -ls /user/hadoop/processed/enriched/route_id=*
```

#### Paso 15: Ejecutar Análisis de Grafos (Fase II - Parte 3)
```bash
# Ejecutar análisis de red (procesamiento batch)
spark-submit --master yarn \
  --packages graphframes:graphframes:0.8.2-spark3.5-s_2.12 \
  processing/spark/graphframes/network_analysis.py

# Verificar resultados en Hive
hive
> SELECT * FROM network_pagerank ORDER BY pagerank DESC LIMIT 5;
> SELECT * FROM network_bottlenecks;
```

#### Paso 16: Ejecutar Análisis de Retrasos (Fase III)
```bash
# Ejecutar streaming de análisis de retrasos
spark-submit --master yarn \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  processing/spark/streaming/delay_analysis.py

# En otra terminal, verificar datos en Hive
hive
> SELECT * FROM delay_aggregates ORDER BY window_start DESC LIMIT 10;
```

---

### FASE 5: Configurar MongoDB (Opcional)

#### Paso 17: Instalar e Iniciar MongoDB
```bash
# Seguir docs/guides/INSTALLATION.md para instalar MongoDB

# Iniciar MongoDB en nodo1
sudo systemctl start mongodb
# O si usas Docker:
docker start mongodb

# Conectar y crear colecciones
mongosh "mongodb://nodo1:27017/transport_db"

# Crear colecciones según diseño en storage/cassandra/schema.cql
# (El archivo tiene comentarios JavaScript con los comandos)
```

---

### FASE 6: Configurar Airflow (Fase IV)

#### Paso 18: Configurar Airflow
```bash
# Si no está instalado, seguir docs/guides/INSTALLATION.md

# Copiar DAGs
cp orchestration/airflow/dags/* ~/airflow/dags/

# Iniciar Airflow
airflow webserver --port 8080 &
airflow scheduler &

# Acceder a la interfaz web
# http://nodo1:8080
```

#### Paso 19: Activar y Ejecutar DAGs
1. Abrir http://nodo1:8080
2. Activar el DAG `transport_monitoring_pipeline`
3. Activar el DAG `monthly_model_retraining`
4. Monitorear ejecuciones

---

## 📋 Checklist de Verificación

Marca cada paso conforme lo completes:

### Preparación
- [ ] Hadoop instalado y configurado
- [ ] /etc/hosts configurado en ambos nodos
- [ ] HDFS y YARN iniciados
- [ ] Script de configuración ejecutado

### Ingesta
- [ ] Kafka instalado y corriendo
- [ ] Topics creados (raw-data, filtered-data, alerts)
- [ ] NiFi configurado (opcional)

### Datos Maestros
- [ ] Hive Metastore iniciado
- [ ] Tablas maestras creadas (master_routes, master_vehicles)
- [ ] Datos maestros insertados

### Procesamiento
- [ ] Datos de prueba generados
- [ ] Limpieza de datos ejecutándose
- [ ] Enriquecimiento ejecutándose
- [ ] Análisis de grafos ejecutado
- [ ] Análisis de retrasos ejecutándose

### Persistencia
- [ ] Datos verificados en HDFS
- [ ] Tablas verificadas en Hive
- [ ] MongoDB configurado (opcional)

### Orquestación
- [ ] Airflow instalado y corriendo
- [ ] DAGs copiados y activados
- [ ] Ejecuciones monitoreadas

---

## 🆘 Troubleshooting Rápido

### Problema: No puedo conectar a nodo2
```bash
# Verificar /etc/hosts
cat /etc/hosts

# Verificar conectividad
ping nodo2
```

### Problema: Kafka no inicia
```bash
# Verificar puertos
netstat -tulpn | grep 9092

# Verificar logs
tail -f $KAFKA_HOME/logs/server.log
```

### Problema: Spark falla en YARN
```bash
# Ver logs de YARN
yarn logs -applicationId <app-id>

# Verificar recursos disponibles
yarn node -list
```

### Problema: Hive no encuentra tablas
```bash
# Verificar que metastore esté corriendo
jps | grep -i metastore

# Verificar configuración
hive -e "SHOW TABLES;"
```

---

## 📚 Próximos Pasos

Una vez completados los pasos básicos:

1. **Leer documentación completa**: `docs/guides/USAGE.md`
2. **Revisar arquitectura**: `docs/architecture/ARCHITECTURE.md`
3. **Personalizar configuraciones**: `config/cluster.properties`
4. **Explorar scripts avanzados**: `scripts/`
5. **Revisar entregables**: `docs/ENTREGABLES.md`

---

## 💡 Consejos

- **Ejecuta los pasos en orden**: Cada fase depende de la anterior
- **Verifica cada paso**: No pases al siguiente hasta confirmar que funciona
- **Usa múltiples terminales**: Algunos procesos son de larga duración (streaming)
- **Revisa los logs**: Si algo falla, los logs te darán pistas
- **Empieza pequeño**: Prueba con pocos datos primero, luego escala

---

## 🎯 Orden Recomendado para Primera Ejecución

1. **Hoy**: Pasos 1-4 (Preparación del entorno)
2. **Hoy**: Pasos 5-7 (Configurar ingesta)
3. **Mañana**: Pasos 8-10 (Datos maestros y prueba)
4. **Mañana**: Pasos 11-16 (Ejecutar pipeline completo)
5. **Después**: Pasos 17-19 (MongoDB y Airflow)

¡Buena suerte con tu proyecto! 🚀
