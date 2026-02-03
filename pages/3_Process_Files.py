"""
Page 3: Process Files
Process uploaded files: extract text, classify, chunk, and embed
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Project, File, Entity
from src.ingestion.file_processor import FileProcessor
from src.ingestion.chunker import TextChunker
from src.ingestion.embedder import TextEmbedder
from src.classification.classifier import DocumentClassifier
from src.extraction.entity_extractor import EntityExtractor
from src.knowledge_base.vector_store import VectorStore
from src.generation.llm_client import OllamaClient
from config import PROJECTS_DIR
import logging

st.set_page_config(page_title="Process Files", layout="wide")

# Load CSS
css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Check if project is selected
if not st.session_state.get('current_project'):
    st.warning("No project selected. Please select a project first.")
    if st.button("← Go to Projects"):
        st.switch_page("pages/1_Projects.py")
    st.stop()

# Get current project
try:
    project = Project.get_by_id(st.session_state.current_project)
    if not project:
        st.error("Project not found")
        st.stop()
except Exception as e:
    st.error(f"Error loading project: {e}")
    st.stop()

# Header
st.markdown(f"""
<div class="main-header">
    <h1>Process Files</h1>
    <p style="color: #8B949E; margin-top: 0.5rem;">
        Extract, classify, and index documents for: <strong style="color: #00D4AA;">{project['name']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Get files
files = File.get_by_project(st.session_state.current_project)
unprocessed_files = [f for f in files if not f['processed']]
processed_files = [f for f in files if f['processed']]

# Stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(files)}</div>
        <div class="metric-label">Total Files</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #F59E0B;">{len(unprocessed_files)}</div>
        <div class="metric-label">Pending</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #10B981;">{len(processed_files)}</div>
        <div class="metric-label">Processed</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    progress_pct = (len(processed_files) / len(files) * 100) if files else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{progress_pct:.0f}%</div>
        <div class="metric-label">Complete</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Processing options
st.markdown("### Processing Options")

col1, col2, col3 = st.columns(3)

with col1:
    use_llm_classification = st.checkbox(
        "Use LLM for Classification",
        value=False,
        help="Use Ollama LLM for more accurate classification (slower)"
    )

with col2:
    use_llm_extraction = st.checkbox(
        "Use LLM for Entity Extraction",
        value=False,
        help="Use Ollama LLM for entity extraction (slower)"
    )

with col3:
    batch_size = st.number_input(
        "Batch Size",
        min_value=1,
        max_value=50,
        value=10,
        help="Number of files to process at once"
    )

# Start processing
st.markdown("### Start Processing")

if len(unprocessed_files) == 0:
    st.success("✓ All files have been processed!")
    if st.button("→ Review Classification"):
        st.switch_page("pages/4_Review_Classification.py")
else:
    st.info(f"**{len(unprocessed_files)} file(s)** ready to process")

    if st.button("Start Processing", type="primary", use_container_width=False):
        st.session_state.processing = True
        st.rerun()

# Processing pipeline
if st.session_state.get('processing', False):
    st.markdown("---")
    st.markdown("### Processing Progress")

    # Initialize components
    with st.spinner("Initializing processing components..."):
        try:
            file_processor = FileProcessor()
            classifier = DocumentClassifier()
            entity_extractor = EntityExtractor()
            chunker = TextChunker()
            embedder = TextEmbedder()
            vector_store = VectorStore()

            # Initialize LLM if needed
            llm_client = None
            if use_llm_classification or use_llm_extraction:
                llm_client = OllamaClient()
                classifier.llm_client = llm_client
                entity_extractor.llm_client = llm_client

        except Exception as e:
            st.error(f"Error initializing components: {e}")
            st.session_state.processing = False
            st.stop()

    # Process files
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()

    total_files = len(unprocessed_files)
    success_count = 0
    error_count = 0

    for i, file_record in enumerate(unprocessed_files):
        file_path = Path(file_record['file_path'])
        filename = file_record['filename']

        with log_container:
            st.markdown(f"**Processing ({i+1}/{total_files}):** {filename}")

            try:
                # Step 1: Extract text
                status_text.text(f"[{i+1}/{total_files}] Extracting text from {filename}...")
                text = file_processor.process_file(file_path)

                if not text:
                    st.warning(f"No text extracted from {filename}")
                    File.update(file_record['id'], processing_error="No text extracted")
                    error_count += 1
                    continue

                # Save extracted text
                processed_dir = PROJECTS_DIR / st.session_state.current_project / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                text_file_path = processed_dir / f"{file_record['id']}.txt"

                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                # Step 2: Classify document
                status_text.text(f"[{i+1}/{total_files}] Classifying {filename}...")
                classification_result = classifier.classify(
                    text=text,
                    filename=filename,
                    use_llm=use_llm_classification
                )

                # Step 3: Extract entities
                status_text.text(f"[{i+1}/{total_files}] Extracting entities from {filename}...")
                entities = entity_extractor.extract(
                    text=text,
                    filename=filename,
                    use_llm=use_llm_extraction
                )

                # Save entities to database
                for entity_type, entity_value in entities.items():
                    if entity_value:
                        Entity.create(
                            project_id=st.session_state.current_project,
                            entity_type=entity_type,
                            entity_value=str(entity_value),
                            source_file_id=file_record['id'],
                            confidence=0.8
                        )

                # Step 4: Chunk text
                status_text.text(f"[{i+1}/{total_files}] Chunking {filename}...")
                chunks = chunker.chunk_with_context(
                    text=text,
                    file_id=file_record['id'],
                    filename=filename,
                    category=classification_result['category']
                )

                # Step 5: Generate embeddings
                status_text.text(f"[{i+1}/{total_files}] Generating embeddings for {filename}...")
                chunks_with_embeddings = embedder.embed_chunks(chunks, show_progress=False)

                # Add unique IDs to chunks
                for j, chunk in enumerate(chunks_with_embeddings):
                    chunk['id'] = f"{file_record['id']}_{j}"

                # Step 6: Store in vector database
                status_text.text(f"[{i+1}/{total_files}] Storing chunks in vector database...")
                vector_store.add_chunks(
                    project_id=st.session_state.current_project,
                    chunks=chunks_with_embeddings
                )

                # Update file record
                File.update(
                    file_record['id'],
                    processed=True,
                    extracted_text_path=str(text_file_path),
                    classification=classification_result['category'],
                    classification_confidence=classification_result['confidence'],
                    chunk_count=len(chunks)
                )

                st.success(f"✓ Processed {filename} - {classification_result['category']} ({len(chunks)} chunks)")
                success_count += 1

            except Exception as e:
                st.error(f"Error processing {filename}: {e}")
                File.update(file_record['id'], processing_error=str(e))
                error_count += 1

        progress_bar.progress((i + 1) / total_files)

    # Completion
    status_text.empty()
    progress_bar.empty()

    st.markdown("---")
    st.markdown("### Processing Complete")

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        st.markdown(f"""
        <div class="card">
            <h4 style="color: #10B981; margin-top: 0;">✓ Success: {success_count}</h4>
            <p style="color: #8B949E;">Files processed successfully</p>
        </div>
        """, unsafe_allow_html=True)

    with result_col2:
        st.markdown(f"""
        <div class="card">
            <h4 style="color: #EF4444; margin-top: 0;">✗ Errors: {error_count}</h4>
            <p style="color: #8B949E;">Files with processing errors</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("→ Review Classification", type="primary"):
        st.session_state.processing = False
        st.switch_page("pages/4_Review_Classification.py")

    if st.button("Finish"):
        st.session_state.processing = False
        st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("## Process Files")

    st.markdown(f"**Project:** {project['name']}")
    st.markdown(f"**Total Files:** {len(files)}")
    st.markdown(f"**Processed:** {len(processed_files)}")
    st.markdown(f"**Pending:** {len(unprocessed_files)}")

    if len(processed_files) > 0:
        progress_pct = len(processed_files) / len(files) * 100
        st.progress(progress_pct / 100)
        st.caption(f"{progress_pct:.1f}% complete")

    st.markdown("---")

    st.markdown("### Next Steps")

    if len(unprocessed_files) == 0:
        if st.button("→ Review Classification", use_container_width=True):
            st.switch_page("pages/4_Review_Classification.py")

    st.markdown("---")

    st.markdown("### Navigation")
    if st.button("← Upload Files"):
        st.switch_page("pages/2_Upload_Files.py")
    if st.button("← Home"):
        st.switch_page("app.py")
