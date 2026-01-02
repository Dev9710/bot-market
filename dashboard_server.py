"""
Simple Flask server to serve the dashboard HTML
"""
from flask import Flask, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def dashboard():
    """Serve the dashboard HTML file."""
    return send_file('dashboard_frontend.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
