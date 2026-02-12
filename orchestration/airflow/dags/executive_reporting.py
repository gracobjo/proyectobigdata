"""
DAG de Airflow para generación de reportes ejecutivos semanales.
Consulta Hive/MongoDB, genera informe y envía por email.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'executive_reporting',
    default_args=default_args,
    description='Reporte ejecutivo semanal: tendencias, métricas, resumen',
    schedule_interval='@weekly',  # Cada lunes
    start_date=days_ago(1),
    catchup=False,
    tags=['reporting', 'executive', 'weekly'],
)

# Tarea 1: Consultar tendencias semanales desde MongoDB
def query_weekly_trends(**context):
    """Consulta agregados semanales desde MongoDB."""
    from pymongo import MongoClient
    from datetime import datetime, timedelta
    import json
    
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    db = client["transport_db"]
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Agregar por ruta (últimos 7 días)
    pipeline = [
        {"$match": {"window_start": {"$gte": week_ago}}},
        {"$group": {
            "_id": "$route_id",
            "avg_delay_pct": {"$avg": "$delay_percentage"},
            "max_delay_pct": {"$max": "$delay_percentage"},
            "total_windows": {"$sum": 1},
            "avg_speed": {"$avg": "$avg_speed"},
        }},
        {"$sort": {"avg_delay_pct": -1}},
    ]
    
    trends = list(db.route_delay_aggregates.aggregate(pipeline))
    
    # Bottlenecks
    bottlenecks = list(db.bottlenecks.find().sort("degree", -1))
    
    report_data = {
        "period": f"{week_ago.date()} a {datetime.utcnow().date()}",
        "routes": trends,
        "bottlenecks": [{"node_id": b["node_id"], "degree": b["degree"]} for b in bottlenecks],
        "total_delay_windows": len(list(db.route_delay_aggregates.find({"window_start": {"$gte": week_ago}}))),
    }
    
    client.close()
    
    # Guardar JSON para el siguiente paso
    import json
    with open("/tmp/weekly_report_data.json", "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"✓ Datos semanales consultados: {len(trends)} rutas")
    return report_data

query_trends = PythonOperator(
    task_id='query_weekly_trends',
    python_callable=query_weekly_trends,
    dag=dag,
)

# Tarea 2: Generar informe HTML
def generate_html_report(**context):
    """Genera un informe HTML a partir de los datos consultados."""
    import json
    
    with open("/tmp/weekly_report_data.json", "r") as f:
        data = json.load(f)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reporte Semanal - Transport Monitoring</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .alert {{ color: #d32f2f; }}
        </style>
    </head>
    <body>
        <h1>Reporte Semanal de Transport Monitoring</h1>
        <p><strong>Período:</strong> {data['period']}</p>
        
        <h2>Rutas por Retraso Promedio</h2>
        <table>
            <tr>
                <th>Ruta</th>
                <th>Retraso Promedio (%)</th>
                <th>Retraso Máximo (%)</th>
                <th>Velocidad Promedio (km/h)</th>
                <th>Ventanas Analizadas</th>
            </tr>
    """
    
    for route in data["routes"]:
        delay_avg = route.get("avg_delay_pct", 0)
        alert_class = "alert" if delay_avg > 50 else ""
        html += f"""
            <tr class="{alert_class}">
                <td>{route['_id']}</td>
                <td>{delay_avg:.2f}%</td>
                <td>{route.get('max_delay_pct', 0):.2f}%</td>
                <td>{route.get('avg_speed', 0):.2f}</td>
                <td>{route.get('total_windows', 0)}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>Cuellos de Botella</h2>
        <ul>
    """
    
    for bn in data["bottlenecks"]:
        html += f"<li><strong>{bn['node_id']}</strong>: grado {bn['degree']}</li>"
    
    html += f"""
        </ul>
        
        <p><strong>Total de ventanas analizadas:</strong> {data['total_delay_windows']}</p>
        <p><em>Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    </body>
    </html>
    """
    
    report_path = f"/tmp/transport_report_{datetime.now().strftime('%Y%m%d')}.html"
    with open(report_path, "w") as f:
        f.write(html)
    
    print(f"✓ Informe HTML generado: {report_path}")
    return report_path

generate_report = PythonOperator(
    task_id='generate_html_report',
    python_callable=generate_html_report,
    dag=dag,
)

# Tarea 3: Enviar email (opcional, requiere configuración SMTP)
send_email = BashOperator(
    task_id='send_email_report',
    bash_command="""
    REPORT_FILE="/tmp/transport_report_$(date +%Y%m%d).html"
    if [ -f "$REPORT_FILE" ]; then
        echo "Reporte generado: $REPORT_FILE"
        echo "Para enviar por email, configurar EmailOperator en Airflow con SMTP"
        # Ejemplo con mailx (si está configurado):
        # cat $REPORT_FILE | mailx -s "Reporte Semanal Transport Monitoring" -a "Content-Type: text/html" admin@example.com
    else
        echo "Error: reporte no encontrado"
        exit 1
    fi
    """,
    dag=dag,
)

# Definir dependencias
query_trends >> generate_report >> send_email
