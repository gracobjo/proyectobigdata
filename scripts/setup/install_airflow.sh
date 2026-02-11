#!/usr/bin/env bash
# Instala Apache Airflow 2.10.0 con el archivo de constraints oficial.
# Usar desde la raíz del proyecto con el venv activado.
# Ver: https://airflow.apache.org/docs/apache-airflow/2.10.0/installation/installing-from-pypi.html

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Python 3.12: Airflow 2.10.0 no tiene constraints-3.12; usamos constraints-3.11 (compatibles en la práctica).
# Si tienes Python 3.10 o 3.11, puedes cambiar la URL a constraints-3.10.txt o constraints-3.11.txt.
PYVER="${AIRFLOW_CONSTRAINTS_PY:-3.11}"
AIRFLOW_VERSION="2.10.0"
CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYVER}.txt"

echo "=== Instalación de Apache Airflow ${AIRFLOW_VERSION} ==="
echo "Constraints: $CONSTRAINTS_URL"
echo ""

if [[ -z "${VIRTUAL_ENV}" ]]; then
  echo "Activa el venv antes de ejecutar: source venv/bin/activate"
  exit 1
fi

# Instalación reproducible con constraints (solo para este paso; no usar constraints en el resto del proyecto).
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  "apache-airflow-providers-apache-spark==4.9.0" \
  --constraint "$CONSTRAINTS_URL"

echo ""
echo "✓ Airflow ${AIRFLOW_VERSION} instalado. Siguiente: airflow db init && airflow users create ..."
echo "  Ver docs/guides/INSTALLATION.md (sección Airflow) y docs/guides/USAGE.md"
