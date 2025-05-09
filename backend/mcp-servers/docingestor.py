from mcp.server.fastmcp import FastMCP
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from difflib import get_close_matches
import os
from dotenv import load_dotenv
load_dotenv()

INGESTOR_SERVER_PORT = os.getenv("INGESTOR_SERVER_PORT")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
mcp = FastMCP("DocIngestorandRetrival", port=INGESTOR_SERVER_PORT, dependencies=["langchain", "langchain_community"])
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
PERSIST_DIR = os.path.join(BACKEND_DIR, "data", "embeddings")
DOCUMENTS_DIR = os.path.join(BACKEND_DIR, "documents", "Policies")
EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

@mcp.tool(
    name="Persist_documents",
    description="Load, chunk, embed, and store all PDFs from the specified folder.",
)
def persist_documents_from_folder(folder_path: str = DOCUMENTS_DIR) -> str:
    """
    Load, chunk, embed, and store all PDFs from the specified folder.
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
    description="Search the documents for relevant content based on a query.",
)
def search_documents(query: str, k: int = 3) -> list[str]:
    """
    Search the documents for relevant content based on a query.
    Returns top-k matching chunks.
    """
    vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=EMBEDDING_MODEL)
    results = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in results]

@mcp.tool(
    name="Get_Page_Content",
    description="Retrieve the raw text from a specific page of a document with fuzzy filename match."
)
def get_page_content(page_number: int, filename_hint: str) -> str:
    resolved_file = resolve_filename(filename_hint)
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
