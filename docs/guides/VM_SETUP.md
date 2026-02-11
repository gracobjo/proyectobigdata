# Guía de Configuración de VM nodo2

## Situación Actual

- VirtualBox está instalado pero no hay VMs registradas
- La carpeta por defecto es: `/home/hadoop/VirtualBox VMs`
- La red VirtualBox está configurada: `vboxnet0` (192.168.56.0/24)
- nodo2 debería estar en: `192.168.56.101`

## Opción 1: Crear Nueva VM nodo2

### Paso 1: Crear la VM

```bash
# Crear carpeta para la VM
mkdir -p "/home/hadoop/VirtualBox VMs/nodo2"

# Crear VM con VBoxManage (o usar interfaz gráfica)
VBoxManage createvm --name "nodo2" --ostype "Linux_64" --register --basefolder "/home/hadoop/VirtualBox VMs"

# Configurar recursos
VBoxManage modifyvm "nodo2" --memory 2048 --cpus 2

# Configurar red (adaptador 1: NAT, adaptador 2: Host-only)
VBoxManage modifyvm "nodo2" --nic1 nat
VBoxManage modifyvm "nodo2" --nic2 hostonly --hostonlyadapter2 vboxnet0

# Crear disco duro
VBoxManage createhd --filename "/home/hadoop/VirtualBox VMs/nodo2/nodo2.vdi" --size 20000 --format VDI

# Conectar disco a la VM
VBoxManage storagectl "nodo2" --name "SATA Controller" --add sata --controller IntelAHCI
VBoxManage storageattach "nodo2" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "/home/hadoop/VirtualBox VMs/nodo2/nodo2.vdi"
```

### Paso 2: Instalar Sistema Operativo

1. Descargar ISO de Ubuntu Server 22.04 o similar
2. Conectar ISO a la VM:
```bash
VBoxManage storagectl "nodo2" --name "IDE Controller" --add ide
VBoxManage storageattach "nodo2" --storagectl "IDE Controller" --port 0 --device 0 --type dvddrive --medium /ruta/a/ubuntu.iso
```

3. Iniciar VM:
```bash
VBoxManage startvm "nodo2" --type gui
```

4. Durante la instalación:
   - Configurar hostname: `nodo2`
   - Configurar usuario: `hadoop` (mismo que nodo1)
   - Configurar IP estática en el segundo adaptador: `192.168.56.101/24`

### Paso 3: Configurar nodo2

Una vez instalado el SO:

```bash
# En nodo2, configurar /etc/hosts
sudo nano /etc/hosts
# Añadir:
192.168.56.1    nodo1
192.168.56.101  nodo2

# Instalar Hadoop y componentes necesarios
# (seguir docs/guides/INSTALLATION.md)
```

### Paso 4: Configurar SSH sin contraseña (para Hadoop)

```bash
# En nodo1, generar clave SSH si no existe
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa

# Copiar clave a nodo2
ssh-copy-id hadoop@nodo2

# Verificar conexión
ssh hadoop@nodo2 "hostname"
```

---

## Opción 2: Trabajar Solo con nodo1 (Modo Standalone)

Si prefieres trabajar solo con nodo1 por ahora, puedes adaptar el proyecto:

### Modificar Configuraciones

1. **HDFS**: Configurar para modo pseudo-distribuido (todo en nodo1)
2. **YARN**: ResourceManager y NodeManager en el mismo nodo
3. **Kafka**: Solo un broker en nodo1
4. **MongoDB**: Solo en nodo1

### Ventajas
- Más simple para desarrollo
- No necesitas mantener una VM
- Más rápido para pruebas

### Desventajas
- No es un cluster real distribuido
- Menos realista para producción

---

## Opción 3: Usar Docker en lugar de VM

Puedes crear un contenedor Docker que actúe como nodo2:

```bash
# Crear Dockerfile para nodo2
# Ejecutar servicios Hadoop en contenedor
docker run -d --name nodo2 \
  --hostname nodo2 \
  --network host \
  -v /hadoop-data:/data \
  hadoop-node:latest
```

---

## Verificación

Una vez configurado nodo2:

```bash
# Verificar VM está corriendo
VBoxManage list runningvms

# Verificar conectividad
ping -c 3 nodo2

# Verificar SSH
ssh hadoop@nodo2 "hostname && jps"

# Verificar que Hadoop puede comunicarse
# En nodo1:
start-dfs.sh
# Debería iniciar DataNode en nodo2
```

---

## Troubleshooting

### VM no aparece en VirtualBox GUI
```bash
# Registrar VM manualmente
VBoxManage registervm "/home/hadoop/VirtualBox VMs/nodo2/nodo2.vbox"
```

### No puede conectar a nodo2
```bash
# Verificar red VirtualBox
VBoxManage list hostonlyifs

# Verificar que vboxnet0 está activa
sudo ip addr show vboxnet0
```

### SSH no funciona
```bash
# Verificar que SSH está instalado en nodo2
ssh hadoop@nodo2 "which sshd"

# Verificar firewall
sudo ufw status
```
