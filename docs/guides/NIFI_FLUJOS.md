# NiFi: procesadores, propiedades y conexiones

Guía para montar en NiFi los flujos de ingesta del proyecto. Puedes **importar** el flujo desde el JSON o **montarlo a mano** siguiendo esta guía.

**Importar en NiFi 2.x:** En un Process Group → **Upload flow definition** → seleccionar **`ingestion/nifi/transport_monitoring_flow.json`**. Luego revisar propiedades (API key OpenWeather, Kafka Brokers, directorio GetFile, Controller Service HDFS para PutHDFS) y habilitar los procesadores.

**Integración IoT:** Para usar sensores reales en lugar de simulaciones, ver **docs/guides/IOT_SENSORES.md** y el flujo de ejemplo **`ingestion/nifi/iot_sensors_flow.json`**.

**Requisitos previos:** Kafka en marcha con topics `raw-data` y `filtered-data`; HDFS con directorio `/user/hadoop/raw`; NiFi 2.6.x instalado y accesible en http://localhost:8443/nifi (o http://nodo1:8443/nifi).

**Fuentes de datos:** Ver **docs/guides/FUENTES_DATOS.md** para obtener/generar datasets. Para logs GPS, ejecuta `python3 scripts/utils/generate_gps_log_file.py -n 200` para crear un fichero de ejemplo en `/home/hadoop/data/gps_logs/`.

---

## Resumen del flujo

| Flujo | Origen | Procesadores principales | Destino |
|-------|--------|---------------------------|---------|
| **1. OpenWeather** | API HTTP | InvokeHTTP → PublishKafka | Kafka `raw-data` |
| **2. FlightRadar24** | API HTTP | InvokeHTTP → PublishKafka | Kafka `raw-data` |
| **3. Logs GPS** | Fichero local | GetFile o TailFile → RouteOnAttribute → PublishKafka + PutHDFS | Kafka `filtered-data` y HDFS `raw` |

---

## Paso 0: Process Group principal

1. En el canvas de NiFi, clic derecho → **Add** → **Process Group**.
2. Nombre: `Transport Monitoring`.
3. Entra dentro del grupo (doble clic) para añadir los procesadores de cada flujo.

---

## Flujo 1: Ingesta API OpenWeather

**Objetivo:** Llamar a la API de OpenWeather cada X minutos y enviar el JSON a Kafka `raw-data`.

### Procesadores a añadir (en este orden)

| Orden | Procesador | Tipo (buscar en Add) |
|-------|------------|----------------------|
| 1 | Obtener datos | **InvokeHTTP** |
| 2 | Enviar a Kafka | **PublishKafka_2_6** (o **PublishKafkaRecord_2_6** si prefieres Record) |

### Propiedades a configurar

**InvokeHTTP**

| Propiedad | Valor | Notas |
|----------|--------|--------|
| **HTTP Method** | GET | |
| **Remote URL** | `https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid=<TU_API_KEY>&units=metric` | Sustituir `<TU_API_KEY>` por tu API key de OpenWeather. |
| **Connection Timeout** | 10 secs | |
| **Read Timeout** | 10 secs | |
| **Run Schedule** | 5 min | Para no exceder límites de la API. |

(Opcional) **Content-Type**: no obligatorio para GET; si usas atributos para el topic, puedes usar **PutAttribute** después.

**PublishKafka_2_6**

| Propiedad | Valor | Notas |
|----------|--------|--------|
| **Kafka Brokers** | `localhost:9092` | O `nodo1:9092` si Kafka está en otro host. |
| **Topic Name** | `raw-data` | Debe existir el topic (script `ingestion/kafka/create_topics.sh`). |
| **Message Demarcator** | (vacío o default) | Un mensaje por flowfile. |
| **Delivery Guarantee** | best effort | O `guarantee single packet` si quieres at-least-once. |

Si el procesador exige **Security Protocol**, en entorno local suele ser `PLAINTEXT`.

