#!/bin/bash
# Terminal 5: Verificar datos en MongoDB
# Uso: bash scripts/run/05_verify_mongodb.sh
# Puede ejecutarse múltiples veces para verificar progreso

cd /home/hadoop/Documentos/ProyectoBigData
source venv/bin/activate

echo "=== Verificando datos en MongoDB ==="
echo ""

python storage/mongodb/verify_data.py
