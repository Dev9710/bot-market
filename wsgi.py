"""
WSGI entry point for Gunicorn
"""
from railway_db_api import app

if __name__ == "__main__":
    app.run()
