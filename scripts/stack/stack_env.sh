# Configuración común para scripts de la pila (stack).
# Las variables pueden sobreescribirse con el entorno.
# Uso: source "$(dirname "$0")/stack_env.sh"  (desde scripts/stack/)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
export PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export HADOOP_HOME="${HADOOP_HOME:-/usr/local/hadoop}"
export NIFI_HOME="${NIFI_HOME:-/opt/nifi}"
export KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"
export SPARK_HOME="${SPARK_HOME:-/opt/spark}"
export HIVE_HOME="${HIVE_HOME:-/opt/hive}"
export AIRFLOW_HOME="${AIRFLOW_HOME:-$HOME/airflow}"

export PATH="${PATH}:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${NIFI_HOME}/bin:${KAFKA_HOME}/bin:${SPARK_HOME}/bin:${HIVE_HOME}/bin"

# Kafka: config por defecto (clásico o KRaft)
KAFKA_CONFIG_CLASSIC="${KAFKA_HOME}/config/server.properties"
KAFKA_CONFIG_KRAFT="${KAFKA_HOME}/config/kraft/server.properties"
if [ -f "$KAFKA_CONFIG_KRAFT" ]; then
  export KAFKA_CONFIG="$KAFKA_CONFIG_KRAFT"
else
  export KAFKA_CONFIG="$KAFKA_CONFIG_CLASSIC"
fi
