# Standard library imports
import logging
import os
from typing import Any, Iterator
import json

# Third-party imports
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from langchain.tools import tool
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Local imports
import db
from config import AI_ASSISTANT_NAME, LOCAL_KNOWLEDGE_BASE_DESCRIPTION, VECTOR_STORE_SEARCH_TOP_K

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Set up the path to the React build directory
react_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'build'))

app = Flask(__name__, static_folder=react_build_dir)
CORS(app)

llm = ChatOpenAI(
    model="gpt-4o-mini", 
    streaming=False  # Changed to False since we don't need streaming
)

# Set debug mode based on environment variable
debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t", "yes")

vector_store = db.get_vector_store()

@tool
def search(question: str) -> str:
    """
    This tool is used to answer questions by searching through available documentation from local knowledge base.
    Args:
        question: The question to answer
    Returns:
        A string containing the search results
    """
    return db.search(vector_store, question, VECTOR_STORE_SEARCH_TOP_K)


def create_answer_agent() -> Runnable:
    """
    Create a graph that can answer questions based on local knowledge base.
    """
    prompt = f"""Your are {AI_ASSISTANT_NAME}, an AI assistant to help to answer questions based on local knowledge base.
{LOCAL_KNOWLEDGE_BASE_DESCRIPTION}

Always use tools to answer technical questions.
Do not make up information.
If you can't find relevant information, say so.

To answer a question:
1. Understand what the user is asking
2. Use the search tool to find relevant information, try to call it multiple times with different queries if needed
3. Generate a comprehensive answer

Provide answer based solely on the search results, in 3 parts
- Summary
- Detail, be comprehensive, verbose, detailed and accurate, include examples if needed
- Sources (extract the "Source" part of the search results, it's a file path, not a link)
"""
    tools = [search]
    return create_react_agent(llm, tools, prompt=prompt, debug=debug)


def _get_answer(query: str, history=None) -> str:
    agent = create_answer_agent()
    messages = []
    
    # Add conversation history if provided
    if history and isinstance(history, list):
        for entry in history:
            if 'question' in entry and 'answer' in entry:
                messages.append(("human", entry['question']))
                messages.append(("assistant", entry['answer']))
    
    # Add the current query
    messages.append(("human", query))
    
    # Invoke the agent with the messages
    a = agent.invoke({"messages": messages})
    return a["messages"][-1].content

# API Endpoints
@app.route('/api/answer', methods=['POST'])
def api_answer():
    data = request.json
    query = data.get('query', '')
    history = data.get('history', [])
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    answer = _get_answer(query, history)
    
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
    app.run(debug=True, port=5001)