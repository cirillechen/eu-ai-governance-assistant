import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please check your .env file.")

# Load embeddings
embeddings = OpenAIEmbeddings()

# Load saved vectorstore
vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

# Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Ask a question
question = input("Ask a question about EU AI/data regulations: ")

# Retrieve relevant docs
docs = retriever.invoke(question)

print("\n--- Retrieved Sources ---")
for i, doc in enumerate(docs, 1):
    source = doc.metadata.get("source", "Unknown source")
    page = doc.metadata.get("page", "Unknown page")
    print(f"{i}. Source: {source}, Page: {page}")

context = "\n\n".join([doc.page_content for doc in docs])

# Prompt
prompt = f"""
You are an assistant for EU AI and data governance regulations.

Answer the user's question only based on the context below.
If the answer is not in the context, say: "I don't know based on the provided documents."

Context:
{context}

Question:
{question}
"""

# Generate answer
response = llm.invoke(prompt)

print("\n--- Answer ---")
print(response.content)