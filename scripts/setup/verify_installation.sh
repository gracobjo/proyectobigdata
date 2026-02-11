#!/bin/bash
# Script para verificar la instalación de todos los componentes

echo "=== Verificación de Instalación del Proyecto Big Data ==="
echo ""

# Verificar Java
echo "1. Verificando Java..."
if command -v java &> /dev/null; then
    java -version
else
    echo "   ERROR: Java no está instalado"
    exit 1
fi

# Verificar Hadoop
echo ""
echo "2. Verificando Hadoop..."
if [ -d "$HADOOP_HOME" ]; then
    hadoop version | head -1
else
    echo "   ERROR: HADOOP_HOME no está configurado"
    exit 1
fi

# Verificar NiFi
echo ""
echo "3. Verificando NiFi..."
if [ -d "$NIFI_HOME" ]; then
    echo "   NiFi encontrado en $NIFI_HOME"
else
    echo "   ERROR: NIFI_HOME no está configurado"
    exit 1
fi

# Verificar Kafka
echo ""
echo "4. Verificando Kafka..."
if [ -d "$KAFKA_HOME" ]; then
    $KAFKA_HOME/bin/kafka-topics.sh --version 2>/dev/null || echo "   Kafka encontrado en $KAFKA_HOME"
else
    echo "   ERROR: KAFKA_HOME no está configurado"
    exit 1
fi

# Verificar Spark
echo ""
echo "5. Verificando Spark..."
if [ -d "$SPARK_HOME" ]; then
    $SPARK_HOME/bin/spark-submit --version 2>&1 | head -1
else
    echo "   ERROR: SPARK_HOME no está configurado"
    exit 1
fi

# Verificar Airflow
echo ""
echo "6. Verificando Airflow..."
if command -v airflow &> /dev/null; then
    airflow version
else
    echo "   ERROR: Airflow no está instalado"
    exit 1
fi

# Verificar Cassandra
echo ""
echo "7. Verificando Cassandra..."
if [ -d "$CASSANDRA_HOME" ]; then
    $CASSANDRA_HOME/bin/cassandra -v 2>&1 | head -1 || echo "   Cassandra encontrado en $CASSANDRA_HOME"
else
    echo "   ERROR: CASSANDRA_HOME no está configurado"
    exit 1
fi

# Verificar Hive
echo ""
echo "8. Verificando Hive..."
if [ -d "$HIVE_HOME" ]; then
    $HIVE_HOME/bin/hive --version 2>&1 | head -1 || echo "   Hive encontrado en $HIVE_HOME"
else
    echo "   ERROR: HIVE_HOME no está configurado"
    exit 1
fi

# Verificar Python
echo ""
echo "9. Verificando Python..."
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "   ERROR: Python3 no está instalado"
    exit 1
fi

# Verificar servicios
echo ""
echo "10. Verificando servicios activos..."
jps | grep -E "(NameNode|DataNode|ResourceManager|NodeManager|Kafka|NiFi|Cassandra)" || echo "   No hay servicios activos (esto es normal si no están iniciados)"

echo ""
echo "=== Verificación completada ==="
