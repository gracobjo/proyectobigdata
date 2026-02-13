# Punto de entrada para Vercel (serverless).
# Vercel detecta la app FastAPI en app.py, index.py o server.py.
from api.main import app

__all__ = ["app"]
