# Standard library imports
import os

# Third-party imports
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

# Local imports
import db
from config import (
    AI_ASSISTANT_NAME,
    LOCAL_KNOWLEDGE_BASE_DESCRIPTION,
    VECTOR_STORE_SEARCH_TOP_K,
    DEBUG_MODE
)

# Load environment variables from .env file
load_dotenv()

# load vector store
vector_store = db.get_vector_store()


def get_llm():
    """Get the LLM based on the OPENAI_API_PROVIDER environment variable."""
    if os.getenv("OPENAI_API_PROVIDER") == "azure":
        return AzureChatOpenAI(
            model=os.getenv("AZURE_OPENAI_MODEL"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
    else:
        return ChatOpenAI(
            model=os.getenv("OPENAI_API_MODEL"),
            streaming=False  # Changed to False since we don't need streaming
        )

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
    llm = get_llm()
    tools = [search]
    return create_react_agent(llm, tools, prompt=prompt, debug=DEBUG_MODE)


def get_answer(query: str, history=None) -> str:
    """
    Get the answer to a question based on the local knowledge base.
    """
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
