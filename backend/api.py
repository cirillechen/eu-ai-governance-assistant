from fastapi import FastAPI
from pydantic import BaseModel

import os
import logging
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load env
load_dotenv()

# Init app
app = FastAPI()

# ---------- Logging setup ----------
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("rag_app")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Load vectorstore (only once!)
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Request schema
class QueryRequest(BaseModel):
    question: str

# API endpoint
@app.post("/ask")
def ask_question(request: QueryRequest):
    question = request.question

    try:
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
You are an AI assistant supporting EU AI and data governance research.

Your role:
- Answer ONLY based on the context
- Provide a structured and moderately detailed answer
- Use bullet points if helpful
- Explain clearly but do not hallucinate
- If not found, say: "I don't know based on the provided documents."

Context:
{context}

Question:
{question}
"""

        response = llm.invoke(prompt)

        result = {
            "answer": response.content,
            "sources": [
                {
                    "source": doc.metadata.get("source"),
                    "page": doc.metadata.get("page")
                }
                for doc in docs
            ]
        }

        logger.info(
            f"QUERY='{question}' | "
            f"ANSWER_PREVIEW='{response.content[:120]}' | "
            f"SOURCES={result['sources']}"
        )

        return result

    except Exception as e:
        logger.error(f"QUERY='{question}' | ERROR='{str(e)}'")
        raise

@app.get("/health")
def health_check():
    return {"status": "ok"}