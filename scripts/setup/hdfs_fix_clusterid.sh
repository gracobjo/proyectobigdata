#!/bin/bash
# Corrige el error "Incompatible clusterIDs" / "All specified directories have failed to load"
# del DataNode: borra los datos locales del DataNode para que tome el clusterID del NameNode.
# Uso: bash scripts/setup/hdfs_fix_clusterid.sh

set -e
HADOOP_CONF="${HADOOP_HOME:-/usr/local/hadoop}/etc/hadoop"

echo "=== Corrección clusterID DataNode ==="
echo ""

# Obtener ruta de dfs.datanode.data.dir (puede ser file:/path o file:///path)
DN_DIR=$(grep -A1 "<name>dfs.datanode.data.dir</name>" "$HADOOP_CONF/hdfs-site.xml" 2>/dev/null | grep "<value>" | sed 's/.*<value>\(.*\)<\/value>.*/\1/' | sed 's|^file:||' | sed 's|^//||' | head -1)

if [ -z "$DN_DIR" ] || [ ! -d "$DN_DIR" ]; then
  # Fallback: rutas típicas
  for d in /usr/local/hadoop/data/datanode /usr/local/hadoop-3.4.1/data/datanode; do
    if [ -d "$d" ]; then
      DN_DIR="$d"
      break
    fi
  done
fi

if [ -z "$DN_DIR" ] || [ ! -d "$DN_DIR" ]; then
  echo "No se encontró el directorio de datos del DataNode. Comprueba dfs.datanode.data.dir en hdfs-site.xml."
  exit 1
fi

echo "Directorios de datos del DataNode: $DN_DIR"
echo ""

# Parar DataNode
echo "1. Parando DataNode..."
hdfs --daemon stop datanode 2>/dev/null || true
sleep 3

echo "2. Borrando contenido de $DN_DIR (para que el DataNode reciba el clusterID del NameNode)..."
sudo rm -rf "$DN_DIR"/*
echo "   Hecho."

echo "3. Arrancando DataNode..."
hdfs --daemon start datanode
sleep 5

echo ""
echo "4. Comprobando..."
hdfs dfsadmin -report 2>&1 | head -30

echo ""
echo "Si ves 'Live datanodes (1)', ya está. Prueba: echo \"test\" | hdfs dfs -put - /test.txt && hdfs dfs -cat /test.txt"
echo "=== Fin ==="
