from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import create_client
import os

# === Load ENV ===
from dotenv import load_dotenv
load_dotenv()

# === ENV Vars ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_NAME ="documents"

# === Paths ===
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
PERSIST_DIR = os.path.join(BACKEND_DIR, "data", "embeddings")
DOCUMENTS_DIR = os.path.join(BACKEND_DIR, "data", "documents", "Policies")

# === Embedding model ===
EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

# === Supabase Client ===
supabase_client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# === Load and process documents ===
docs = []
for file in os.listdir(DOCUMENTS_DIR):
    if file.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(DOCUMENTS_DIR, file))
        pages = loader.load()
        for i, page in enumerate(pages):
            page.metadata["source_file"] = file
            page.metadata["page_number"] = i + 1
            docs.append(page)

# === Chunk text ===
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
documents = text_splitter.split_documents(docs)

print(f"✅ Loaded {len(documents)} chunks from PDFs in {DOCUMENTS_DIR}")
print(f"Example chunk:\n{documents[0].page_content[:200]}...\n")

# === Store in Supabase vector DB ===
vectorstore = SupabaseVectorStore.from_documents(
    documents=documents,
    embedding=EMBEDDING_MODEL,
    client=supabase_client,
    table_name=SUPABASE_TABLE_NAME
)

print("✅ Embeddings stored in Supabase Vector DB")
