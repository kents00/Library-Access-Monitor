from waitress import serve
from app import app
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT"))
    serve(app, host=app.config['HOST'], port=port)