#!/bin/bash
# Script para configurar variables de entorno del proyecto

echo "=== Configurando Variables de Entorno ==="
echo ""

# Detectar instalaciones
HADOOP_DIR="/usr/local/hadoop"
SPARK_DIR=$(find /opt /usr/local -maxdepth 2 -type d -name "spark*" 2>/dev/null | head -1)
KAFKA_DIR=$(find /opt /usr/local -maxdepth 2 -type d -name "kafka*" 2>/dev/null | head -1)
NIFI_DIR=$(find /opt /usr/local -maxdepth 2 -type d -name "nifi*" 2>/dev/null | head -1)
HIVE_DIR=$(find /opt /usr/local -maxdepth 2 -type d -name "hive*" 2>/dev/null | head -1)

echo "Instalaciones detectadas:"
echo "  HADOOP: ${HADOOP_DIR:-NO ENCONTRADO}"
echo "  SPARK: ${SPARK_DIR:-NO ENCONTRADO}"
echo "  KAFKA: ${KAFKA_DIR:-NO ENCONTRADO}"
echo "  NIFI: ${NIFI_DIR:-NO ENCONTRADO}"
echo "  HIVE: ${HIVE_DIR:-NO ENCONTRADO}"
echo ""

# Crear o actualizar .bashrc
BASHRC_FILE="$HOME/.bashrc"

if [ ! -f "$BASHRC_FILE" ]; then
    echo "Creando $BASHRC_FILE..."
    touch "$BASHRC_FILE"
fi

# Añadir configuración si no existe
if ! grep -q "# Big Data Project Environment" "$BASHRC_FILE"; then
    echo "" >> "$BASHRC_FILE"
    echo "# Big Data Project Environment" >> "$BASHRC_FILE"
    echo "# Added by ProyectoBigData setup script" >> "$BASHRC_FILE"
    
    [ -n "$HADOOP_DIR" ] && echo "export HADOOP_HOME=$HADOOP_DIR" >> "$BASHRC_FILE"
    [ -n "$SPARK_DIR" ] && echo "export SPARK_HOME=$SPARK_DIR" >> "$BASHRC_FILE"
    [ -n "$KAFKA_DIR" ] && echo "export KAFKA_HOME=$KAFKA_DIR" >> "$BASHRC_FILE"
    [ -n "$NIFI_DIR" ] && echo "export NIFI_HOME=$NIFI_DIR" >> "$BASHRC_FILE"
    [ -n "$HIVE_DIR" ] && echo "export HIVE_HOME=$HIVE_DIR" >> "$BASHRC_FILE"
    
    echo "" >> "$BASHRC_FILE"
    echo "# Add to PATH" >> "$BASHRC_FILE"
    [ -n "$HADOOP_DIR" ] && echo "export PATH=\$PATH:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin" >> "$BASHRC_FILE"
    [ -n "$SPARK_DIR" ] && echo "export PATH=\$PATH:\$SPARK_HOME/bin" >> "$BASHRC_FILE"
    [ -n "$KAFKA_DIR" ] && echo "export PATH=\$PATH:\$KAFKA_HOME/bin" >> "$BASHRC_FILE"
    [ -n "$NIFI_DIR" ] && echo "export PATH=\$PATH:\$NIFI_HOME/bin" >> "$BASHRC_FILE"
    [ -n "$HIVE_DIR" ] && echo "export PATH=\$PATH:\$HIVE_HOME/bin" >> "$BASHRC_FILE"
    
    echo "" >> "$BASHRC_FILE"
    echo "export MONGO_URI=\"mongodb://nodo1:27017/transport_db\"" >> "$BASHRC_FILE"
    
    echo "✓ Variables de entorno añadidas a $BASHRC_FILE"
else
    echo "⚠ Las variables ya están configuradas en $BASHRC_FILE"
fi

echo ""
echo "Para aplicar los cambios, ejecuta:"
echo "  source ~/.bashrc"
echo ""
echo "O cierra y abre una nueva terminal"
