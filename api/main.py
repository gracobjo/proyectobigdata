"""
API REST Transport Monitoring - Prueba de Swagger.
Lee datos de MongoDB (transport_db). Swagger UI en http://localhost:5000/docs

Ejecutar: uvicorn api.main:app --host 0.0.0.0 --port 5000
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
MONGO_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "transport_db"

app = FastAPI(
    title="Transport Monitoring API",
    description="API REST para estado de vehículos, retrasos y bottlenecks (MongoDB). Ver docs/api/openapi.yaml",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client[DB_NAME]

def serialize_doc(doc):
    if doc is None:
        return None
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d

@app.get("/health")
def health():
    """Estado del servicio y conexión MongoDB."""
    try:
        db = get_db()
        db.command("ping")
        return {"status": "ok", "mongo": "connected"}
    except Exception as e:
        return {"status": "ok", "mongo": "error", "detail": str(e)}

@app.get("/vehicles")
def list_vehicles(route_id: str = None, limit: int = Query(20, le=100)):
    """Listar último estado de vehículos (MongoDB vehicle_status)."""
    db = get_db()
    q = {} if not route_id else {"route_id": route_id}
    cursor = db.vehicle_status.find(q).sort("timestamp", -1).limit(limit)
    return [serialize_doc(d) for d in cursor]

@app.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str):
    """Último estado de un vehículo."""
    db = get_db()
    doc = db.vehicle_status.find_one({"vehicle_id": vehicle_id}, sort=[("timestamp", -1)])
    if not doc:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return serialize_doc(doc)

@app.get("/delays")
def list_delays(route_id: str = None, limit: int = Query(50, le=200)):
    """Agregados de retrasos por ventana (MongoDB route_delay_aggregates)."""
    db = get_db()
    q = {} if not route_id else {"route_id": route_id}
    cursor = db.route_delay_aggregates.find(q).sort("window_start", -1).limit(limit)
    return [serialize_doc(d) for d in cursor]

@app.get("/bottlenecks")
def list_bottlenecks():
    """Nodos cuello de botella (MongoDB bottlenecks)."""
    db = get_db()
    cursor = db.bottlenecks.find().sort("degree", -1)
    return [serialize_doc(d) for d in cursor]
