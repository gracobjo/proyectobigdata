"""
Grafo de la red (mismo que viz/graph_data y network_analysis.py).
Aristas: (src, dst, route_id, distance_km, time_minutes).
"""
VERTICES = [
    {"id": "A", "name": "Almacen_Norte", "lat": 40.7128, "lon": -74.0060, "region": "Norte"},
    {"id": "B", "name": "Almacen_Sur", "lat": 34.0522, "lon": -118.2437, "region": "Sur"},
    {"id": "C", "name": "Almacen_Este", "lat": 41.8781, "lon": -87.6298, "region": "Este"},
    {"id": "D", "name": "Almacen_Oeste", "lat": 37.7749, "lon": -122.4194, "region": "Oeste"},
    {"id": "E", "name": "Almacen_Centro", "lat": 39.9526, "lon": -75.1652, "region": "Centro"},
]
EDGES = [
    ("A", "B", "Ruta_AB", 2800.0, 45),
    ("A", "C", "Ruta_AC", 1200.0, 20),
    ("B", "D", "Ruta_BD", 560.0, 10),
    ("C", "E", "Ruta_CE", 800.0, 15),
    ("D", "E", "Ruta_DE", 4000.0, 60),
    ("A", "E", "Ruta_AE", 200.0, 5),
    ("B", "C", "Ruta_BC", 3000.0, 50),
]

# MongoDB route_id (R001, R002...) -> (src, dst) en el grafo. Orden coherente con rutas maestras.
ROUTE_ID_TO_EDGE = {
    "R001": ("A", "B"),
    "R002": ("A", "C"),
    "R003": ("B", "D"),
    "R004": ("C", "E"),
    "R005": ("D", "E"),
    "R006": ("A", "E"),
    "R007": ("B", "C"),
}

EDGE_TO_TIME = {(src, dst): time_min for (src, dst, _, _, time_min) in EDGES}
