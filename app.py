import os
from dotenv import load_dotenv
import streamlit as st

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found. Please check your .env file.")
    st.stop()

st.set_page_config(page_title="EU AI Governance Assistant", page_icon="📘")

st.title("EU AI Governance Assistant")
st.caption(
    "Document-grounded support for EU AI and data governance research. "
    "This assistant does not provide legal advice."
)

# Demo questions
demo_questions = [
    "What is the purpose of the EU AI Act?",
    "What is personal data under GDPR?",
    "What does the Data Governance Act regulate?",
    "What is the difference between GDPR and the AI Act?",
    "What should a company check before using AI in recruitment?",
    "When do the main obligations of the AI Act start to apply?",
]

# Session state for selected question
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

# Load vector store
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# User input
query = st.text_input(
    "Ask a question about EU AI / GDPR / Data Governance:",
    value=st.session_state.selected_question
)

if query:
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