#!/usr/bin/env python3
"""
Script para generar un fichero de logs GPS que NiFi puede leer con GetFile.
Genera un archivo JSONL (JSON Lines) con datos GPS simulados.
"""
import json
import random
import os
from datetime import datetime, timedelta

# Configuración
OUTPUT_DIR = "/home/hadoop/data/gps_logs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"gps_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
NUM_RECORDS = 100

VEHICLES = ['V001', 'V002', 'V003', 'V004', 'V005', 'V006', 'V007', 'V008']
ROUTES = ['R001', 'R002', 'R003', 'R004', 'R005', 'R006', 'R007']
STATUSES = ['IN_TRANSIT', 'LOADING', 'UNLOADING', 'MAINTENANCE']

# Coordenadas aproximadas de almacenes
WAREHOUSES = {
    'A': (40.7128, -74.0060),  # Almacen_Norte
    'B': (34.0522, -118.2437), # Almacen_Sur
    'C': (41.8781, -87.6298),  # Almacen_Este
    'D': (37.7749, -122.4194), # Almacen_Oeste
    'E': (39.9526, -75.1652),  # Almacen_Centro
}

def generate_gps_record():
    """Genera un registro de datos GPS simulado"""
    vehicle_id = random.choice(VEHICLES)
    route_id = random.choice(ROUTES)
    status = random.choice(STATUSES)
    
    # Generar coordenadas cerca de un almacén aleatorio
    warehouse = random.choice(list(WAREHOUSES.keys()))
    base_lat, base_lon = WAREHOUSES[warehouse]
    
    # Añadir variación aleatoria
    latitude = base_lat + random.uniform(-0.1, 0.1)
    longitude = base_lon + random.uniform(-0.1, 0.1)
    
    # Velocidad según estado
    if status == 'IN_TRANSIT':
        speed = random.uniform(50, 100)
    elif status in ['LOADING', 'UNLOADING']:
        speed = random.uniform(0, 5)
    else:
        speed = 0
    
    timestamp = datetime.now() - timedelta(minutes=random.randint(0, 60))
    
    return {
        'vehicle_id': vehicle_id,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'latitude': round(latitude, 6),
        'longitude': round(longitude, 6),
        'speed': round(speed, 2),
        'route_id': route_id,
        'status': status
    }

def main():
    """Genera un fichero JSONL con logs GPS"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generar fichero de logs GPS para NiFi")
    parser.add_argument("-n", "--num-records", type=int, default=NUM_RECORDS,
                       help=f"Número de registros a generar (default: {NUM_RECORDS})")
    parser.add_argument("-o", "--output", type=str, default=OUTPUT_FILE,
                       help=f"Ruta del fichero de salida (default: {OUTPUT_FILE})")
    parser.add_argument("-d", "--directory", type=str, default=OUTPUT_DIR,
                       help=f"Directorio de salida (default: {OUTPUT_DIR})")
    
    args = parser.parse_args()
    
    # Crear directorio si no existe
    os.makedirs(args.directory, exist_ok=True)
    
    # Determinar ruta del fichero
    if args.output == OUTPUT_FILE and args.directory != OUTPUT_DIR:
        output_file = os.path.join(args.directory, os.path.basename(OUTPUT_FILE))
    else:
        output_file = args.output
    
    print(f"Generando {args.num_records} registros GPS...")
    print(f"Directorio de salida: {args.directory}")
    print(f"Fichero: {output_file}")
    
    try:
        with open(output_file, 'w') as f:
            for i in range(args.num_records):
                record = generate_gps_record()
                f.write(json.dumps(record) + '\n')
                
                if (i + 1) % 50 == 0:
                    print(f"  Generados {i + 1}/{args.num_records} registros...")
        
        print(f"\n✓ Fichero generado exitosamente: {output_file}")
        print(f"  Total de registros: {args.num_records}")
        print(f"\nPara usar en NiFi:")
        print(f"  1. Configura GetFile con Input Directory: {args.directory}")
        print(f"  2. O usa TailFile para leer este fichero en tiempo real")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
