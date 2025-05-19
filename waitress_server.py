from waitress import serve
from app import app

if __name__ == "__main__":
    # Get config from Flask app
    port = app.config['PORT']
    host = app.config['HOST']
    print(f"Starting Waitress server on {host}:{port}...")
    serve(app, host=host, port=port)
