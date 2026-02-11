#!/bin/bash
# Script para arrancar HDFS antes de ejecutar el pipeline
# Uso: bash scripts/run/00_start_hdfs.sh

echo "=== Arrancando HDFS ==="

# Verificar si ya está corriendo
if jps | grep -q NameNode; then
    echo "✓ HDFS ya está corriendo"
    jps | grep -E "NameNode|DataNode|SecondaryNameNode"
else
    echo "Arrancando NameNode..."
    hdfs --daemon start namenode 2>&1
    sleep 5
    
    echo "Arrancando DataNode..."
    hdfs --daemon start datanode 2>&1
    sleep 5
    
    echo "Verificando procesos..."
    jps | grep -E "NameNode|DataNode|SecondaryNameNode" || echo "⚠ Algunos procesos no están corriendo"
fi

echo ""
echo "Saliendo del modo seguro..."
hdfs dfsadmin -safemode leave 2>&1

sleep 2

echo ""
echo "Estado de HDFS:"
hdfs dfsadmin -report 2>&1 | head -10

echo ""
echo "✓ HDFS listo para usar"
