#!/bin/bash
# Script para configurar el cluster distribuido
# Ejecutar en ambos nodos (nodo1 y nodo2)

set -e

echo "=== Configuración del Cluster Distribuido ==="
echo ""

# Detectar el nodo actual
CURRENT_HOST=$(hostname)
echo "Nodo actual: $CURRENT_HOST"

# Verificar conectividad entre nodos
echo ""
echo "Verificando conectividad..."
if ping -c 1 nodo1 > /dev/null 2>&1; then
    echo "✓ nodo1 alcanzable"
else
    echo "✗ No se puede alcanzar nodo1"
    echo "  Asegúrate de que /etc/hosts tenga la entrada correcta"
fi

if ping -c 1 nodo2 > /dev/null 2>&1; then
    echo "✓ nodo2 alcanzable"
else
    echo "✗ No se puede alcanzar nodo2"
    echo "  Asegúrate de que /etc/hosts tenga la entrada correcta"
fi

# Verificar que Hadoop esté instalado
if [ -z "$HADOOP_HOME" ]; then
    echo "ERROR: HADOOP_HOME no está configurado"
    exit 1
fi

echo ""
echo "=== Configuración de HDFS ==="

# Crear directorios necesarios en HDFS
echo "Creando directorios en HDFS..."
hdfs dfs -mkdir -p /user/hadoop/raw || true
hdfs dfs -mkdir -p /user/hadoop/processed || true
hdfs dfs -mkdir -p /user/hadoop/checkpoints || true
hdfs dfs -mkdir -p /user/hive/warehouse || true
hdfs dfs -mkdir -p /spark-logs || true

echo "✓ Directorios creados"

# Verificar permisos
hdfs dfs -chmod 755 /user/hadoop || true
hdfs dfs -chmod 755 /user/hive || true

echo ""
echo "=== Verificación de Servicios ==="

# Verificar servicios de Hadoop
if jps | grep -q NameNode; then
    echo "✓ NameNode activo"
else
    echo "✗ NameNode no está activo (debe estar en nodo1)"
fi

if jps | grep -q DataNode; then
    echo "✓ DataNode activo"
else
    echo "✗ DataNode no está activo"
fi

if jps | grep -q ResourceManager; then
    echo "✓ ResourceManager activo"
else
    echo "✗ ResourceManager no está activo (debe estar en nodo1)"
fi

if jps | grep -q NodeManager; then
    echo "✓ NodeManager activo"
else
    echo "✗ NodeManager no está activo"
fi

echo ""
echo "=== Configuración completada ==="
echo ""
echo "Próximos pasos:"
echo "1. Verificar que todos los servicios estén activos"
echo "2. Crear topics de Kafka: ./ingestion/kafka/create_topics.sh"
echo "3. Iniciar servicios adicionales (NiFi, MongoDB, Airflow) según necesidad"
