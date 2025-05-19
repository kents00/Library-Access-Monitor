from app import app

if __name__ == "__main__":
    # This block only executes when run directly, not when imported
    # This allows for local development with "python wsgi.py"
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
