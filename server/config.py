"""
Configuration settings for the application.
This module contains constants and settings that can be adjusted without modifying the core code.
"""

import os

# this will be part of the system prompt
AI_ASSISTANT_NAME = "AKS Wiki Assistant"

# this will be part of the system prompt
LOCAL_KNOWLEDGE_BASE_DESCRIPTION = """
This knowledge base contains AKS internal wikis, TSG docs, and personal wikis.
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
]

# Concurrency settings
DEFAULT_MAX_WORKERS = 5  # Default number of parallel workers for summary generation
