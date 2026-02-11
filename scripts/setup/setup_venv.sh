#!/bin/bash
# Crea un entorno virtual Python en el proyecto para evitar "externally-managed-environment" (PEP 668).
# Uso: bash scripts/setup/setup_venv.sh

set -e
PROJECT_ROOT="$(cd "$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")" && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

echo "=== Entorno virtual en $VENV_DIR ==="

if [ -d "$VENV_DIR" ]; then
    echo "  Ya existe. Para reinstalar: rm -rf $VENV_DIR y vuelve a ejecutar este script."
    echo "  Activar: source $VENV_DIR/bin/activate"
    exit 0
fi

python3 -m venv "$VENV_DIR"
echo "  Creado: $VENV_DIR"

# Instalar dependencias mínimas para generate_sample_data y scripts Python del proyecto
"$VENV_DIR/bin/pip" install --upgrade pip
# kafka-python 2.0.2 en PyPI falla con Python 3.12 (kafka.vendor.six.moves). Usar versión desde GitHub con el fix.
"$VENV_DIR/bin/pip" install "git+https://github.com/dpkp/kafka-python.git"
# Codec snappy (Kafka puede comprimir con snappy; sin esto falla UnsupportedCodecError)
"$VENV_DIR/bin/pip" install python-snappy 2>/dev/null || echo "  (python-snappy opcional: si falla, instala libsnappy-dev y vuelve a ejecutar setup_venv.sh)"

if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "  Instalando requirements.txt..."
    "$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements.txt" || true
fi

echo ""
echo "Para usar el venv:"
echo "  source $VENV_DIR/bin/activate"
echo "  python scripts/utils/generate_sample_data.py"
echo ""
echo "O sin activar:"
echo "  $VENV_DIR/bin/python scripts/utils/generate_sample_data.py"
echo "=== Fin ==="
