# Modo Standalone (Solo nodo1)

## Configuración para Trabajar Solo con nodo1

Si prefieres trabajar sin la VM nodo2, puedes adaptar el proyecto para modo standalone (pseudo-distribuido).

## Cambios Necesarios

### 1. Configurar HDFS en Modo Pseudo-Distribuido

Hadoop puede ejecutarse en modo pseudo-distribuido donde todos los servicios corren en el mismo nodo.

**Ventajas:**
- Más simple para desarrollo
- No necesitas mantener una VM
- Perfecto para pruebas y desarrollo

**Configuración:**

Los archivos de configuración ya están preparados para usar `nodo1` como único nodo. Solo necesitas:

1. Asegurarte de que `/etc/hosts` tenga:
```
127.0.0.1   localhost nodo1
```

2. Iniciar servicios en nodo1:
```bash
start-dfs.sh
start-yarn.sh
```

### 2. Adaptar Scripts del Proyecto

Los scripts ya están configurados para usar `nodo1`, así que funcionarán directamente.

### 3. Verificar Configuración

```bash
# Verificar que todos los servicios están en nodo1
jps
# Deberías ver:
# - NameNode
# - DataNode  
# - SecondaryNameNode
# - ResourceManager
# - NodeManager

# Verificar HDFS
hdfs dfs -ls /
```

### 4. Ejecutar Pipeline

El pipeline completo funcionará igual, solo que todo estará en nodo1:

```bash
# Crear topics de Kafka
./ingestion/kafka/create_topics.sh

# Generar datos de prueba
python3 scripts/utils/generate_sample_data.py

# Ejecutar procesamiento
spark-submit --master yarn \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  processing/spark/sql/data_cleaning.py
```

## Notas Importantes

- **Para evaluación**: El proyecto funcionará perfectamente en modo standalone
- **Para producción**: Necesitarías un cluster distribuido real
- **Rendimiento**: En modo standalone es más lento pero suficiente para desarrollo

## Cuando Estés Listo para Cluster Real

Cuando quieras configurar nodo2:
1. Seguir `docs/guides/VM_SETUP.md`
2. Los scripts ya están preparados para trabajar con ambos nodos
3. Solo necesitarás iniciar los servicios en nodo2
