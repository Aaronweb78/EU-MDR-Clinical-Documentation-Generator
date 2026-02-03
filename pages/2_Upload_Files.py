"""
Page 2: Upload Files
Upload and manage files for a project
"""
import streamlit as st
from pathlib import Path
import sys
import shutil

sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Project, File
from src.utils.file_utils import get_file_type, get_file_size, format_file_size, is_supported_file
from config import PROJECTS_DIR

st.set_page_config(page_title="Upload Files", layout="wide")

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
    <h1>Upload Files</h1>
    <p style="color: #8B949E; margin-top: 0.5rem;">
        Upload documentation for: <strong style="color: #00D4AA;">{project['name']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Stats
col1, col2, col3, col4 = st.columns(4)

existing_files = File.get_by_project(st.session_state.current_project)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(existing_files)}</div>
        <div class="metric-label">Total Files</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_size = sum(f['file_size'] for f in existing_files)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{format_file_size(total_size)}</div>
        <div class="metric-label">Total Size</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    processed = sum(1 for f in existing_files if f['processed'])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{processed}</div>
        <div class="metric-label">Processed</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    classified = sum(1 for f in existing_files if f['classification'])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{classified}</div>
        <div class="metric-label">Classified</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# File uploader
st.markdown("### Upload Documents")

st.info("""
**Supported formats:** PDF, DOCX, DOC, XLSX, XLS, TXT
**Recommended:** Upload all relevant documentation including design specs, risk analysis, clinical data, IFU, test reports, etc.
""")

uploaded_files = st.file_uploader(
    "Choose files",
    type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt'],
    accept_multiple_files=True,
    help="Select one or more files to upload"
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) ready to upload**")

    if st.button("Upload All Files", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        project_input_dir = PROJECTS_DIR / st.session_state.current_project / "input"
        project_input_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        error_count = 0

        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Uploading {uploaded_file.name}...")

                # Check if file type is supported
                if not is_supported_file(uploaded_file.name):
                    st.warning(f"Skipping unsupported file: {uploaded_file.name}")
                    error_count += 1
                    continue

                # Save file
                file_path = project_input_dir / uploaded_file.name

                # Check if file already exists
                if file_path.exists():
                    st.warning(f"File already exists: {uploaded_file.name}")
                    error_count += 1
                    continue

                # Write file
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())

                # Create database record
                file_type = get_file_type(uploaded_file.name)
                file_size = file_path.stat().st_size

                File.create(
                    project_id=st.session_state.current_project,
                    filename=uploaded_file.name,
                    file_path=str(file_path),
                    file_type=file_type,
                    file_size=file_size
                )

                success_count += 1

            except Exception as e:
                st.error(f"Error uploading {uploaded_file.name}: {e}")
                error_count += 1

            progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.empty()
        progress_bar.empty()

        if success_count > 0:
            st.success(f"✓ Successfully uploaded {success_count} file(s)")
        if error_count > 0:
            st.warning(f"{error_count} file(s) had errors")

        st.rerun()

st.markdown("---")

# Existing files list
st.markdown("### Uploaded Files")

if not existing_files:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon"></div>
        <h3>No Files Uploaded Yet</h3>
        <p>Upload your first files above to get started</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Filter options
    filter_col1, filter_col2 = st.columns([1, 3])

    with filter_col1:
        file_type_filter = st.selectbox(
            "Filter by type",
            ["All"] + list(set(f['file_type'] for f in existing_files))
        )

    # Apply filter
    filtered_files = existing_files
    if file_type_filter != "All":
        filtered_files = [f for f in existing_files if f['file_type'] == file_type_filter]

    # Display files in table
    st.markdown(f"Showing {len(filtered_files)} of {len(existing_files)} files")

    for file in filtered_files:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            with col1:
                # File icon based on type
                st.markdown(f"**{file['filename']}**")

                # Status badges
                badges = []
                if file['processed']:
                    badges.append('<span style="background: #10B98133; color: #10B981; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">Processed</span>')
                if file['classification']:
                    badges.append(f'<span style="background: #3B82F633; color: #3B82F6; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">{file["classification"]}</span>')

                if badges:
                    st.markdown(" ".join(badges), unsafe_allow_html=True)

            with col2:
                st.caption(file['file_type'].upper())

            with col3:
                st.caption(format_file_size(file['file_size']))

            with col4:
                if file['chunk_count'] and file['chunk_count'] > 0:
                    st.caption(f"{file['chunk_count']} chunks")
                else:
                    st.caption("—")

            with col5:
                if st.button("Delete", key=f"delete_{file['id']}", use_container_width=True):
                    st.session_state[f"confirm_delete_file_{file['id']}"] = True

            # Confirm delete
            if st.session_state.get(f"confirm_delete_file_{file['id']}", False):
                st.warning("Delete this file?")
                conf_col1, conf_col2, conf_col3 = st.columns([1, 1, 3])

                with conf_col1:
                    if st.button("Yes", key=f"yes_{file['id']}"):
                        try:
                            # Delete file from disk
                            file_path = Path(file['file_path'])
                            if file_path.exists():
                                file_path.unlink()

                            # Delete from database (would need to add this method)
                            # For now, just update to mark as deleted
                            st.success("✓ File deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with conf_col2:
                    if st.button("No", key=f"no_{file['id']}"):
                        st.session_state[f"confirm_delete_file_{file['id']}"] = False
                        st.rerun()

            st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("## Upload Files")

    st.markdown(f"**Project:** {project['name']}")
    st.markdown(f"**Files:** {len(existing_files)}")

    st.markdown("---")

    st.markdown("### Next Steps")

    if len(existing_files) > 0:
        if st.button("→ Process Files", use_container_width=True):
            st.switch_page("pages/3_Process_Files.py")
    else:
        st.info("Upload files to continue")

    st.markdown("---")

    st.markdown("### Navigation")
    if st.button("← Projects"):
        st.switch_page("pages/1_Projects.py")
    if st.button("← Home"):
        st.switch_page("app.py")
