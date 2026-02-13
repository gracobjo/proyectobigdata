# Dockerizar el proyecto Big Data

Stack completo (Hadoop, NiFi, Spark, Hive, MongoDB, Airflow, API) en Docker para **pruebas locales** y opciones para **Railway**, **Vercel** o **AWS (S3/ECS)**.

## Requisitos

- Docker Engine 20.10+
- Docker Compose v2 (`docker compose`)

## Uso rápido

### 1. Solo servicios de apoyo + API (ligero, ideal para Railway o pruebas rápidas)

```bash
cd docker
docker compose --profile light up -d
```

Levanta: **Kafka**, **MongoDB**, **API REST** y un init que crea los topics de Kafka (`raw-data`, `filtered-data`, `alerts`).

- **API:** http://localhost:5000/docs  
- **MongoDB:** localhost:27017  
- **Kafka:** localhost:9092 (desde el host; desde contenedores usar `kafka:9092`)

### 2. Stack completo (Hadoop, NiFi, Hive, Airflow, API)

```bash
cd docker
docker compose --profile full up -d
```

Además de lo anterior, levanta:

- **HDFS (NameNode + DataNode):** http://localhost:9870 — RPC `hdfs://namenode:9000`
- **YARN (ResourceManager):** puerto 8088
- **NiFi:** https://localhost:8443 (o http://localhost:8080 según imagen)
- **Hive Metastore:** thrift://hive-metastore:9083
- **Airflow:** http://localhost:8081 (usuario `admin` / contraseña `admin` tras el primer init)

La primera vez con perfil `full` puede tardar varios minutos (descarga de imágenes e init de Airflow).

### 3. Crear topics Kafka a mano (si el init no se ejecutó)

```bash
docker compose exec kafka kafka-topics.sh --create --if-not-exists \
  --bootstrap-server localhost:9092 --topic raw-data --partitions 3 --replication-factor 1
docker compose exec kafka kafka-topics.sh --create --if-not-exists \
  --bootstrap-server localhost:9092 --topic filtered-data --partitions 3 --replication-factor 1
docker compose exec kafka kafka-topics.sh --create --if-not-exists \
  --bootstrap-server localhost:9092 --topic alerts --partitions 1 --replication-factor 1
```

### 4. Parar y eliminar volúmenes

```bash
docker compose --profile full down
docker compose --profile full down -v   # borra datos en volúmenes
```

---

## Desplegar en Railway (pruebas)

**Railway** tiene límites de memoria y no está pensado para un cluster Hadoop completo. Opciones:

### Opción A: Solo la API + MongoDB/Kafka en Railway

1. **Subir el repo** a GitHub (ya lo tienes).
2. En **Railway**, crear un proyecto y añadir:
   - **Servicio 1:** "New → GitHub Repo" → seleccionar el repo. Como **Dockerfile** usa `docker/Dockerfile.api` (en Railway: Root Directory no aplica al path del Dockerfile; configura **Dockerfile path** = `docker/Dockerfile.api` y **Build context** = raíz del repo, o build desde raíz con `docker build -f docker/Dockerfile.api .`).
   - **Servicio 2:** MongoDB (Railway tiene plugin MongoDB o usa Mongo Atlas).
   - **Servicio 3 (opcional):** Kafka (Railway no tiene Kafka nativo; puedes usar un add-on de terceros o **Upstash Kafka** y poner `KAFKA_BOOTSTRAP_SERVERS` en variables de la API).

3. En la API, definir variables de entorno en Railway:
   - `MONGO_URI` = URI de tu MongoDB (ej. `mongodb+srv://...` si Atlas, o la URL interna de Railway si MongoDB en el mismo proyecto).
   - `DB_NAME` = `transport_db`.

4. Desplegar. La API quedará en una URL tipo `https://xxx.railway.app`. Swagger en `/docs`.

### Opción B: Docker Compose “light” en un solo servicio

Railway puede desplegar un **compose** con un único servicio; no suele ejecutar un compose con varios contenedores. Por tanto, para “todo en uno” en Railway no es viable el stack completo. Lo realista es: **un servicio = API** (Dockerfile.api) y MongoDB/Kafka externos (Railway plugins o externos).

---

## Desplegar en Vercel (solo la API, serverless)

**Vercel** es una plataforma serverless (funciones por invocación). No puede ejecutar Hadoop, NiFi, Kafka ni Airflow; solo es adecuada para exponer la **API REST** (FastAPI) como funciones serverless.

### Qué se despliega

- Solo la **API** (`/health`, `/vehicles`, `/delays`, `/bottlenecks`, `/routes/recommend`, Swagger en `/docs`).
- **MongoDB** debe ser externo (por ejemplo **MongoDB Atlas**). En Vercel configuras la variable `MONGO_URI` con la URI de Atlas.

### Pasos

1. **MongoDB Atlas** (gratis): crea un cluster, obtén la URI de conexión (ej. `mongodb+srv://usuario:pass@cluster.xxxxx.mongodb.net/transport_db`).

