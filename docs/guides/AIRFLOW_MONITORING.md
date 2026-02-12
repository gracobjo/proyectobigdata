# Monitoreo de DAGs en Airflow

Guía para monitorear y gestionar las ejecuciones de DAGs en Airflow.

## Comandos básicos de monitoreo

### Ver todas las ejecuciones de un DAG

```bash
airflow dags list-runs -d <dag_id>
```

Ejemplo:
```bash
airflow dags list-runs -d weekly_delay_model_training
```

### Ver ejecuciones por estado

```bash
# Solo ejecuciones en curso
airflow dags list-runs -d <dag_id> --state running

# Solo ejecuciones fallidas
airflow dags list-runs -d <dag_id> --state failed

# Solo ejecuciones exitosas
airflow dags list-runs -d <dag_id> --state success
```

### Ver el estado de un DAG run específico

**Importante**: Usa el `execution_date`, no el `run_id`.

```bash
airflow dags state <dag_id> <execution_date>
```

El `execution_date` se muestra en la columna `execution_date` de `dags list-runs`. Formato: `YYYY-MM-DDTHH:MM:SS+00:00`

Ejemplo:
```bash
airflow dags state weekly_delay_model_training "2026-02-12T16:11:28+00:00"
```

### Ver el estado de una tarea específica

```bash
airflow tasks state <dag_id> <task_id> <execution_date>
```

Ejemplo:
```bash
airflow tasks state weekly_delay_model_training check_mongodb_data "2026-02-12T16:11:28+00:00"
```

### Ver todas las tareas de un DAG

```bash
airflow tasks list <dag_id>
```

### Ver logs de una tarea

```bash
airflow tasks logs <dag_id> <task_id> <execution_date>
```

Ejemplo:
```bash
airflow tasks logs weekly_delay_model_training check_mongodb_data "2026-02-12T16:11:28+00:00"
```

## Estados de ejecución

| Estado | Significado |
|-------|-------------|
| **queued** | En cola, esperando ser ejecutado |
| **running** | Ejecutándose actualmente |
| **success** | Completado exitosamente |
| **failed** | Falló durante la ejecución |
| **skipped** | Omitido (dependencias fallaron) |
| **up_for_retry** | En espera de reintento |
| **up_for_reschedule** | Programado para reintento |

## Solución de problemas

### El DAG está en "queued" y no se ejecuta

1. **Verificar que el scheduler esté corriendo:**
   ```bash
   ps aux | grep "airflow scheduler"
   ```

2. **Verificar que el DAG no esté pausado:**
   ```bash
   airflow dags list | grep <dag_id>
   ```
   Si está pausado (`is_paused = True`), activarlo:
   ```bash
   airflow dags unpause <dag_id>
   ```

3. **Verificar límites de concurrencia:**
   - El executor puede tener límites de tareas concurrentes
   - Revisar `airflow.cfg` para `parallelism` y `dag_concurrency`

4. **Revisar logs del scheduler:**
   ```bash
   tail -f ~/airflow/logs/scheduler.log
   ```

### Ver logs del scheduler

```bash
# Ver últimas líneas
tail -50 ~/airflow/logs/scheduler.log

# Seguir en tiempo real
tail -f ~/airflow/logs/scheduler.log

# Buscar errores
grep -i error ~/airflow/logs/scheduler.log | tail -20
```

### Ver logs del webserver

```bash
tail -50 ~/airflow/logs/webserver.log
```

## Interfaz web

La forma más fácil de monitorear es usar la interfaz web:

1. Abre http://localhost:8080
2. Busca tu DAG en la lista
3. Haz clic en el nombre del DAG
4. Ve a la pestaña **Graph** o **Grid** para ver el estado de las tareas
5. Haz clic en una tarea para ver sus logs

## Ejemplos prácticos

### Monitorear una ejecución completa

```bash
# 1. Ejecutar el DAG
airflow dags trigger weekly_delay_model_training

# 2. Obtener el execution_date del run creado
EXEC_DATE=$(airflow dags list-runs -d weekly_delay_model_training --no-header | head -1 | awk '{print $3}')

# 3. Monitorear el estado
watch -n 5 "airflow dags state weekly_delay_model_training \"$EXEC_DATE\""

# 4. Ver logs cuando termine
airflow tasks logs weekly_delay_model_training notify_completion "$EXEC_DATE"
```

### Verificar que todas las tareas completaron

```bash
# Listar todas las tareas y sus estados
for task in $(airflow tasks list weekly_delay_model_training); do
    echo -n "$task: "
    airflow tasks state weekly_delay_model_training "$task" "2026-02-12T16:11:28+00:00"
done
```

## Referencias

- Documentación principal: **docs/guides/AIRFLOW.md**
- Comandos CLI: `airflow --help` o `airflow dags --help`
