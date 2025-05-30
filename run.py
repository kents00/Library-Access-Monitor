from waitress import serve
from app import app
import os

if __name__ == "__main__":
    # Get PORT from environment variable with fallback to 1000 (from .env)
    port = int(os.environ.get("PORT", 1000))
    # Get HOST from environment variable with fallback to 0.0.0.0 (from .env)
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting server on {host}:{port}")
    serve(app, host=host, port=port)