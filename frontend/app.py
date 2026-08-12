import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Loan Agreement Analyser",
    layout="wide"
)

st.title("Loan Agreement Analyser")

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []

tab1, tab2 = st.tabs(["Upload Document", "Query Agreement"])

with tab1:
    st.header("Document Ingestion")
    uploaded_file = st.file_uploader("Select Loan Agreement PDF", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document"):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/ingest", files=files)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["session_id"] = data["session_id"]
                        st.session_state["messages"] = []
                        st.success("Document processed successfully")
                        st.write(f"Session ID: {data['session_id']}")
                        st.write(f"Pages: {data['pages']}")
                        st.write(f"Total Chunks: {data['chunks_created']}")
                        st.write(f"Clauses Identified: {data['clauses_found']}")
                    else:
                        st.error(f"Processing failed: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    if st.session_state["session_id"]:
        st.subheader("Active Session Management")
        if st.button("Clear Active Session"):
            session_id = st.session_state["session_id"]
            try:
                response = requests.delete(f"{API_URL}/session/{session_id}")
                if response.status_code == 200:
                    st.session_state["session_id"] = None
                    st.session_state["messages"] = []
                    st.success("Session deleted successfully")
                    st.rerun()
                else:
                    st.error(f"Failed to clear session: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab2:
    st.header("Interactive Query")
    
    if not st.session_state["session_id"]:
        st.warning("Please upload and process a document in the Upload tab first")
    else:
        st.info(f"Active Session: {st.session_state['session_id']}")
        
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "citations" in msg and msg["citations"]:
                    with st.expander("Show Sources"):
                        for citation in msg["citations"]:
                            st.markdown(f"**Clause {citation['clause_id']} (Page {citation['page']})**")
                            st.write(citation["text"])
                            st.markdown("---")

        if prompt := st.chat_input("Ask a question about your loan agreement"):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Analyzing document context"):
                    payload = {
                        "session_id": st.session_state["session_id"],
                        "question": prompt
                    }
                    try:
                        response = requests.post(f"{API_URL}/query", json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            answer = data["answer"]
                            citations = data["citations"]
                            
                            st.write(answer)
                            if citations:
                                with st.expander("Show Sources"):
                                    for citation in citations:
                                        st.markdown(f"**Clause {citation['clause_id']} (Page {citation['page']})**")
                                        st.write(citation["text"])
                                        st.markdown("---")
                                        
                            st.session_state["messages"].append({
                                "role": "assistant",
                                "content": answer,
                                "citations": citations
                            })
                        elif response.status_code == 404:
                            st.error("Session expired or database cleared. Please re-upload document.")
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error communicating with backend: {str(e)}")