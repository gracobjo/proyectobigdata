# Estado de los Terminales y Qué Hacer

## Situación Actual

### ❌ Terminal 2 (data_cleaning.py) - FALLÓ
**Error:** `Connection refused` a HDFS (localhost:9000)
**Causa:** HDFS no estaba corriendo
**Estado:** El proceso terminó con error

### ❌ Terminal 3 (delay_analysis.py) - FALLÓ  
**Error:** `Connection refused` a HDFS (localhost:9000)
**Causa:** HDFS no estaba corriendo
**Estado:** El proceso terminó con error

### ✅ HDFS - AHORA CORRIENDO
**Estado:** NameNode y DataNode activos
**Modo seguro:** Desactivado
**Listo para usar:** Sí

---

## Qué Hacer Ahora

### Opción 1: Reiniciar los Terminales (Recomendado)

Como HDFS ahora está corriendo, puedes ejecutar de nuevo los scripts:

**Terminal 2 (Limpieza):**
```bash
bash scripts/run/02_data_cleaning.sh
```

**Terminal 3 (Análisis de retrasos):**
```bash
bash scripts/run/03_delay_analysis.sh
```

Estos scripts deberían funcionar ahora porque HDFS está disponible.

---

### Opción 2: Verificar Estado Antes de Continuar

Antes de ejecutar los scripts, verifica que todo esté listo:

```bash
# Verificar HDFS
jps | grep -E "NameNode|DataNode"
hdfs dfsadmin -report | head -5

# Verificar Kafka
jps | grep Kafka
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Verificar MongoDB
pgrep -f mongod || docker ps | grep mongo
```

---

## Orden Completo de Ejecución (Actualizado)

### ✅ Paso 0: Arrancar HDFS (YA HECHO)
```bash
bash scripts/run/00_start_hdfs.sh
```
**Estado:** ✅ Completado

### ✅ Paso 1: Generar Datos
```bash
bash scripts/run/01_generate_data.sh
```
**Estado:** Verificar si ya se ejecutó

### ⚠️ Paso 2: Limpieza (REINICIAR)
```bash
bash scripts/run/02_data_cleaning.sh
```
**Estado:** ❌ Falló anteriormente, necesita reiniciarse

### ⚠️ Paso 3: Análisis de Retrasos (REINICIAR)
```bash
bash scripts/run/03_delay_analysis.sh
```
**Estado:** ❌ Falló anteriormente, necesita reiniciarse

### ⏸️ Paso 4: Consumidor MongoDB (ESPERAR)
```bash
bash scripts/run/04_mongodb_consumer.sh
```
**Estado:** Esperar a que Terminal 3 genere datos

---

## Preguntas Frecuentes

### ¿Necesito cerrar los terminales que fallaron?
**No necesariamente.** Los procesos ya terminaron (fallaron), así que puedes:
- Usar las mismas terminales para ejecutar de nuevo los scripts
- O abrir nuevas terminales

### ¿Los datos generados en Terminal 1 se perdieron?
**No.** Los datos en Kafka (`raw-data`) persisten aunque los scripts fallen. Puedes verificar:
```bash
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic raw-data \
  --from-beginning \
  --max-messages 3
```

### ¿Necesito regenerar los datos?
**Solo si:** El topic `raw-data` está vacío. Verifica primero:
```bash
/opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic raw-data
```

### ¿Qué pasa con los checkpoints de Spark?
Los checkpoints en HDFS pueden tener información de la ejecución fallida. Si quieres empezar limpio:
```bash
# Eliminar checkpoints (opcional)
hdfs dfs -rm -r /user/hadoop/checkpoints/cleaning 2>/dev/null
hdfs dfs -rm -r /user/hadoop/checkpoints/delay_hive 2>/dev/null
hdfs dfs -rm -r /user/hadoop/checkpoints/delay_kafka 2>/dev/null
```

**Nota:** Esto hará que los scripts procesen desde el principio. Si quieres continuar desde donde se quedaron, no elimines los checkpoints.

---

## Resumen Rápido

1. ✅ HDFS está corriendo (problema resuelto)
2. ⚠️ Terminal 2 y 3 fallaron pero pueden reiniciarse
3. ✅ Los datos en Kafka persisten
4. ✅ Puedes ejecutar los scripts de nuevo ahora

**Siguiente paso:** Ejecutar Terminal 2 de nuevo con `bash scripts/run/02_data_cleaning.sh`
