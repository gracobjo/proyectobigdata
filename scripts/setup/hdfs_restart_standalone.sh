#!/bin/bash
# Reinicia HDFS en modo standalone y verifica que el DataNode se registre.
# Ejecutar DESPUÉS de copiar hdfs-site-standalone.xml a /usr/local/hadoop/etc/hadoop/hdfs-site.xml

set -e

echo "=== Reinicio de HDFS (modo standalone) ==="
echo ""

# Comprobar que la config correcta está instalada
if ! grep -q "dfs.datanode.address" /usr/local/hadoop/etc/hadoop/hdfs-site.xml 2>/dev/null; then
    echo "ERROR: No se encuentra dfs.datanode.address en hdfs-site.xml"
    echo "Ejecuta primero:"
    echo "  sudo cp /home/hadoop/Documentos/ProyectoBigData/config/hdfs/hdfs-site-standalone.xml /usr/local/hadoop/etc/hadoop/hdfs-site.xml"
    exit 1
fi

echo "1. Deteniendo servicios HDFS..."
hdfs --daemon stop datanode     2>/dev/null || true
hdfs --daemon stop secondarynamenode 2>/dev/null || true
hdfs --daemon stop namenode     2>/dev/null || true
sleep 5

echo "2. Iniciando NameNode..."
hdfs --daemon start namenode
sleep 8

echo "3. Iniciando DataNode..."
hdfs --daemon start datanode
sleep 8

echo "4. Iniciando Secondary NameNode..."
hdfs --daemon start secondarynamenode
sleep 3

echo ""
echo "5. Comprobando procesos..."
jps | grep -E "NameNode|DataNode|SecondaryNameNode" || true

echo ""
echo "6. Reporte HDFS (debe aparecer al menos 1 Live datanode):"
hdfs dfsadmin -report 2>&1 | head -30

echo ""
echo "7. Prueba de escritura..."
if echo "test" | hdfs dfs -put - /test.txt 2>/dev/null; then
    echo "   OK: Escritura correcta"
    hdfs dfs -cat /test.txt
    hdfs dfs -rm /test.txt
    echo ""
    echo "=== HDFS está funcionando correctamente ==="
else
    echo "   FALLO: Sigue sin poder escribir. Revisa:"
    echo "   - Que hayas copiado hdfs-site-standalone.xml sobre hdfs-site.xml"
    echo "   - Logs del DataNode: tail -100 \$HADOOP_HOME/logs/hadoop-*-datanode-*.log"
    echo "   - Logs del NameNode: tail -100 \$HADOOP_HOME/logs/hadoop-*-namenode-*.log"
fi
