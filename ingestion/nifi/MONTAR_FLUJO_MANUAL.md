# Montar el flujo a mano en NiFi (cuando la importación falla)

En **NiFi 2.7.x** la opción "Upload flow definition" puede dar *"An unexpected error has occurred"* (bug conocido). Esta guía permite montar el flujo en unos minutos sin importar JSON.

**Enfoque del proyecto:** flujo principal = **Logs GPS** (GetFile → PublishKafka `filtered-data`). OpenWeather y FlightRadar24 son opcionales.

## Requisitos

- Kafka en marcha con topic **`filtered-data`** (y opcionalmente `raw-data`).
- Directorio de logs GPS: `mkdir -p /home/hadoop/data/gps_logs`
- Opcional: datos de prueba: `python3 scripts/utils/generate_gps_log_file.py -n 100`

---

## Paso 1: Crear el Process Group

1. En el canvas de NiFi: clic derecho → **Add** → **Process Group**.
2. Clic derecho sobre el nuevo grupo → **Configure** → nombre: **Transport Monitoring** (o el que prefieras) → **Apply**.
3. **Doble clic** en el grupo para entrar dentro.

---

## Paso 2: Flujo principal — Logs GPS → Kafka

1. Añade **GetFile** (Add → Processor → buscar GetFile).
2. Configura GetFile:
   - **Input Directory**: `/home/hadoop/data/gps_logs`
   - **File Filter**: `.*\.jsonl?` (o `.*\.json`)
   - **Keep Source File**: false
   - **Polling Interval**: `5 sec`
   - **Apply**.
3. Añade **PublishKafka** (o **PublishKafka_2_6**).
4. Configura PublishKafka:
   - **Kafka Brokers**: `localhost:9092`
   - **Topic Name**: `filtered-data`
   - **Apply**.
5. Conecta: GetFile (relación **success**) → PublishKafka → **Add**.

Con esto tienes el flujo GPS listo. Opcionalmente continúa con los pasos siguientes para OpenWeather y FlightRadar24.

---

## Paso 3 (opcional): Flujo OpenWeather → Kafka

1. Arrastra un procesador al canvas (icono **+** o clic derecho → **Add** → **Processor**).
2. Busca **InvokeHTTP** → selecciónalo → **Add**.
3. Clic derecho en InvokeHTTP → **Configure** (o doble clic):
   - **HTTP Method**: GET
   - **Remote URL**: `https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid=REPLACE_WITH_API_KEY&units=metric` (cambia `REPLACE_WITH_API_KEY` por tu API key).
   - **Run Schedule**: `5 min`
   - En **Relationships** marca **failure** y **retry** como "auto-terminate" si quieres.
   - **Apply**.
4. Añade otro procesador: busca **PublishKafka** (o **PublishKafka_2_6**) → **Add**.
5. Configura PublishKafka:
   - **Kafka Brokers**: `localhost:9092`
   - **Topic Name**: `raw-data`
   - **Apply**.
6. Conectar: arrastra desde el **cuadradito** de salida de InvokeHTTP (relación **success**) hasta el PublishKafka → **Add**.

---

## Paso 4 (opcional): Flujo FlightRadar24 (o mock) → Kafka

1. Añade otro **InvokeHTTP**.
2. Configura:
   - **Remote URL**: `https://httpbin.org/get` (mock; o la URL real de FlightRadar24 si tienes clave).
   - **Run Schedule**: `1 min`
   - **Apply**.
3. Añade otro **PublishKafka**:
   - **Kafka Brokers**: `localhost:9092`
   - **Topic Name**: `raw-data`
   - **Apply**.
4. Conecta: InvokeHTTP (**success**) → PublishKafka.

---

## Paso 5 (opcional): PutHDFS para copia raw a HDFS

1. Añade **PutHDFS**.
2. Configura:
   - **Directory**: `/user/hadoop/raw`
   - **Hadoop Configuration Resources** (o Controller Service): apunta a tu `core-site.xml` y `hdfs-site.xml` (o configura un Controller Service de tipo **HadoopConfigurationProvider** en el grupo y asígnalo aquí).
   - **Apply**.
3. Conecta: GetFile (**success**) → PutHDFS (así GetFile envía a Kafka y a HDFS).

---

## Paso 6: Arrancar los procesadores

1. Selecciona los procesadores que quieras (para el flujo GPS: GetFile y PublishKafka filtered-data).
2. Clic derecho → **Start** (o el botón play en la barra).
3. Comprueba en Kafka que llegan mensajes (flujo GPS → topic `filtered-data`):
   ```bash
   kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic filtered-data --from-beginning --max-messages 3
   ```

---

## Resumen visual

**Flujo principal (GPS):**
```
[GetFile GPS Logs] --success--> [PublishKafka filtered-data] --> topic filtered-data
```

Opcional: misma salida GetFile → PutHDFS → `/user/hadoop/raw`. Otros flujos:
```
[InvokeHTTP OpenWeather] --success--> [PublishKafka] --> raw-data
[InvokeHTTP FlightRadar] --success--> [PublishKafka] --> raw-data
```

---

## Referencias

- Propiedades detalladas y troubleshooting: **docs/guides/NIFI_FLUJOS.md**
- Fuentes de datos: **docs/guides/FUENTES_DATOS.md**
