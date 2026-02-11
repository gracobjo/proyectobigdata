# Guía de Instalación

## Requisitos del Sistema

- **SO**: Linux (recomendado) o macOS
- **Java**: JDK 11 o superior
- **Python**: 3.8 o superior
- **Memoria**: Mínimo 8GB RAM (recomendado 16GB+)
- **Disco**: Mínimo 50GB espacio libre

## Instalación de Componentes Apache

### 1. Hadoop 3.4.2

```bash
# Descargar Hadoop
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.4.2/hadoop-3.4.2.tar.gz
tar -xzf hadoop-3.4.2.tar.gz
mv hadoop-3.4.2 /opt/hadoop

# Configurar variables de entorno
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```

### 2. Apache NiFi 2.6.0

```bash
# Descargar NiFi
wget https://archive.apache.org/dist/nifi/2.6.0/nifi-2.6.0-bin.tar.gz
tar -xzf nifi-2.6.0-bin.tar.gz
mv nifi-2.6.0 /opt/nifi

# Configurar variables de entorno
export NIFI_HOME=/opt/nifi
export PATH=$PATH:$NIFI_HOME/bin
```

### 3. Apache Kafka 3.9.1

```bash
# Descargar Kafka (KRaft mode)
wget https://archive.apache.org/dist/kafka/3.9.1/kafka_2.13-3.9.1.tgz
tar -xzf kafka_2.13-3.9.1.tgz
mv kafka_2.13-3.9.1 /opt/kafka

# Configurar variables de entorno
export KAFKA_HOME=/opt/kafka
export PATH=$PATH:$KAFKA_HOME/bin
```

### 4. Apache Spark 3.5.x

```bash
# Descargar Spark
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xzf spark-3.5.0-bin-hadoop3.tgz
mv spark-3.5.0-bin-hadoop3 /opt/spark

# Configurar variables de entorno
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin
```

### 5. Apache Airflow 2.10.x

```bash
# Instalar Airflow con pip
pip install apache-airflow==2.10.0

# Inicializar base de datos
airflow db init

# Crear usuario admin
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### 6. MongoDB

Puedes instalar MongoDB de varias formas. Un ejemplo sencillo en Linux (Debian/Ubuntu) sería:

```bash
# Instalar MongoDB Community (ejemplo genérico, ajusta a tu distro)
sudo apt update
sudo apt install -y mongodb

# Verificar servicio
sudo systemctl status mongodb
```

O bien utilizar Docker:

```bash
docker run -d --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin \
  mongo:6
```

### 7. Apache Hive

```bash
# Hive requiere Hadoop previamente instalado
wget https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz
tar -xzf apache-hive-3.1.3-bin.tar.gz
mv apache-hive-3.1.3-bin /opt/hive

# Configurar variables de entorno
export HIVE_HOME=/opt/hive
export PATH=$PATH:$HIVE_HOME/bin
```

## Configuración del Proyecto

1. Clonar o copiar los archivos de configuración del proyecto:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
cp config/* /opt/[componente]/conf/
```

2. Ajustar las rutas y parámetros según tu entorno en los archivos de configuración.

3. Inicializar HDFS:

```bash
hdfs namenode -format
start-dfs.sh
start-yarn.sh
```

4. Crear directorios necesarios en HDFS:

```bash
hdfs dfs -mkdir -p /user/hadoop/raw
hdfs dfs -mkdir -p /user/hadoop/processed
```

## Dependencias Python del proyecto

El proyecto usa un **entorno virtual** y un `requirements.txt` para scripts de procesamiento (Spark, Kafka, MongoDB) y para la visualización del grafo.

1. Crear y activar el entorno virtual:

```bash
cd /home/hadoop/Documentos/ProyectoBigData
bash scripts/setup/setup_venv.sh
source venv/bin/activate
```

2. Instalar dependencias Python:

```bash
pip install -r requirements.txt
```

Incluye, entre otras: `pyspark`, `kafka-python`, `graphframes-py`, `pymongo`, `pandas`. Para la **visualización del grafo** (Streamlit) también están incluidas: `streamlit`, `pyvis`, `networkx`.

En sistemas con Python gestionado por el SO (PEP 668), usar siempre el venv; no instalar paquetes con `pip` a nivel sistema.

### Visualización del grafo (opcional)

Para ejecutar la app **Streamlit** que visualiza el grafo de la red de transporte y los cuellos de botella desde MongoDB:

```bash
source venv/bin/activate
streamlit run viz/app_grafo.py
```

Requisitos: las dependencias anteriores (streamlit, pyvis, networkx) ya están en `requirements.txt`. MongoDB es opcional (si está activo y con datos en `transport_db.bottlenecks`, se resaltan los nodos bottleneck en rojo).

Guía detallada: [Visualización del grafo](VISUALIZACION_GRAFO.md).

## Verificación de Instalación

Ejecutar los scripts de verificación:

```bash
./scripts/setup/verify_installation.sh
```

## Próximos Pasos

Una vez completada la instalación, consultar:
- [Guía de Configuración](CONFIGURATION.md)
- [Guía de Uso](USAGE.md)
- [Visualización del grafo](VISUALIZACION_GRAFO.md) (app Streamlit opcional)
