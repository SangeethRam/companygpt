from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import os

# Load documents
docs = []
INGESTOR_SERVER_PORT = os.getenv("INGESTOR_SERVER_PORT")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
PERSIST_DIR = os.path.join(BACKEND_DIR, "data", "embeddings")
DOCUMENTS_DIR = os.path.join(BACKEND_DIR, "documents", "Policies")
EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

for file in os.listdir(DOCUMENTS_DIR):
    if file.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(DOCUMENTS_DIR, file))
        pages = loader.load()
        for page in pages:
            # Add page metadata
            page.metadata["source_file"] = file
            docs.append(page)

# Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
documents = text_splitter.split_documents(docs)

print(f"✅ Loaded {len(documents)} documents from {DOCUMENTS_DIR}")
print(documents[0].page_content)
# Load local embedding model
# model = SentenceTransformer("all-MiniLM-L6-v2")
# Store in vector DB (Chroma)
vectorstore = Chroma.from_documents(documents, EMBEDDING_MODEL, persist_directory=PERSIST_DIR)
vectorstore.persist()
print("✅ Embeddings stored locally in Chroma DB")