2. **Conectar el repo a Vercel**: en [vercel.com](https://vercel.com) → New Project → Import Git Repository (tu repo de GitHub).

3. **Configuración del proyecto** en Vercel:
   - **Root Directory:** dejar por defecto (raíz del repo).
   - **Framework Preset:** Other (o detectado).
   - **Build Command:** opcional; el proyecto usa `requirements-vercel.txt` para no instalar Spark/Airflow (ver `vercel.json`).
   - **Variables de entorno** (Settings → Environment Variables):
     - `MONGO_URI` = tu URI de MongoDB Atlas (ej. `mongodb+srv://...`).
     - `DB_NAME` = `transport_db`.

4. **Desplegar**: Vercel usará `index.py` (punto de entrada que expone la app FastAPI) y `requirements-vercel.txt` para las dependencias ligeras. La API quedará en `https://tu-proyecto.vercel.app`. Swagger en `https://tu-proyecto.vercel.app/docs`.

### Archivos del repo usados por Vercel

- `index.py` — entrada que expone la app FastAPI para Vercel.
- `vercel.json` — excluye carpetas pesadas (docker, processing, ingestion, etc.) para no superar el límite de tamaño.
- `requirements-vercel.txt` — dependencias mínimas (pymongo, fastapi, uvicorn, scikit-learn, joblib, networkx); no incluye Spark ni Airflow.

### Limitaciones

- **Cold starts**: la primera petición tras un tiempo inactivo puede tardar unos segundos.
- **Timeout**: las funciones tienen límite de tiempo (p. ej. 10–60 s según plan); el endpoint `/routes/recommend` con `use_ml=True` debe seguir siendo rápido.
- **Solo lectura sobre MongoDB**: el pipeline (Kafka, Spark, Hive, etc.) se ejecuta en otro entorno; en Vercel solo se sirve la API que consulta MongoDB.

---

## Subir a S3 (artefactos y backups)

**S3** es almacenamiento de objetos; no ejecuta contenedores. Puedes usarlo para:

1. **Guardar backups** de MongoDB, HDFS (exportados) o logs.
2. **Almacenar artefactos** de build (p. ej. imágenes Docker exportadas) si tu CI/CD lo usa.
3. **Documentación / entregables** en un bucket (por ejemplo el PDF del proyecto).

Ejemplo desde tu máquina (con AWS CLI y credenciales configuradas):

```bash
# Backup de MongoDB
docker compose exec mongodb mongodump --archive --db transport_db | gzip > backup.gz
aws s3 cp backup.gz s3://TU_BUCKET/backups/mongo-$(date +%Y%m%d).gz

# Subir documentación
aws s3 sync docs/ s3://TU_BUCKET/docs/ --exclude "*.git*"
```

Para **ejecutar el stack en AWS** (no solo S3):

- **ECS (Fargate)** o **EKS**: usa el mismo `docker-compose.yml` como referencia y define cada servicio como tarea/servicio (MongoDB gestionado con DocumentDB o Mongo en ECS; Kafka con MSK).
- **EC2**: en una instancia puedes instalar Docker y ejecutar `docker compose --profile full up -d` igual que en local (ajustando memoria y puertos).

---

## Resumen de puertos (stack full)

| Servicio      | Puerto(s)        | URL / uso                          |
|--------------|------------------|------------------------------------|
| HDFS NameNode| 9870, 9000       | http://localhost:9870, hdfs://namenode:9000 |
| Kafka        | 9092             | bootstrap: localhost:9092 o kafka:9092      |
| MongoDB      | 27017            | mongodb://localhost:27017          |
| NiFi         | 8443, 8080       | https://localhost:8443             |
| Hive Metastore | 9083           | thrift://hive-metastore:9083       |
| Airflow      | 8081 → 8080      | http://localhost:8081              |
| API          | 5000             | http://localhost:5000/docs         |

## Ejecutar jobs Spark / pipeline desde el host

Con el perfil `full` activo, HDFS está en `hdfs://namenode:9000`. Desde tu máquina necesitas que el host resuelva `namenode` (p. ej. en `/etc/hosts`: `127.0.0.1 namenode`) o ejecutar los jobs **dentro de un contenedor** que tenga Spark y red compartida con el compose:

```bash
# Ejemplo: ejecutar un script Spark dentro de la red (requiere imagen con Spark + proyecto)
docker compose run --rm -e HDFS_NAMENODE=namenode -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 spark-client spark-submit --master local[*] ...
```

Para tener ese “spark-client” tendrías que añadir un `Dockerfile.spark` que copie el código y tenga Spark; es opcional y se puede documentar en una siguiente iteración.

## Referencias

- [docs/README.md](../docs/README.md) — Índice de documentación del proyecto.
- [docs/scripts/stack-arranque-pila.md](../docs/scripts/stack-arranque-pila.md) — Arranque de la pila sin Docker (cluster real).