### Conexiones

| Origen | Puerto de salida | Destino | Puerto de entrada |
|--------|-------------------|----------|-------------------|
| InvokeHTTP | **success** | PublishKafka_2_6 | **input** |
| InvokeHTTP | **failure** | (opcional) conexión a un **HandleHttpRequest** o **PutFile** para retry/log. |

---

## Flujo 2: Ingesta API FlightRadar24

**Objetivo:** Llamar a la API de FlightRadar24 (o un endpoint de prueba) cada 1 minuto y enviar a Kafka `raw-data`.

### Procesadores a añadir

| Orden | Procesador | Tipo |
|-------|------------|------|
| 1 | Obtener datos | **InvokeHTTP** |
| 2 | Enviar a Kafka | **PublishKafka_2_6** |

### Propiedades

**InvokeHTTP**

| Propiedad | Valor |
|----------|--------|
| **HTTP Method** | GET |
| **Remote URL** | URL de la API (FlightRadar24 suele requerir autenticación; en pruebas se puede usar un mock o `https://httpbin.org/get`). |
| **Run Schedule** | 1 min |

**PublishKafka_2_6**

| Propiedad | Valor |
|----------|--------|
| **Kafka Brokers** | `localhost:9092` |
| **Topic Name** | `raw-data` |

### Conexiones

- **InvokeHTTP** → **success** → **PublishKafka_2_6** → input.

---

## Flujo 3: Procesamiento de logs GPS (ficheros → Kafka + HDFS)

**Objetivo:** Leer ficheros de log GPS (p. ej. generados por `generate_sample_data.py` guardados en disco, o un directorio que simule la entrada), filtrar si hace falta y enviar a **Kafka** topic `filtered-data` y copia raw a **HDFS** `/user/hadoop/raw`.

### Procesadores a añadir

| Orden | Procesador | Tipo |
|-------|------------|------|
| 1 | Leer ficheros | **GetFile** (o **TailFile** si son logs que se escriben en tiempo real) |
| 2 | Filtrar / encaminar | **RouteOnAttribute** (opcional) |
| 3 | Enviar a Kafka | **PublishKafka_2_6** |
| 4 | Copia raw a HDFS | **PutHDFS** |

### Propiedades

**GetFile**

| Propiedad | Valor |
|----------|--------|
| **Input Directory** | `/home/hadoop/data/gps_logs` (o la ruta donde se escriban los JSON de GPS). Crear el directorio si no existe. |
| **File Filter** | `.*\.json` o `*.json` (según versión) |
| **Keep Source File** | false (mueve) o true (copia) |
| **Run Schedule** | 5 secs o según necesidad |

**RouteOnAttribute** (opcional)

- Añadir una propiedad de ruta, p. ej. `valid` = `${literal(true):equals('true')}` para dejar pasar todo, o una condición sobre `${filename}` / contenido para separar válidos de no válidos.
- Salidas típicas: **matched** → PublishKafka y PutHDFS; **unmatched** → otro grupo o Drop.

**PublishKafka_2_6**

| Propiedad | Valor |
|----------|--------|
| **Kafka Brokers** | `localhost:9092` |
| **Topic Name** | `filtered-data` |

**PutHDFS**

| Propiedad | Valor |
|----------|--------|
| **Hadoop Configuration Resources** | Fichero(s) core-site.xml y hdfs-site.xml (o directorio `$HADOOP_HOME/etc/hadoop`). En NiFi 2.x suele usarse un **Controller Service** tipo **HadoopConfigurationProvider** o **StandardHadoopConfigurationProvider** que apunte a esos ficheros. |
| **Directory** | `/user/hadoop/raw` |
| **Conflict Resolution** | replace o ignore (según si quieres sobrescribir) |

