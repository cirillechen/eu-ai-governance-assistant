import os
import requests
import streamlit as st

st.set_page_config(page_title="EU AI Governance Assistant", page_icon="📘")

st.title("EU AI Governance Assistant")
st.caption(
    "Document-grounded support for EU AI and data governance research. "
    "This assistant does not provide legal advice."
)

# ---------- Backend API URL ----------
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/ask")

st.caption(f"Current API URL: {API_URL}")

# ---------- Session state ----------
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- Demo questions ----------
demo_questions = [
    "What is the purpose of the EU AI Act?",
    "What is personal data under GDPR?",
    "What does the Data Governance Act regulate?",
    "What is the difference between GDPR and the AI Act?",
    "What should a company check before using AI in recruitment?",
    "When do the main obligations of the AI Act start to apply?",
]

st.subheader("Example questions")
col1, col2 = st.columns(2)

for i, question in enumerate(demo_questions):
    if i % 2 == 0:
        if col1.button(question, key=f"q_{i}", use_container_width=True):
            st.session_state.selected_question = question
    else:
        if col2.button(question, key=f"q_{i}", use_container_width=True):
            st.session_state.selected_question = question

# ---------- User input ----------
query = st.text_input(
    "Ask a question about EU AI / GDPR / Data Governance:",
    value=st.session_state.selected_question
)

col_a, col_b = st.columns([1, 1])

with col_a:
    ask_clicked = st.button("Ask")
with col_b:
    clear_clicked = st.button("Clear history")

if clear_clicked:
    st.session_state.chat_history = []
    st.session_state.selected_question = ""
    st.rerun()

# ---------- Ask backend ----------
if ask_clicked and query.strip():
    with st.spinner("Sending query to backend API..."):
        try:
            response = requests.post(
                API_URL,
                json={"question": query},
                timeout=120
            )
            response.raise_for_status()
            result = response.json()

            answer = result.get("answer", "No answer returned.")
            sources = result.get("sources", [])
            metadata = result.get("metadata", {})

            st.session_state.chat_history.append(
                {
                    "question": query,
                    "answer": answer,
                    "sources": sources,
                    "metadata": metadata
                }
            )

            st.session_state.selected_question = query

        except requests.exceptions.ConnectionError:
            st.error(
                f"Could not connect to the backend API at {API_URL}. "
                "Make sure the backend service is running."
            )
        except requests.exceptions.Timeout:
            st.error("The backend API request timed out.")
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ---------- Current answer ----------
if st.session_state.chat_history:
    latest_item = st.session_state.chat_history[-1]

    st.subheader("Latest Answer")
    st.write(latest_item["answer"])

    with st.expander("View sources for latest answer"):
        if latest_item["sources"]:
            for i, source_item in enumerate(latest_item["sources"], 1):
                source_path = source_item.get("source", "Unknown source")
                source = os.path.basename(source_path)
                page = source_item.get("page", "N/A")

                st.markdown(f"**{i}. {source} — Page {page}**")

                if source_path and source_path != "Unknown source":
                    abs_path = os.path.abspath(source_path)
                    st.markdown(f"[Open document](file:///{abs_path})")
        else:
            st.caption("No sources returned.")

    if latest_item.get("metadata"):
        with st.expander("View system metadata"):
            st.json(latest_item["metadata"])

# ---------- Conversation history ----------
st.subheader("Conversation History")

if st.session_state.chat_history:
    for idx, item in enumerate(reversed(st.session_state.chat_history), 1):
        question_number = len(st.session_state.chat_history) - idx + 1

        with st.expander(f"Q{question_number}: {item['question']}"):
            st.markdown("**Answer:**")
            st.write(item["answer"])

            st.markdown("**Sources:**")
            if item["sources"]:
                for j, source_item in enumerate(item["sources"], 1):
                    source_path = source_item.get("source", "Unknown source")
                    source = os.path.basename(source_path)
                    page = source_item.get("page", "N/A")

                    st.markdown(f"- {j}. {source} — Page {page}")

                    if source_path and source_path != "Unknown source":
                        abs_path = os.path.abspath(source_path)
                        st.markdown(f"[Open document](file:///{abs_path})")
            else:
                st.caption("No sources returned.")

            if item.get("metadata"):
                st.markdown("**Metadata:**")
                st.json(item["metadata"])
else:
    st.caption("No conversation history yet.")

# ---------- Download history ----------
if st.session_state.chat_history:
    export_text = ""

    for idx, item in enumerate(st.session_state.chat_history, 1):
        export_text += f"Question {idx}: {item['question']}\n"
        export_text += f"Answer {idx}: {item['answer']}\n"
        export_text += "Sources:\n"

        if item["sources"]:
            for source_item in item["sources"]:
                source_path = source_item.get("source", "Unknown source")
                source = os.path.basename(source_path)
                page = source_item.get("page", "N/A")
                export_text += f"- {source} — Page {page}\n"
        else:
            export_text += "- No sources returned\n"

        if item.get("metadata"):
            export_text += "Metadata:\n"
            for k, v in item["metadata"].items():
                export_text += f"- {k}: {v}\n"

        export_text += "\n" + ("-" * 60) + "\n\n"

    st.download_button(
        label="Download conversation history",
        data=export_text,
        file_name="eu_ai_governance_history.txt",
        mime="text/plain"
    )