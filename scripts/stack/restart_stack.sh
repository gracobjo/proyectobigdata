#!/bin/bash
# Reinicia la pila: primero apaga todos los componentes y luego los arranca.
# Uso: bash scripts/stack/restart_stack.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================="
echo "  Reinicio de la pila - Proyecto BigData"
echo "=============================================="
echo ""

echo "Fase 1: Apagado..."
bash "$SCRIPT_DIR/stop_stack.sh"
echo ""
echo "Esperando 5 segundos antes de arrancar..."
sleep 5
echo ""

echo "Fase 2: Arranque..."
bash "$SCRIPT_DIR/start_stack.sh"
echo ""

echo "Estado final:"
bash "$SCRIPT_DIR/status_stack.sh"
