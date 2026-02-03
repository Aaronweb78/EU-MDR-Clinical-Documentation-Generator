"""
EU MDR Clinical Documentation Generator
Main Application Entry Point
"""
import streamlit as st
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title="MDR Doc Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    """Load custom CSS styling"""
    css_file = Path("assets/style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize session state
if 'current_project' not in st.session_state:
    st.session_state.current_project = None

# Main page content
st.title("EU MDR Clinical Documentation Generator")
st.caption("Professional offline tool for generating EU MDR clinical documentation")

# Welcome section
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Report Types", "4")
    st.caption("CEP, CER, SSCP, LSR")

with col2:
    st.metric("Offline", "100%")
    st.caption("All processing local")

with col3:
    st.metric("File Types", "5+")
    st.caption("PDF, DOCX, XLSX, TXT")

st.divider()

# Features overview
st.markdown("### Getting Started")

with st.container(border=True):
    st.markdown("**How to Use This Application**")
    st.markdown("""
1. **Create a Project** - Start by creating a new project for your medical device
2. **Upload Files** - Upload all relevant documentation (500+ files supported)
3. **Process Files** - Automatically extract text, classify, and index documents
4. **Review Classification** - Verify and adjust document classifications
5. **Generate Reports** - Create CEP, CER, SSCP, and LSR documents
6. **Export** - Download formatted DOCX files
    """)

# Navigation guide
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("**Document Management**")
        st.markdown("""
- Smart document classification
- Automatic text extraction
- Vector-based search
- Entity extraction
        """)

with col2:
    with st.container(border=True):
        st.markdown("**Report Generation**")
        st.markdown("""
- EU MDR compliant templates
- Local LLM generation (Ollama)
- Section-by-section editing
- Professional DOCX export
        """)

# System status
st.markdown("### System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    try:
        from src.generation.llm_client import OllamaClient
        client = OllamaClient()
        connection = client.test_connection()
        if connection['success']:
            st.success("✓ Ollama Connected")
            st.caption(f"Models: {len(connection.get('models', []))}")
        else:
            st.error("✗ Ollama Not Connected")
            st.caption("Check that Ollama is running")
    except Exception as e:
        st.error("✗ Ollama Not Connected")
        st.caption(str(e))

with status_col2:
    try:
        from src.database.models import get_connection
        conn = get_connection()
        conn.close()
        st.success("✓ Database Ready")
        st.caption("SQLite initialized")
    except Exception as e:
        st.error("✗ Database Error")
        st.caption(str(e))

with status_col3:
    try:
        from src.knowledge_base.vector_store import VectorStore
        vs = VectorStore()
        st.success("✓ Vector Store Ready")
        st.caption("ChromaDB initialized")
    except Exception as e:
        st.error("✗ Vector Store Error")
        st.caption(str(e))

st.markdown("<br>", unsafe_allow_html=True)

# Quick actions
st.markdown("### Quick Actions")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("Manage Projects", use_container_width=True):
        st.switch_page("pages/1_Projects.py")

with action_col2:
    if st.button("Upload Files", use_container_width=True):
        if st.session_state.current_project:
            st.switch_page("pages/2_Upload_Files.py")
        else:
            st.warning("Please select a project first")

with action_col3:
    if st.button("Process Files", use_container_width=True):
        if st.session_state.current_project:
            st.switch_page("pages/3_Process_Files.py")
        else:
            st.warning("Please select a project first")

with action_col4:
    if st.button("Generate Reports", use_container_width=True):
        if st.session_state.current_project:
            st.switch_page("pages/5_Generate_Reports.py")
        else:
            st.warning("Please select a project first")

# Footer
st.divider()
st.caption("EU MDR Clinical Documentation Generator v1.0 | Fully offline | Privacy-focused | Professional quality")

# Sidebar
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("Use the pages above to navigate through the application")

    if st.session_state.current_project:
        st.markdown("---")
        st.markdown("### Current Project")
        st.info(f"{st.session_state.current_project}")

        if st.button("Clear Selection"):
            st.session_state.current_project = None
            st.rerun()

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This application generates EU MDR clinical documentation using:
    - Local LLM (Ollama)
    - Offline processing
    - Vector search (ChromaDB)
    - Professional templates
    """)
