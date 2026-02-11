# Solución al problema de HDFS: "0 datanode(s) running"

## Diagnóstico del problema

### 1. **Desajuste de hostname/IP (causa principal)**

- El **hostname** de la máquina es `nodo1`.
- En `/etc/hosts`, `nodo1` está mapeado a **192.168.56.1** (IP de la red VirtualBox que no existe en este equipo).
- El **DataNode** se registra en el NameNode con la dirección que obtiene al resolver su hostname → **nodo1** → **192.168.56.1**.
- Cuando el NameNode intenta enviar bloques al DataNode, usa **192.168.56.1:9864**, que en tu máquina **no es alcanzable**.
- Resultado: el NameNode no puede hablar con el DataNode → "0 datanode(s) running".

### 2. **NameNode en 0.0.0.0 impide que el DataNode se registre**

- Si `dfs.namenode.rpc-address` es **0.0.0.0:9000**, el DataNode intenta conectarse a "0.0.0.0:9000" para registrarse; en muchos sistemas esa conexión falla.
- Debe ser **127.0.0.1:9000** (y lo mismo para `http-address` y `secondary.http-address`) para que el DataNode pueda conectar al NameNode en standalone.

### 3. **Error tipográfico en hdfs-site.xml**

- `dfs.namenode.secondary.http-address` puede estar como **0.0.0.001:50090** (typo). Debe ser **127.0.0.1:50090** en standalone.

### 4. **Factor de replicación**

- `dfs.replication` está en **2**.
- En modo standalone solo hay **un** DataNode, por lo que no se pueden crear 2 réplicas.
- Para un solo nodo debe ser **1**.

### 5. **ClusterID incompatible (DataNode no se registra)**

- Si en el log del DataNode aparece: **"Incompatible clusterIDs"** o **"All specified directories have failed to load"**, el directorio de datos del DataNode tiene un `clusterID` distinto al del NameNode (por ejemplo, se formateó el NameNode después de haber arrancado el DataNode, o se usaron rutas distintas).
- El DataNode rechaza registrarse para no unirse a otro cluster por error.
- **Solución**: parar el DataNode, borrar el contenido del directorio de datos del DataNode (o al menos el archivo `current/VERSION`) para que en el próximo arranque reciba el clusterID del NameNode. Ver sección "Solución: clusterID incompatible" más abajo.

---

## Solución (pasos a seguir)

### Opción recomendada: Usar hdfs-site-standalone.xml del proyecto

El archivo `config/hdfs/hdfs-site-standalone.xml` del proyecto ya tiene **NameNode y Secondary en 127.0.0.1** (no 0.0.0.0), para que el DataNode pueda conectarse y registrarse correctamente. Solo hay que copiarlo y reiniciar HDFS:

```bash
sudo cp /home/hadoop/Documentos/ProyectoBigData/config/hdfs/hdfs-site-standalone.xml /usr/local/hadoop/etc/hadoop/hdfs-site.xml
```

Luego reinicia HDFS (ver sección "Después de cambiar la configuración" más abajo) y ejecuta `hdfs dfsadmin -report`. Si sigue en 0 datanodes, aplica además el cambio de `/etc/hosts` (siguiente opción).

### Opción A: Cambiar /etc/hosts (muy fiable)

Haz que **nodo1** resuelva a **127.0.0.1**. Así el DataNode se registra con una IP que el NameNode puede usar sin tocar la config de Hadoop:

```bash
sudo nano /etc/hosts
```

Modifica la línea de nodo1 para que quede exactamente así (y borra o comenta la que tenía 192.168.56.1):

```
127.0.0.1   nodo1
```

Guarda (Ctrl+O, Enter, Ctrl+X). Luego **reinicia HDFS**:

```bash
hdfs --daemon stop datanode
hdfs --daemon stop secondarynamenode
hdfs --daemon stop namenode
sleep 5
hdfs --daemon start namenode
sleep 8
hdfs --daemon start datanode
sleep 8
hdfs --daemon start secondarynamenode
sleep 3
hdfs dfsadmin -report
```

Debería aparecer "Live datanodes (1)". Prueba: `echo "test" | hdfs dfs -put - /test.txt && hdfs dfs -cat /test.txt`

---

### Opción B: Solo configuración de Hadoop (hdfs-site.xml)

Ejecuta estos comandos (algunos requieren `sudo`):

