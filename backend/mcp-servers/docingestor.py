from mcp.server.fastmcp import FastMCP
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
# from langchain.embeddings import HuggingFaceEmbeddings
from difflib import get_close_matches
import os
from typing import List, Tuple
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dotenv import load_dotenv
load_dotenv()

INGESTOR_SERVER_PORT = os.getenv("INGESTOR_SERVER_PORT")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
mcp = FastMCP("DocIngestorandRetrival", port=INGESTOR_SERVER_PORT, dependencies=["langchain", "langchain_community"])
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
PERSIST_DIR = os.path.join(BACKEND_DIR, "data", "embeddings")
DOCUMENTS_DIR = os.path.join(BACKEND_DIR, "data", "documents", "Policies")
# EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

@mcp.tool(
    name="Persist_documents",
    description="Load, chunk, embed, and store all PDFs from the specified folder.",
)
def persist_documents_from_folder(folder_path: str = DOCUMENTS_DIR) -> str:
    """ Load, chunk, embed, and store all PDFs from the specified folder.
    Args:
        folder_path (str): Path to the folder containing PDF documents. Defaults to DOCUMENTS_DIR.

    Returns:
        str: Message indicating the number of documents persisted or an error message.
    """

    if not os.path.exists(folder_path):
        return f"Folder '{folder_path}' does not exist."

    docs = []
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(folder_path, file))
            pages = loader.load()
            for i, page in enumerate(pages):
                page.metadata["source_file"] = file
                page.metadata["page_number"] = i + 1
                docs.append(page)


    if not docs:
        return "No PDF files found."

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    documents = text_splitter.split_documents(docs)

    vectorstore = Chroma.from_documents(documents, EMBEDDING_MODEL, persist_directory=PERSIST_DIR)
    vectorstore.persist()

    return f"{len(documents)} documents persisted to Chroma DB from '{folder_path}'"

@mcp.tool(
    name="Search_Documents",
    description="Search the documents for relevant content related to doc based on a query.",
)
def search_documents(query: str, k: int = 5, min_score: float = 0.75) -> list[str]:
    """ 
    Search the documents for relevant content based on a query.
    Returns top-k matching chunks

    Args:
        query (str): The search query string to look for in the documents.
        k (int, optional): The number of top matching document chunks to return. Defaults to 3.
        min_score (float, optional): The minimum cosine similarity score threshold for filtering results. Defaults to 0.75.
    Returns:
        list[str]: A list of the top-k matching document chunk contents as strings.
    """
    vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=EMBEDDING_MODEL)

    # Normal Similarity search

    print(f"Searching for '{query}' in {PERSIST_DIR} with k={k}")
    # results = vectorstore.similarity_search(query, k=k)
    # return [doc.page_content for doc in results]

    # Similarity search with scores
    results: List[Tuple] = vectorstore.similarity_search_with_score(query, k=k * 2)  # fetch more, filter below
    # # Filter by cosine similarity threshold
    filtered = [doc.page_content for doc, score in results if score <= min_score]

    # # Limit to top-k after filtering
    print(f"Resolved results: {results}")
    return filtered[:k]

@mcp.tool(
    name="Get_Page_Content",
    description="Retrieve the raw text from a specific page of a document with fuzzy filename match."
)
def get_page_content(page_number: int, filename_hint: str) -> str:
    """
    Retrieve the raw text from a specific page of a document with fuzzy filename match.

    Args:
        page_number (int): The page number to retrieve (1-based index).
        filename_hint (str): A hint or partial name to identify the PDF file.

    Returns:
        str: The raw text content of the specified page, or an error message if not found.
    """
    resolved_file = resolve_filename(filename_hint)
    print(f"Resolved file: {resolved_file}")
    if not resolved_file:
        return f"No matching file found for '{filename_hint}'."

    path = os.path.join(DOCUMENTS_DIR, resolved_file)
    loader = PyPDFLoader(path)
    pages = loader.load()

    if page_number < 1 or page_number > len(pages):
        return f"Page {page_number} is out of range. This document has {len(pages)} pages."

    return f"Content from '{resolved_file}' page {page_number}:\n\n{pages[page_number - 1].page_content}"

def resolve_filename(user_input: str, folder_path: str = DOCUMENTS_DIR) -> str | None:
    """
    Tries to match a fuzzy filename description to a real filename.
    Returns the best match or None.
    """
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    matches = get_close_matches(user_input.lower(), [f.lower() for f in files], n=1, cutoff=0.5)
    
    if matches:
        # Return the original filename with correct case
        for f in files:
            if f.lower() == matches[0]:
                return f
    return None

if __name__ == "__main__":
    mcp.run(transport="sse")
