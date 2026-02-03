"""
Page 7: Settings
Application settings and configuration
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Settings
from src.generation.llm_client import OllamaClient
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

st.set_page_config(page_title="Settings", layout="wide")

# Load CSS
css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Settings</h1>
    <p style="color: #8B949E; margin-top: 0.5rem;">
        Configure application settings and preferences
    </p>
</div>
""", unsafe_allow_html=True)

# Ollama Settings
st.markdown("### Ollama LLM Settings")

col1, col2 = st.columns(2)

with col1:
    ollama_url = st.text_input(
        "Ollama Server URL",
        value=Settings.get('ollama_url', OLLAMA_BASE_URL)
    )

    # Test connection
    if st.button("Test Connection"):
        try:
            client = OllamaClient(base_url=ollama_url)
            result = client.test_connection()

            if result['success']:
                st.success("✓ Connected successfully!")
                st.info(f"Available models: {', '.join(result.get('models', []))}")
                Settings.set('ollama_url', ollama_url)
            else:
                st.error(f"✗ Connection failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    # Get available models
    try:
        client = OllamaClient(base_url=ollama_url)
        available_models = client.list_models()
    except:
        available_models = [OLLAMA_DEFAULT_MODEL]

    selected_model = st.selectbox(
        "Model",
        available_models,
        index=0 if OLLAMA_DEFAULT_MODEL not in available_models else available_models.index(OLLAMA_DEFAULT_MODEL)
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=Settings.get('temperature', 0.3),
        step=0.1,
        help="Lower values = more consistent, Higher values = more creative"
    )

    if st.button("Save LLM Settings"):
        Settings.set('ollama_model', selected_model)
        Settings.set('temperature', temperature)
        st.success("✓ Settings saved")

st.markdown("---")

# Embedding Settings
st.markdown("### Embedding Settings")

col1, col2 = st.columns(2)

with col1:
    chunk_size = st.number_input(
        "Chunk Size (tokens)",
        min_value=200,
        max_value=1000,
        value=Settings.get('chunk_size', CHUNK_SIZE),
        step=50,
        help="Size of text chunks for embedding"
    )

with col2:
    chunk_overlap = st.number_input(
        "Chunk Overlap (tokens)",
        min_value=0,
        max_value=200,
        value=Settings.get('chunk_overlap', CHUNK_OVERLAP),
        step=10,
        help="Overlap between consecutive chunks"
    )

if st.button("Save Embedding Settings"):
    Settings.set('chunk_size', chunk_size)
    Settings.set('chunk_overlap', chunk_overlap)
    st.success("✓ Settings saved")

st.markdown("---")

# Company Information
st.markdown("### Company Information")

col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input(
        "Company Name",
        value=Settings.get('company_name', '')
    )

    company_address = st.text_area(
        "Company Address",
        value=Settings.get('company_address', ''),
        height=100
    )

with col2:
    authorized_rep = st.text_input(
        "EU Authorized Representative",
        value=Settings.get('authorized_rep', '')
    )

    contact_email = st.text_input(
        "Contact Email",
        value=Settings.get('contact_email', '')
    )

if st.button("Save Company Information"):
    Settings.set('company_name', company_name)
    Settings.set('company_address', company_address)
    Settings.set('authorized_rep', authorized_rep)
    Settings.set('contact_email', contact_email)
    st.success("✓ Company information saved")

st.markdown("---")

# System Information
st.markdown("### System Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <h4 style="color: #00D4AA;">Database</h4>
        <p style="color: #8B949E;">SQLite</p>
        <p style="color: #8B949E; font-size: 0.875rem;">Status: ✓ Active</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <h4 style="color: #3B82F6;">Vector Store</h4>
        <p style="color: #8B949E;">ChromaDB</p>
        <p style="color: #8B949E; font-size: 0.875rem;">Status: ✓ Active</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <h4 style="color: #10B981;">Embeddings</h4>
        <p style="color: #8B949E;">SentenceTransformers</p>
        <p style="color: #8B949E; font-size: 0.875rem;">Model: MiniLM-L6</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# About
st.markdown("### About")

st.markdown("""
<div class="card">
    <h4 style="color: #00D4AA;">EU MDR Clinical Documentation Generator</h4>
    <p style="color: #FAFAFA;"><strong>Version:</strong> 1.0.0</p>
    <p style="color: #8B949E;">
        A professional, fully offline desktop application for generating EU MDR 2017/745 compliant
        clinical documentation including CEP, CER, SSCP, and LSR documents.
    </p>
    <br>
    <p style="color: #8B949E;"><strong>Features:</strong></p>
    <ul style="color: #8B949E;">
        <li>100% offline processing - all data stays on your machine</li>
        <li>Local LLM generation using Ollama</li>
        <li>Support for 500+ documents (PDF, DOCX, XLSX, TXT)</li>
        <li>Intelligent document classification and entity extraction</li>
        <li>Vector-based semantic search with ChromaDB</li>
        <li>Professional DOCX export with proper formatting</li>
    </ul>
    <br>
    <p style="color: #8B949E;"><strong>Technology Stack:</strong></p>
    <p style="color: #8B949E; font-size: 0.875rem;">
        Python • Streamlit • Ollama • ChromaDB • Sentence-Transformers • LangChain • SQLite
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## Settings")

    st.markdown("### Quick Actions")

    if st.button("Reload Settings", use_container_width=True):
        st.rerun()

    st.markdown("---")

    st.markdown("### Navigation")
    if st.button("← Home"):
        st.switch_page("app.py")
