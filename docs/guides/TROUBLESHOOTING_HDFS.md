# Troubleshooting HDFS - Problema DataNode no detectado

## Problema Actual

El NameNode no detecta el DataNode aunque ambos procesos están corriendo. Error:
```
There are 0 datanode(s) running and 0 node(s) are excluded in this operation.
```

## Diagnóstico

- ✅ NameNode corriendo (puerto 9000, 9870)
- ✅ DataNode corriendo (puerto 9864)
- ❌ NameNode no detecta DataNode
- ❌ No se puede escribir en HDFS

## Solución Temporal: Usar Sistema de Archivos Local

Mientras se resuelve el problema de HDFS, podemos usar el sistema de archivos local para las tablas:

### Modificar scripts para usar file:// en lugar de hdfs://

Los scripts pueden funcionar con archivos locales temporalmente:

```python
# En lugar de:
LOCATION 'hdfs://localhost:9000/user/hive/warehouse/master_routes'

# Usar temporalmente:
LOCATION 'file:///tmp/hive_warehouse/master_routes'
```

## Solución Permanente: Corregir Configuración HDFS

### 1. Verificar que ambos servicios usen la misma IP

```bash
# Verificar core-site.xml
grep fs.defaultFS $HADOOP_HOME/etc/hadoop/core-site.xml

# Debe ser: hdfs://localhost:9000 o hdfs://127.0.0.1:9000
```

### 2. Verificar hdfs-site.xml

```bash
# Verificar que no haya IPs hardcodeadas
grep -E "192.168|nodo1" $HADOOP_HOME/etc/hadoop/hdfs-site.xml
```

### 3. Reiniciar servicios completamente

```bash
# Detener todo
hdfs --daemon stop datanode
hdfs --daemon stop namenode

# Esperar
sleep 5

# Iniciar en orden
hdfs --daemon start namenode
sleep 5
hdfs --daemon start datanode
sleep 5

# Verificar
hdfs dfsadmin -report
```

### 4. Verificar logs

```bash
# Logs del NameNode
tail -f $HADOOP_HOME/logs/hadoop-*-namenode-*.log

# Logs del DataNode  
tail -f $HADOOP_HOME/logs/hadoop-*-datanode-*.log
```

## Alternativa: Continuar sin HDFS para Desarrollo

Para desarrollo y pruebas, podemos:
1. Usar sistema de archivos local para tablas
2. Usar Kafka para streaming (ya funciona)
3. Usar Spark en modo local sin YARN

Esto permite avanzar con el proyecto mientras se resuelve HDFS.
