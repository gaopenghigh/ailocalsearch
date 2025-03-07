import os
from flask import Flask, Response, request, jsonify, send_from_directory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import tool
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import db
from config import AI_ASSISTANT_NAME, LOCAL_KNOWLEDGE_BASE_DESCRIPTION
# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Set up the path to the React build directory
react_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'build'))

app = Flask(__name__, static_folder=react_build_dir)
CORS(app)

llm = ChatOpenAI(
    model="gpt-4o", 
    streaming=False  # Changed to False since we don't need streaming
)

vector_store = db.get_vector_store()


@tool
def search(question: str) -> str:
    """
    This tool is used to answer questions by searching through available documentation from local knowledge base.
    Args:
        query: The question to answer
    Returns:
        A string containing the search results
    """
    return db.search(vector_store, question, 50)


def new_search_agent():
    # Define the system prompt
    system_prompt = f"""Your are {AI_ASSISTANT_NAME}, an AI assistant to help to answer questions based on local knowledge base.
{LOCAL_KNOWLEDGE_BASE_DESCRIPTION}

Always use tools to answer technical questions.
Do not make up information.
If you can't find relevant information, say so.

To answer a question:
1. Understand what the user is asking
2. Use the search tool to find relevant information
3. Generate a comprehensive answer

Try your best to provide a clear and accurate answer based solely on the search results, in 3 parts
- Summary
- Detail, don't miss any details
- Sources (extract the "Source" part of the search results, it's a file path, not a link)
"""    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "QUESTION: {input}")
    ])

    tools = [search]
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    return agent_executor


@app.route('/api/answer', methods=['GET'])
def answer():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    agent_executor = new_search_agent()
    result = agent_executor.invoke({"input": query})
    return jsonify({
        "response": result,
        "ai_assistant_name": AI_ASSISTANT_NAME
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