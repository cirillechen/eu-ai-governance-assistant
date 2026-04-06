import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

st.set_page_config(page_title="EU AI Governance Assistant", page_icon="📘")

st.title("EU AI Governance Assistant")
st.caption(
    "Document-grounded support for EU AI and data governance research. "
    "This assistant does not provide legal advice."
)

# ---------- API key ----------
api_key = None

if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found. Please add it in Streamlit Secrets or your local .env file.")
    st.stop()

os.environ["OPENAI_API_KEY"] = api_key

# ---------- Demo questions ----------
demo_questions = [
    "What is the purpose of the EU AI Act?",
    "What is personal data under GDPR?",
    "What does the Data Governance Act regulate?",
    "What is the difference between GDPR and the AI Act?",
    "What should a company check before using AI in recruitment?",
    "When do the main obligations of the AI Act start to apply?",
]

if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

st.subheader("Example questions")
col1, col2 = st.columns(2)

for i, question in enumerate(demo_questions):
    if i % 2 == 0:
        if col1.button(question, key=f"q_{i}", use_container_width=True):
            st.session_state.selected_question = question
    else:
        if col2.button(question, key=f"q_{i}", use_container_width=True):
            st.session_state.selected_question = question


# ---------- Build or load vectorstore ----------
@st.cache_resource
def get_vectorstore():
    embeddings = OpenAIEmbeddings()
    vectorstore_path = "vectorstore"
    data_path = Path("data/raw")

    if os.path.exists(vectorstore_path):
        return FAISS.load_local(
            vectorstore_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

    documents = []

    for file_path in data_path.glob("*"):
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
            documents.extend(loader.load())
        elif suffix == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents.extend(loader.load())

    if not documents:
        raise ValueError("No documents found in data/raw.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(vectorstore_path)
    return vectorstore


with st.spinner("Loading knowledge base..."):
    vectorstore = get_vectorstore()

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ---------- User input ----------
query = st.text_input(
    "Ask a question about EU AI / GDPR / Data Governance:",
    value=st.session_state.selected_question
)

if query:
    with st.spinner("Searching documents and drafting answer..."):
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
You are an AI assistant supporting EU AI and data governance research.

Your role:
- Answer only based on the provided context
- Be concise, clear, and useful
- If the answer is not in the context, say:
  "I don't know based on the provided documents."
- Do not provide legal advice
- When relevant, mention the regulation or source document name

Context:
{context}

Question:
{query}
"""

        response = llm.invoke(prompt)

    st.subheader("Answer")
    st.write(response.content)

    with st.expander("View sources"):
        for i, doc in enumerate(docs, 1):
            source = os.path.basename(doc.metadata.get("source", "Unknown source"))
            page = doc.metadata.get("page", "N/A")
            snippet = doc.page_content[:300].replace("\n", " ").strip()

            st.markdown(f"**{i}. {source} — Page {page}**")
            st.caption(snippet + "...")