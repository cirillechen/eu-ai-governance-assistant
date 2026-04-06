import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please create a .env file.")

docs = []
folder_path = "data/raw"

for file in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file)

    if file.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        loaded_docs = loader.load()
        docs.extend(loaded_docs)
        print(f"Loaded PDF: {file} ({len(loaded_docs)} pages)")

    elif file.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
        loaded_docs = loader.load()
        docs.extend(loaded_docs)
        print(f"Loaded TXT: {file}")

if not docs:
    raise ValueError("No supported documents found in data/raw")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

chunks = text_splitter.split_documents(docs)
print(f"Split into {len(chunks)} chunks")

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("vectorstore")

print("Vectorstore saved successfully!")