**Configuración HDFS en NiFi:** En el Process Group o a nivel raíz, **Controller Settings** → **Controller Services** → añadir **StandardHadoopConfigurationProvider** (o equivalente) y configurar con la ruta de `core-site.xml` y `hdfs-site.xml` (p. ej. `/opt/hadoop/etc/hadoop`). Luego en PutHDFS seleccionar ese servicio en la propiedad correspondiente (p. ej. **Hadoop Configuration Resources** si acepta el servicio).

Si NiFi corre en el mismo nodo que HDFS, a veces basta con tener `HADOOP_CONF_DIR` en el entorno de NiFi y referenciar el directorio en el Controller Service.

### Conexiones (Flujo 3)

| Origen | Puerto | Destino |
|--------|--------|---------|
| GetFile | success | RouteOnAttribute (si se usa) |
| RouteOnAttribute | matched | PublishKafka_2_6 (input) |
| RouteOnAttribute | matched | PutHDFS (input) |

Si no usas RouteOnAttribute:

- **GetFile** → success → **PublishKafka_2_6**
- **GetFile** → success → **PutHDFS**

(Un mismo flowfile puede ir a dos procesadores usando la misma relación de conexión desde GetFile a ambos; NiFi envía una copia a cada destino.)

---

## Valores comunes a revisar

| Componente | Propiedad / Dónde | Valor típico |
|------------|-------------------|--------------|
| Kafka | Brokers | `localhost:9092` o `nodo1:9092` |
| Kafka | Topic datos crudos | `raw-data` |
| Kafka | Topic datos filtrados | `filtered-data` |
| HDFS | Directorio raw | `/user/hadoop/raw` |
| HDFS | Namenode (core-site / hdfs-site) | `hdfs://localhost:9000` o `hdfs://nodo1:9000` |
| NiFi | Usuario para HDFS | Debe tener permisos de escritura en `/user/hadoop/raw` (ver TROUBLESHOOTING.md) |

---

## Orden recomendado al montar el flujo

1. Crear el **Process Group** "Transport Monitoring".
2. **Flujo 1:** Añadir InvokeHTTP + PublishKafka_2_6, configurar propiedades y conectar success → PublishKafka.
3. **Flujo 2:** Igual con el segundo InvokeHTTP y su PublishKafka (mismo topic `raw-data`).
4. **Flujo 3:** Añadir GetFile (o TailFile), opcionalmente RouteOnAttribute, PublishKafka_2_6 y PutHDFS; configurar Controller Service de HDFS y propiedades; conectar GetFile a Kafka y a PutHDFS.
5. **Habilitar** cada procesador (clic derecho → Start).
6. Comprobar en Kafka que llegan mensajes: `kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw-data --from-beginning --max-messages 5`.

---

## Manejo de errores y buenas prácticas

- **Back-pressure:** Por defecto NiFi aplica back-pressure; en las colas (conexiones) se puede ajustar el umbral de "back pressure object threshold" si hay muchos flowfiles.
- **Retry:** En InvokeHTTP, configurar **Penalize** o **Retry** en la relación **failure** para reintentar sin saturar.
- **Alertas:** Opcionalmente conectar **failure** de InvokeHTTP o de PublishKafka a un procesador que envíe correo (SendEmail) o escriba en log (PutSlack, etc.) si el proyecto lo requiere.
- **Permisos HDFS:** Si PutHDFS falla por permisos, crear `/user/hadoop/raw` y dar permisos (p. ej. `hdfs dfs -chmod 775 /user/hadoop/raw` y que el usuario de NiFi coincida o esté en el grupo adecuado). Ver **docs/guides/TROUBLESHOOTING.md** (sección NiFi y HDFS).

---

## Referencias

- **Ingesta general:** `ingestion/nifi/README.md`
- **Topics Kafka:** `ingestion/kafka/create_topics.sh`
- **Configuración NiFi/Kafka/HDFS:** `docs/guides/CONFIGURATION.md`
- **Problemas NiFi/HDFS:** `docs/guides/TROUBLESHOOTING.md`
- **Arquitectura:** `docs/architecture/ARCHITECTURE.md`
