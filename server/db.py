import os
import logging
import re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter

import concurrent.futures
import glob

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import configuration settings
try:
    # When imported as a package
    from server.config import (
        DATA_RAW_DIR,
        DATA_SUMMARY_DIR,
        CHROMA_DATA_DIR,
        FILE_PATH_IGNORE_REGEX,
        DEFAULT_MAX_WORKERS
    )
except ImportError:
    # When run directly
    from config import (
        DATA_RAW_DIR,
        DATA_SUMMARY_DIR,
        CHROMA_DATA_DIR,
        FILE_PATH_IGNORE_REGEX,
        DEFAULT_MAX_WORKERS
    )

# Define alias for backward compatibility
DATA_DB_DIR = CHROMA_DATA_DIR

def get_embeddings():
    """Get the embedding model using Hugging Face."""
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    return embeddings


def _generate_summary(content: str) -> str:
    """Generate a summary of content using GPT-4o-mini."""
    llm = ChatOpenAI(model_name="gpt-4o-mini")
    prompt = """You are a helpful assistant that creates concise summaries of technical documents. Please create a concise summary of the following document. Focus on the main points and key information.
        
DOCUMENT:
{content}
""".format(content=content)
    messages = [HumanMessage(content=prompt)]
    return llm.invoke(messages).content.strip()


def _create_summary_file(source_file_path: str):
    """Create a summary file for a source file."""
    # Get the relative path from DATA_RAW_DIR to the source file
    rel_path = os.path.relpath(source_file_path, DATA_RAW_DIR)
    # Create the summary file path by joining DATA_SUMMARY_DIR with the relative path
    summary_file_path = os.path.join(DATA_SUMMARY_DIR, rel_path)
    if os.path.exists(summary_file_path):
        logging.info(f"Skip file {source_file_path} because summary file already exists: {summary_file_path}")
        return
    # Create the summary directory if it doesn't exist
    os.makedirs(os.path.dirname(summary_file_path), exist_ok=True)
    with open(source_file_path, "r") as f:
        content = f.read()
        # Check if content is empty or too short (less than 3 lines)
        if not content or len(content.strip().split('\n')) < 3:
            logging.info(f"Skip file {source_file_path} because content is too short")
            return
        logging.info(f"Generate summary for {source_file_path}")
        summary = _generate_summary(content)
        with open(summary_file_path, "w") as f:
            f.write(summary)


def build_summaries(ignore_file_path_regex: list[str] = FILE_PATH_IGNORE_REGEX, max_workers=DEFAULT_MAX_WORKERS):
    """Build the summaries for the data.
    
    Args:
        data_raw_dir: Directory containing the raw data files
        max_workers: Maximum number of concurrent workers for parallel processing
    """
    # Find all markdown files in the data_raw_dir and its subdirectories
    markdown_files = []
    for root, _, _ in os.walk(DATA_RAW_DIR):
        md_files = glob.glob(os.path.join(root, "*.md"))
        markdown_files.extend(md_files)
    
    logging.info(f"Found {len(markdown_files)} markdown files to process")
    
    # Process the files in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for file_path in markdown_files:
            if any(re.match(pattern, file_path) for pattern in ignore_file_path_regex):
                logging.info(f"Ignore file {file_path}")
                continue
            futures.append(executor.submit(_create_summary_file, file_path))
        
        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error processing file: {e}")
    
    logging.info(f"Completed summary generation for {len(markdown_files)} files")


def build_vector_db():
    """Build the vector database based on Chroma."""
    for data_dir in [DATA_SUMMARY_DIR, DATA_RAW_DIR]:
        _build_vector_db(data_dir)


def _build_vector_db(data_dir: str, file_path_ignore_regex: list[str] = FILE_PATH_IGNORE_REGEX):
    """Build the vector database based on Chroma.
    
    Args:
        data_dir: Directory containing the data files
        file_path_ignore_regex: List of regex patterns to ignore
    """
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        silent_errors=True,
        show_progress=True,
        use_multithreading=True,
    )
    documents = loader.load()
    for doc in documents:
        if any(re.match(pattern, doc.metadata["source"]) for pattern in file_path_ignore_regex):
            logging.info(f"Ignore file {doc.metadata['source']}")
            documents.remove(doc)

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    all_chunks = []
    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        for chunk in chunks:
            chunk.metadata["title"] = os.path.basename(doc.metadata["source"])
            # Convert source path to relative path by removing the base directory prefix
            source = doc.metadata["source"]
            if source.startswith(DATA_RAW_DIR):
                source = os.path.relpath(source, DATA_RAW_DIR)
            elif source.startswith(DATA_SUMMARY_DIR):
                source = os.path.relpath(source, DATA_SUMMARY_DIR)
            chunk.metadata["source"] = source
            all_chunks.append(chunk)

    os.makedirs(DATA_DB_DIR, exist_ok=True)
    Chroma.from_documents(
        documents=all_chunks,
        embedding=get_embeddings(),
        persist_directory=DATA_DB_DIR,
    )


def get_vector_store(persist_directory: str = DATA_DB_DIR) -> Chroma:
    """Get an existing Chroma vector store."""
    return Chroma(
        embedding_function=get_embeddings(),
        persist_directory=persist_directory,
    )

def search(vector_store: Chroma, query: str, k: int = 50) -> str:
    logging.info(f"Searching for {query}")
    docs = vector_store.similarity_search(query, k=k)
    
    references = {}
    for doc in docs:
        source = doc.metadata["source"]
        logging.info(f"Processing {source}")
        ref = {}
        if _is_filepath_a_summary_doc(source):
            ref["source"] = _get_original_doc_path(source)
            ref["summary"] = _get_summary_doc_content(source)
        else:
            ref["source"] = source
            summary_doc_path = _get_summary_doc_path(source)
            ref["summary"] = _get_summary_doc_content(summary_doc_path)
        if ref["source"] not in references:
            references[ref["source"]] = ref
    
    result = ""
    for source, ref in references.items():
        source = source.replace(DATA_RAW_DIR, "").replace(DATA_SUMMARY_DIR, "")
        result += f"Source: {source}\n\n{ref['summary']}\n"
        result += "\n----\n\n"
    return result


def _get_summary_doc_path(source: str) -> str:
    """Replace the prefix DATA_RAW_DIR with DATA_SUMMARY_DIR in the source path."""
    return os.path.join(DATA_SUMMARY_DIR, source)

def _get_original_doc_path(source: str) -> str:
    """Replace the prefix DATA_SUMMARY_DIR with DATA_RAW_DIR in the source path."""
    return os.path.join(DATA_RAW_DIR, source)

def _get_summary_doc_content(source: str) -> str:
    """get the content of the summary doc"""
    return _get_file_content(_get_summary_doc_path(source))

def _get_original_doc_content(source: str) -> str:
    """get the content of the original doc"""
    return _get_file_content(_get_original_doc_path(source))

def _get_file_content(file_path: str) -> str:
    """get the content of the file, return None if the file does not exist"""
    if not os.path.exists(file_path):
        return None
    return open(file_path, "r").read()

def _is_filepath_a_summary_doc(file_path: str) -> bool:
    """check if the file path is a summary doc"""
    return file_path.startswith(DATA_SUMMARY_DIR)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_summaries()
    build_vector_db()
    vector_store = get_vector_store()
    print(search(vector_store, "AKS", 5))

