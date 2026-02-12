"""
Paso 1 (sin IA): Recomendación de ruta usando grafo + retrasos actuales en MongoDB.
Paso 3 (con IA): Recomendación ponderando aristas con modelo de predicción de retrasos.
"""
import os
from datetime import datetime
import networkx as nx
from routing.graph_data import EDGES, ROUTE_ID_TO_EDGE, EDGE_TO_TIME

MONGO_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "transport_db"
COLLECTION_DELAYS = "route_delay_aggregates"


def _get_db():
    from pymongo import MongoClient
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)[DB_NAME]


def get_delays_by_route(mongo_db=None):
    """
    Lee los últimos delay_percentage por route_id desde MongoDB.
    Returns: dict route_id -> delay_percentage (0 si no hay datos).
    """
    if mongo_db is None:
        mongo_db = _get_db()
    coll = mongo_db[COLLECTION_DELAYS]
    latest = {}
    for doc in coll.find().sort("window_start", -1):
        rid = doc.get("route_id")
        if rid and rid not in latest:
            latest[rid] = float(doc.get("delay_percentage", 0) or 0)
    return latest


def build_weighted_graph(delays_by_route=None, mongo_db=None):
    """
    Construye un grafo dirigido con pesos en las aristas.
    peso = time_minutes * (1 + delay_percentage/100).
    delays_by_route: dict route_id (R001, R002...) -> delay_percentage. Si None, se lee de MongoDB.
    """
    if delays_by_route is None:
        delays_by_route = get_delays_by_route(mongo_db)

    edge_to_route_id = {v: k for k, v in ROUTE_ID_TO_EDGE.items()}
    G = nx.DiGraph()
    for src, dst, _route_id, _dist, time_min in EDGES:
        rid = edge_to_route_id.get((src, dst))
        delay_pct = float(delays_by_route.get(rid, 0.0) or 0.0)
        weight = time_min * (1.0 + delay_pct / 100.0)
        G.add_edge(src, dst, weight=weight, time_minutes=time_min, delay_percentage=delay_pct)
    return G


def recommend_route(origin: str, destination: str, mongo_db=None):
    """
    Recomienda la ruta (secuencia de nodos) que minimiza el peso (tiempo ponderado por retraso).
    origin, destination: id de nodo (A, B, C, D, E).
    Returns: dict con path (lista de nodos), edges (lista de (src,dst)), total_weight, total_time_minutes.
    """
    G = build_weighted_graph(mongo_db=mongo_db)
    origin, destination = origin.strip().upper(), destination.strip().upper()
    if origin not in G or destination not in G:
        return None
    try:
        path = nx.shortest_path(G, origin, destination, weight="weight")
    except nx.NetworkXNoPath:
        return None
    total_weight = 0.0
    total_time = 0.0
    edges = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        data = G.edges[u, v]
        total_weight += data["weight"]
        total_time += data["time_minutes"]
        edges.append((u, v))
    return {
        "path": path,
        "edges": edges,
        "total_weight": round(total_weight, 2),
        "total_time_minutes": round(total_time, 2),
    }


# --- Paso 3: recomendación con IA (modelo de predicción de retrasos) ---

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_delay.joblib")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "encoder_route.joblib")
_model_cache = None
_encoder_cache = None


def load_model():
    """Carga modelo y encoder desde disco (si existen)."""
    global _model_cache, _encoder_cache
    if _model_cache is not None:
        return _model_cache, _encoder_cache
    if not os.path.isfile(MODEL_PATH) or not os.path.isfile(ENCODER_PATH):
        return None, None
    import joblib
    _model_cache = joblib.load(MODEL_PATH)
    _encoder_cache = joblib.load(ENCODER_PATH)
    return _model_cache, _encoder_cache


def predict_delay_for_route(route_id: str, at: datetime, model, encoder):
    """Predice delay_percentage para un route_id en un instante (hour, day_of_week, month)."""
    import numpy as np
    at = at or datetime.utcnow()
    try:
        enc = encoder.transform([str(route_id)])[0]
    except Exception:
        return 0.0
    X = np.array([[enc, at.hour, at.weekday(), at.month]])
    pred = model.predict(X)
    return max(0.0, float(pred[0]))


def recommend_route_ml(origin: str, destination: str, at=None, mongo_db=None, k_paths=5):
    """
    Recomienda la ruta entre origin y destination usando el modelo de predicción de retrasos (Paso 3).
    Obtiene k caminos candidatos (por tiempo base), los puntúa con el modelo y devuelve el de menor tiempo efectivo predicho.
    at: datetime para la predicción (hora, día, mes). Si None, se usa ahora.
    """
    model, encoder = load_model()
    if model is None or encoder is None:
        return None  # Sin modelo: devolver None para que el API pueda usar Paso 1

    at = at or datetime.utcnow()
    edge_to_route_id = {v: k for k, v in ROUTE_ID_TO_EDGE.items()}

    G = nx.DiGraph()
    for src, dst, _, _dist, time_min in EDGES:
        G.add_edge(src, dst, time_minutes=time_min)

    origin = origin.strip().upper()
    destination = destination.strip().upper()
    if origin not in G or destination not in G:
        return None

    try:
        gen = nx.shortest_simple_paths(G, origin, destination, weight="time_minutes")
        candidates = []
        for _ in range(k_paths):
            try:
                path = next(gen)
            except StopIteration:
                break
            total_eff = 0.0
            total_time = 0.0
            edges = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                rid = edge_to_route_id.get((u, v))
                time_min = EDGE_TO_TIME.get((u, v), 0)
                pred_delay = predict_delay_for_route(rid or "", at, model, encoder)
                total_eff += time_min * (1.0 + pred_delay / 100.0)
                total_time += time_min
                edges.append((u, v))
            candidates.append((total_eff, path, edges, total_time))
    except nx.NetworkXNoPath:
        return None

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    _weight, path, edges, total_time = candidates[0]
    return {
        "path": path,
        "edges": edges,
        "total_weight": round(_weight, 2),
        "total_time_minutes": round(total_time, 2),
        "model_used": True,
    }
