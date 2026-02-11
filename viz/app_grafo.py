#!/usr/bin/env python3
"""
Visualización del grafo de red de transporte con Streamlit.
Muestra nodos (almacenes), aristas (rutas) y resalta los bottlenecks desde MongoDB.

Uso:
  pip install streamlit pyvis networkx
  streamlit run viz/app_grafo.py
"""

import os
import sys

# Asegurar que la raíz del proyecto esté en el path (streamlit run viz/app_grafo.py)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import networkx as nx
from pyvis.network import Network

from viz.graph_data import VERTICES, EDGES

# MongoDB opcional (bottlenecks)
MONGO_URI = "mongodb://127.0.0.1:27017/"
MONGO_DB = "transport_db"
MONGO_COLLECTION = "bottlenecks"

def get_bottlenecks():
    """Obtener grados de nodos desde MongoDB (bottlenecks)."""
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[MONGO_DB]
        coll = db[MONGO_COLLECTION]
        docs = list(coll.find({}, {"_id": 0, "node_id": 1, "degree": 1}))
        return {d["node_id"]: d["degree"] for d in docs}
    except Exception:
        return {}

def build_networkx_graph():
    """Construir grafo con NetworkX (para layout)."""
    G = nx.DiGraph()
    for v in VERTICES:
        G.add_node(v["id"], **v)
    for e in EDGES:
        src, dst, route_id, dist_km, time_min = e
        G.add_edge(src, dst, route_id=route_id, distance_km=dist_km, time_minutes=time_min)
    return G

def render_pyvis(G, bottlenecks):
    """Generar HTML interactivo con Pyvis."""
    net = Network(
        height="500px",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources="in_line",
    )
    net.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.001,
        damping=0.09,
    )

    # Nodos
    for n in G.nodes():
        data = G.nodes[n]
        label = f"{n} - {data.get('name', n)}"
        title = f"ID: {n}\n{data.get('name', '')}\nRegión: {data.get('region', '')}"
        degree = bottlenecks.get(n, 0)
        is_bottleneck = degree >= 3
        color = "#e74c3c" if is_bottleneck else "#3498db"
        size = 25 + (degree * 5) if degree else 20
        net.add_node(n, label=label, title=title, color=color, size=size)

    # Aristas
    for u, v in G.edges():
        edge_data = G.edges[u, v]
        title = f"{edge_data.get('route_id', '')} - {edge_data.get('distance_km', 0):.0f} km, {edge_data.get('time_minutes', 0)} min"
        net.add_edge(u, v, title=title)

    html = net.generate_html()
    return html

def main():
    st.set_page_config(page_title="Grafo Red de Transporte", page_icon="🛣️", layout="wide")
    st.title("🛣️ Red de Transporte - Visualización del grafo")
    st.caption("Grafo de almacenes y rutas (mismo modelo que network_analysis.py). Nodos rojos = bottlenecks desde MongoDB.")

    bottlenecks = get_bottlenecks()
    if bottlenecks:
        st.success(f"Bottlenecks cargados desde MongoDB: {len(bottlenecks)} nodos (grado ≥ 3).")
        with st.expander("Ver bottlenecks"):
            for nid, deg in sorted(bottlenecks.items(), key=lambda x: -x[1]):
                st.write(f"**{nid}**: grado {deg}")
    else:
        st.info("MongoDB no disponible o colección bottlenecks vacía. Se muestra el grafo sin resaltar bottlenecks.")

    G = build_networkx_graph()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Grafo interactivo (Pyvis)")
        html = render_pyvis(G, bottlenecks)
        st.components.v1.html(html, height=550, scrolling=False)

    with col2:
        st.subheader("Resumen")
        st.write(f"**Nodos:** {G.number_of_nodes()} almacenes")
        st.write(f"**Aristas:** {G.number_of_edges()} rutas")
        st.write("**Nodos:** A (Norte), B (Sur), C (Este), D (Oeste), E (Centro).")
        st.write("**Leyenda:** Nodos en rojo = cuello de botella (grado ≥ 3). Tamaño proporcional al grado.")
        st.divider()
        st.write("**Rutas (ejemplos):**")
        for u, v in list(G.edges())[:5]:
            e = G.edges[u, v]
            st.write(f"- {u} → {v}: {e.get('route_id', '')} ({e.get('distance_km', 0):.0f} km)")

if __name__ == "__main__":
    main()
