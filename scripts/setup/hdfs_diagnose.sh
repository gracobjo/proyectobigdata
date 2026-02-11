#!/bin/bash
# Diagnóstico cuando HDFS muestra "0 datanode(s) running"
# Comprueba qué ficheros está usando realmente Hadoop y si tienen 127.0.0.1 (correcto) o 0.0.0.0 (incorrecto).

HADOOP_CONF="${HADOOP_HOME:-/usr/local/hadoop}/etc/hadoop"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")"
PROJECT_CONF="$PROJECT_ROOT/config/hdfs/hdfs-site-standalone.xml"

echo "=== Diagnóstico HDFS ==="
echo ""

echo "1. Procesos Java (NameNode, DataNode):"
jps | grep -E "NameNode|DataNode|SecondaryNameNode" || echo "   Ninguno encontrado"
echo ""

echo "2. /etc/hosts - línea de nodo1 (debe ser 127.0.0.1 para standalone):"
grep -E "nodo1|127\.0\.0\.1" /etc/hosts 2>/dev/null || echo "   No se pudo leer /etc/hosts"
echo ""

echo "3. Resolución de 'nodo1':"
getent hosts nodo1 2>/dev/null || echo "   getent no disponible"
echo ""

echo "4. core-site.xml - fs.defaultFS (debe ser hdfs://127.0.0.1:9000 o hdfs://localhost:9000 en standalone):"
grep -A1 "fs.defaultFS" "$HADOOP_CONF/core-site.xml" 2>/dev/null || echo "   No encontrado"
echo ""

echo "5. hdfs-site.xml EN TU MÁQUINA - propiedades críticas (deben ser 127.0.0.1, NO 0.0.0.0):"
for prop in dfs.namenode.rpc-address dfs.namenode.http-address dfs.namenode.secondary.http-address dfs.datanode.address dfs.datanode.http.address dfs.replication; do
  val=$(grep -A1 "<name>$prop</name>" "$HADOOP_CONF/hdfs-site.xml" 2>/dev/null | grep "<value>" | sed 's/.*<value>\(.*\)<\/value>.*/\1/')
  if [ -n "$val" ]; then
    echo "   $prop = $val"
  fi
done
echo ""

echo "6. ¿Coincide con el fichero del proyecto? (diff hdfs-site.xml vs hdfs-site-standalone.xml):"
if [ -f "$PROJECT_CONF" ] && [ -f "$HADOOP_CONF/hdfs-site.xml" ]; then
  if diff -q "$PROJECT_CONF" "$HADOOP_CONF/hdfs-site.xml" >/dev/null 2>&1; then
    echo "   Sí: el hdfs-site.xml de Hadoop ES IGUAL al del proyecto (config correcta)."
  else
    echo "   No: son distintos. Para aplicar la config del proyecto ejecuta:"
    echo "   sudo cp $PROJECT_CONF $HADOOP_CONF/hdfs-site.xml"
    echo "   y reinicia HDFS (stop datanode, secondarynamenode, namenode; start namenode; start datanode; start secondarynamenode)."
  fi
else
  echo "   (no se pudo comparar: $PROJECT_CONF o $HADOOP_CONF/hdfs-site.xml no encontrado)"
fi
echo ""

echo "7. Puertos en escucha (9000=NN RPC, 9864=DN HTTP, 9866=DN data):"
ss -tlnp 2>/dev/null | grep -E "9000|9864|9866" || netstat -tlnp 2>/dev/null | grep -E "9000|9864|9866" || echo "   No se pudo listar"
echo ""

echo "8. Últimas líneas del log del DataNode (errores/registro):"
DN_LOG=$(ls -t ${HADOOP_HOME:-/usr/local/hadoop}/logs/hadoop-*-datanode-*.log 2>/dev/null | head -1)
if [ -n "$DN_LOG" ]; then
    echo "   Archivo: $DN_LOG"
    tail -40 "$DN_LOG" | grep -E "register|Registration|ERROR|Exception|Started|bind|127.0.0.1|0\.0\.0\.0|namenode" || tail -15 "$DN_LOG"
else
    echo "   No se encontró log de DataNode"
fi
echo ""

echo "9. Últimas líneas del log del NameNode (datanode/registration):"
NN_LOG=$(ls -t ${HADOOP_HOME:-/usr/local/hadoop}/logs/hadoop-*-namenode-*.log 2>/dev/null | head -1)
if [ -n "$NN_LOG" ]; then
    echo "   Archivo: $NN_LOG"
    tail -60 "$NN_LOG" | grep -E "datanode|DataNode|register|Registration|ERROR" || tail -10 "$NN_LOG"
else
    echo "   No se encontró log de NameNode"
fi
echo ""

echo "10. hdfs dfsadmin -report (resumen):"
hdfs dfsadmin -report 2>&1 | head -25
echo ""

# Si hay error de clusterID, sugerir fix
if grep -q "Incompatible clusterIDs\|All specified directories have failed to load" "${DN_LOG:-/dev/null}" 2>/dev/null; then
    echo ">>> DETECTADO: ClusterID incompatible entre NameNode y DataNode."
    echo ">>> Solución: ejecuta:  bash $PROJECT_ROOT/scripts/setup/hdfs_fix_clusterid.sh"
    echo ""
fi

echo "=== Fin diagnóstico ==="
