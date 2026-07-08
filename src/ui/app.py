"""
Phase 5: User Interface (Minimal)

A lightweight Streamlit web application providing a chat interface 
for the HDFC Mutual Fund FAQ Assistant.
"""
import os
import sys
import streamlit as st

# Suppress HuggingFace warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Ensure src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.rag.chain import get_rag_chain, ask_question
from src.config import DISCLAIMER

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="HDFC Mutual Fund FAQ Assistant",
    page_icon="📈",
    layout="centered"
)

# ==========================================
# Application State
# ==========================================
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize RAG chain (cached to avoid reloading models on every interaction)
@st.cache_resource(show_spinner="Initializing AI Models...")
def load_chain():
    try:
        return get_rag_chain()
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Failed to load AI Models: {e}")
        st.stop()

chain = load_chain()

# ==========================================
# Header & UI Layout
# ==========================================
st.title("📈 HDFC Mutual Fund FAQ Assistant")

st.markdown(
    f"""
    <div style="padding: 10px; background-color: #ffe6e6; border-left: 5px solid #ff4d4d; color: #cc0000; font-size: 14px;">
        <strong>⚠️ DISCLAIMER:</strong> {DISCLAIMER}
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.write("Welcome! I can answer factual questions based on official HDFC mutual fund documentation.")

# ==========================================
# Example Questions
# ==========================================
st.markdown("### 💡 Example Questions")
col1, col2 = st.columns(2)

# We use buttons that set a session state variable to trigger a query
if "preset_query" not in st.session_state:
    st.session_state.preset_query = None

def set_query(q):
    st.session_state.preset_query = q

with col1:
    if st.button("What is the expense ratio of HDFC Mid-Cap Fund?"):
        set_query("What is the expense ratio of HDFC Mid-Cap Fund?")
    if st.button("What is the AUM of HDFC Defence Fund?"):
        set_query("What is the AUM of HDFC Defence Fund?")
with col2:
    if st.button("What is the minimum SIP for HDFC Silver ETF?"):
        set_query("What is the minimum SIP for HDFC Silver ETF?")
    if st.button("Should I invest in HDFC Mid-Cap Fund?"):
        set_query("Should I invest in HDFC Mid-Cap Fund?")

st.divider()

# ==========================================
# Chat Interface
# ==========================================
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Determine if we have a preset query or user input
user_input = st.chat_input("Ask a question about HDFC mutual funds...")
query = st.session_state.preset_query if st.session_state.preset_query else user_input

# Process the query
if query:
    # Reset the preset query
    st.session_state.preset_query = None
    
    # Display user message in chat message container
    st.chat_message("user").markdown(query)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Searching official documents..."):
            try:
                response = ask_question(query, chain)
                st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"An error occurred: {e}")
