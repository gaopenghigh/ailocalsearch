# Standard library imports
import logging
import os

# Third-party imports
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Local imports
import ai
from config import (
    AI_ASSISTANT_NAME,
    LOCAL_KNOWLEDGE_BASE_DESCRIPTION,
    HTTP_SERVER_HOST,
    HTTP_SERVER_PORT,
    DEBUG_MODE
)

# Configure logging
# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO, 
    force=True,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/app.log',
    filemode='a'
)


# Load environment variables from .env file
load_dotenv()

# Set up the path to the React build directory
react_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'build'))
app = Flask(__name__, static_folder=react_build_dir)
CORS(app)

# API Endpoints
@app.route('/api/answer', methods=['POST'])
def api_answer():
    data = request.json
    query = data.get('query', '')
    history = data.get('history', [])
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    answer = ai.get_answer(query, history)
    
    # Add the new Q&A pair to history
    history.append({
        "question": query,
        "answer": answer
    })
    
    return jsonify({
        "question": query,
        "answer": answer,
        "history": history
    })

# Add API endpoint to get assistant description
@app.route('/api/description', methods=['GET'])
def api_description():
    """Return the description of this assistant."""
    return jsonify({
        "name": AI_ASSISTANT_NAME,
        "description": LOCAL_KNOWLEDGE_BASE_DESCRIPTION
    })

# Serve React App - static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, host=HTTP_SERVER_HOST, port=HTTP_SERVER_PORT)