```bash
# 1. Backup de hdfs-site.xml
sudo cp /usr/local/hadoop/etc/hadoop/hdfs-site.xml /usr/local/hadoop/etc/hadoop/hdfs-site.xml.backup2

# 2. Corregir el typo 0.0.0.001 -> 0.0.0.0
sudo sed -i 's/0.0.0.001/0.0.0.0/g' /usr/local/hadoop/etc/hadoop/hdfs-site.xml

# 3. Cambiar replicación a 1
sudo sed -i 's/<value>2<\/value>/<value>1<\/value>/' /usr/local/hadoop/etc/hadoop/hdfs-site.xml

# 4. Añadir dirección del DataNode para que use 127.0.0.1 (antes del </configuration> final)
#    Esto hace que el DataNode se anuncie como localhost y el NameNode pueda contactarlo.
sudo sed -i 's|</configuration>|  <property>\n    <name>dfs.datanode.address</name>\n    <value>127.0.0.1:9866</value>\n  </property>\n  <property>\n    <name>dfs.datanode.http.address</name>\n    <value>127.0.0.1:9864</value>\n  </property>\n</configuration>|' /usr/local/hadoop/etc/hadoop/hdfs-site.xml
```

El último `sed` puede no insertar bien los saltos de línea. Si el XML queda mal, usa el archivo que se indica más abajo.

### Opción B: Editar hdfs-site.xml a mano

Abre el archivo:

```bash
sudo nano /usr/local/hadoop/etc/hadoop/hdfs-site.xml
```

Asegúrate de que:

1. **dfs.namenode.rpc-address** sea `127.0.0.1:9000` y **dfs.namenode.http-address** `127.0.0.1:9870` (no 0.0.0.0, para que el DataNode pueda conectar).
2. **dfs.namenode.secondary.http-address** sea `127.0.0.1:50090` (no `0.0.0.001`).
3. **dfs.replication** sea `1`.
4. Añade **antes** de la etiqueta `</configuration>` final: de la etiqueta `</configuration>` final:

```xml
  <!-- Dirección del DataNode: usar 127.0.0.1 para modo standalone -->
  <property>
    <name>dfs.datanode.address</name>
    <value>127.0.0.1:9866</value>
    <description>Dirección donde el DataNode escucha y se anuncia al NameNode</description>
  </property>
  <property>
    <name>dfs.datanode.http.address</name>
    <value>127.0.0.1:9864</value>
  </property>
```

Guarda y cierra.

### Opción C: Ajustar solo /etc/hosts (alternativa rápida)

Si prefieres no tocar `hdfs-site.xml`, puedes hacer que **nodo1** apunte a localhost. Así el DataNode se anuncia como 127.0.0.1 al resolver su hostname:

```bash
sudo nano /etc/hosts
```

Cambia la línea de nodo1 para que quede:

```
127.0.0.1   nodo1
```

(Comenta o borra la línea que tenía 192.168.56.1 nodo1.) Opcional: deja nodo2 como esté o coméntala si no usas la VM.

Luego **reinicia HDFS** (NameNode y DataNode). No hace falta cambiar la replicación ni el typo de 0.0.0.001 si solo usas esta opción; pero corregir replicación a 1 y el typo sigue siendo recomendable.

---

## Solución: clusterID incompatible

Si el diagnóstico muestra **"Incompatible clusterIDs"** o **"All specified directories have failed to load"** en el log del DataNode, haz lo siguiente (esto borra los datos locales del DataNode; en standalone no suele haber nada importante):

```bash
# 1. Parar solo el DataNode
hdfs --daemon stop datanode
sleep 3

# 2. Borrar el directorio de datos del DataNode para que tome el clusterID del NameNode
#    (usa la ruta que tengas en hdfs-site.xml; suele ser una de estas)
sudo rm -rf /usr/local/hadoop/data/datanode/*
# Si tu instalación usa otra ruta (p. ej. hadoop-3.4.1):
# sudo rm -rf /usr/local/hadoop-3.4.1/data/datanode/*

# 3. Arrancar de nuevo el DataNode
hdfs --daemon start datanode
sleep 5

# 4. Comprobar
hdfs dfsadmin -report
```

Deberías ver **Live datanodes (1)**. Prueba: `echo "test" | hdfs dfs -put - /test.txt && hdfs dfs -cat /test.txt`

---

## Después de cambiar la configuración

```bash
# 1. Parar servicios HDFS
hdfs --daemon stop datanode
hdfs --daemon stop secondarynamenode
hdfs --daemon stop namenode

# 2. Esperar unos segundos
sleep 5

# 3. Arrancar en orden
hdfs --daemon start namenode
sleep 5
hdfs --daemon start datanode
sleep 5
hdfs --daemon start secondarynamenode

# 4. Comprobar
jps | grep -E "NameNode|DataNode"
hdfs dfsadmin -report

# 5. Probar escritura
echo "test" | hdfs dfs -put - /test.txt
hdfs dfs -cat /test.txt
hdfs dfs -rm /test.txt
```

Si `hdfs dfsadmin -report` muestra un DataNode "Live" y la escritura/lectura funciona, el problema de HDFS está resuelto.
