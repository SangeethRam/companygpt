import logging
from mcp.server.fastmcp import FastMCP
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from difflib import get_close_matches
from dotenv import load_dotenv
from supabase.client import create_client
from typing import List, Tuple
import os

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("DocIngestorAndRetrieval")

# Config
INGESTOR_SERVER_PORT = os.getenv("INGESTOR_SERVER_PORT")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_NAME = "documents"

logger.info("Starting DocIngestorAndRetrieval MCP server...")
logger.debug(f"Using Supabase URL: {SUPABASE_URL}")
logger.debug(f"Using Supabase Table: {SUPABASE_TABLE_NAME}")

# Init MCP and Supabase client
mcp = FastMCP("DocIngestorAndRetrieval", port=INGESTOR_SERVER_PORT, dependencies=["langchain", "langchain_community"])

try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
logger.info("Embedding model initialized.")

def get_supabase_vectorstore():
    logger.debug("Creating SupabaseVectorStore instance...")
    return SupabaseVectorStore(
        embedding=embedding_model,
        client=supabase_client,
        table_name=SUPABASE_TABLE_NAME,
        query_name="match_documents"
    )

@mcp.tool(
    name="Search_Documents",
    description="Search the documents for relevant content related to doc based on a query.",
)
def search_documents(query: str, k: int = 5, min_score: float = 0.75) -> list[str]:
    """
    Search the Supabase vector store for relevant content based on a query.
    Returns top-k matches.
    """
    logger.info(f"Search_Documents called with query='{query}', k={k}")
    try:
        vectorstore = get_supabase_vectorstore()
        docs = vectorstore.similarity_search(query, k=k)
        logger.debug(f"Retrieved {len(docs)} documents from Supabase")

        return [doc.page_content for doc in docs]
    except Exception as e:
        logger.error(f"Error in Search_Documents: {e}", exc_info=True)
        return [f"Error executing Search_Documents: {str(e)}"]


@mcp.tool(
    name="Get_Page_Content",
    description="Retrieve the raw text from a specific page of a document with fuzzy filename match."
)
def get_page_content(page_number: int, filename_hint: str) -> str:
    logger.info(f"Get_Page_Content called with page_number={page_number}, filename_hint='{filename_hint}'")
    resolved_file = resolve_filename(filename_hint)
    if not resolved_file:
        logger.warning(f"No matching file found for '{filename_hint}'.")
        return f"No matching file found for '{filename_hint}'."

    logger.debug(f"Resolved filename: {resolved_file}")

    try:
        response = supabase_client.table(SUPABASE_TABLE_NAME) \
            .select("content, metadata") \
            .eq("metadata->>source_file", resolved_file) \
            .order("metadata->>page_number", desc=False) \
            .execute()

        chunks = response.data if response and response.data else []
        logger.debug(f"Found {len(chunks)} chunks for file '{resolved_file}'.")

        if not chunks:
            logger.warning(f"No pages found for file '{resolved_file}'.")
            return f"No pages found for file '{resolved_file}'."

        if page_number < 1 or page_number > len(chunks):
            logger.warning(f"Page number {page_number} out of range for file '{resolved_file}' with {len(chunks)} pages.")
            return f"Page {page_number} is out of range. This document has {len(chunks)} pages."

        chunk = chunks[page_number - 1]
        return f"Content from '{resolved_file}' page {page_number}:\n\n{chunk['content']}"

    except Exception as e:
        logger.error(f"Error retrieving page content: {e}", exc_info=True)
        return f"Error retrieving page content: {str(e)}"

def resolve_filename(user_input: str) -> str | None:
    logger.info(f"Resolving filename for input '{user_input}'")
    try:
        response = supabase_client.table(SUPABASE_TABLE_NAME) \
            .select("metadata") \
            .execute()
        
        files = list({
            entry["metadata"].get("source_file")
            for entry in response.data
            if entry.get("metadata") and entry["metadata"].get("source_file")
        })
        logger.debug(f"Unique source_file values retrieved: {files}")

        matches = get_close_matches(user_input.lower(), [f.lower() for f in files], n=1, cutoff=0.5)
        if matches:
            for f in files:
                if f.lower() == matches[0]:
                    logger.info(f"Fuzzy matched '{user_input}' to file '{f}'")
                    return f
        logger.warning(f"No fuzzy match found for '{user_input}'")
        return None

    except Exception as e:
        logger.error(f"Error resolving filename: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Running MCP server...")
    mcp.run(transport="sse")
