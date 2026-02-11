# Configuración del Cluster Distribuido

## Arquitectura del Cluster

El proyecto está configurado para ejecutarse en un cluster distribuido con:

- **nodo1** (equipo físico): 
  - NameNode (HDFS)
  - ResourceManager (YARN)
  - Kafka Broker/Controller
  - MongoDB (opcional)
  - NiFi
  - Airflow

- **nodo2** (VM VirtualBox):
  - DataNode (HDFS)
  - NodeManager (YARN)
  - Kafka Broker (opcional, para replicación)

## Configuración de Red

### Requisitos de Conectividad

- nodo1 y nodo2 deben poder comunicarse entre sí
- Verificar conectividad: `ping nodo2` desde nodo1 y viceversa
- Configurar `/etc/hosts` en ambos nodos:

```bash
# En /etc/hosts de ambos nodos
<IP_nodo1>    nodo1
<IP_nodo2>    nodo2
```

### Puertos Necesarios

**nodo1:**
- HDFS NameNode: 9000, 9870
- YARN ResourceManager: 8088
- Kafka: 9092, 9093
- MongoDB: 27017
- NiFi: 8443
- Airflow: 8080

**nodo2:**
- HDFS DataNode: 9864
- YARN NodeManager: 8042
- Kafka: 9092 (si se configura como broker adicional)

## Configuración de HDFS

El NameNode debe estar en **nodo1**. Las configuraciones usan:
- `hdfs://nodo1:9000` como filesystem por defecto
- nodo2 actúa como DataNode

## Configuración de YARN

- ResourceManager en **nodo1**
- NodeManager en **nodo2** (y opcionalmente en nodo1)

## Configuración de Kafka

Kafka está configurado para ejecutarse principalmente en **nodo1**:
- Broker y Controller en nodo1
- Para alta disponibilidad, se puede agregar nodo2 como broker adicional

## Configuración de MongoDB

MongoDB puede ejecutarse en **nodo1** o **nodo2** según preferencia. 
La configuración por defecto asume nodo1.

## Scripts de Configuración

Ver `scripts/setup/configure_cluster.sh` para automatizar la configuración.
