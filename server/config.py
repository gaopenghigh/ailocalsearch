"""
Configuration settings for the application.
This module contains constants and settings that can be adjusted without modifying the core code.
"""

import os

# this will be part of the system prompt
AI_ASSISTANT_NAME = "AKS Wiki Assistant"

# this will be part of the system prompt
LOCAL_KNOWLEDGE_BASE_DESCRIPTION = """
This knowledge base is owned by AKS (Azure Kubernetes Service) engineering team, used to share technical details of AKS.
It contains internal wikis, TSG docs, and personal wikis, all are technical documents.
"""

# Directory paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_SUMMARY_DIR = os.path.join(DATA_DIR, "summary")
CHROMA_DATA_DIR = os.path.join(DATA_DIR, "chroma")

# Default file path ignore patterns 
# Files that match these regex patterns will be ignored during processing
FILE_PATH_IGNORE_REGEX = [
    r".*/Archive/.*",   # Ignore archived files
    r".*/Weekly-Meetings/.*", # Ignore weekly meeting files
    r".*/Meeting-notes/.*", # Ignore meeting notes files
    r".*/.*\(Archived\).*",  # Ignore files with (Archived) in the path
    r".*/Weekly/.*",  # Ignore files with Weekly in the path
]

# Concurrency settings
DEFAULT_MAX_WORKERS = 5  # Default number of parallel workers for summary generation

# Vector store search settings
VECTOR_STORE_SEARCH_TOP_K = 50

# HTTP server settings
HTTP_SERVER_HOST = '0.0.0.0'
HTTP_SERVER_PORT = 5001
DEBUG_MODE = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t", "yes")
