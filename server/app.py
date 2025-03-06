import os
from flask import Flask, Response, request, jsonify
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

app = Flask(__name__)
CORS(app)

llm = ChatOpenAI(
    model="gpt-4o", 
    streaming=False  # Changed to False since we don't need streaming
)

vector_store = db.get_vector_store()


@tool
def answer_question_by_search(question):
    """
    This tool is used to answer questions by searching through available documentation from local knowledge base.
    Args:
        query: The question to answer
    Returns:
        A string containing the search results
    """
    search_results = db.search(vector_store, question, 20)
    prompt = f"""
    You are an AI assistant to help answer questions based on local knowledge.
    Answer the following question based on the provided information.
    If you don't know the answer based on the provided information, say so.
    Do not make up information.
    
    QUESTION: {question}
    
    INFORMATION:
    {search_results}
    
    Please provide a clear and accurate answer based solely on the information provided, in 3 segments:
    1. Summary of the answer
    2. Detailed answer, with all the details
    3. Sources
    """
    logging.info(search_results)
    response = llm.invoke(prompt)
    return response.content


def new_search_agent():
    # Define the system prompt
    system_prompt = f"""
    Your are {AI_ASSISTANT_NAME}, AI assistant to answer questions based on local knowledge base.
    {LOCAL_KNOWLEDGE_BASE_DESCRIPTION}

    You help answer technical questions by using the search tool.
    To answer a question:
    1. Understand what the user is asking
    2. Use the search tool to find relevant information
    3. Generate a comprehensive answer
    
    Always use the tools provided, tools can be called multiple times if needed.
    Do not make up information.
    If you can't find relevant information, say so.
    
    Try your best to provide a clear and accurate answer based solely on the search results, in 3 parts
    - Summary
    - Detail, don't miss any details
    - Sources
    """
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "{input}")
    ])

    tools = [answer_question_by_search]
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)