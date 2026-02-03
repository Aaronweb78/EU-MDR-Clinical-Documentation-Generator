"""
Page 1: Project Management
Create, view, select, and delete projects
"""
import streamlit as st
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Project
from src.database.operations import create_project_workspace, delete_project_workspace, get_project_stats

st.set_page_config(page_title="Projects", layout="wide")

# Load CSS
css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.title("Project Management")
st.caption("Create and manage your medical device documentation projects")

# Create new project section
st.markdown("### Create New Project")

with st.form("new_project_form"):
    col1, col2 = st.columns(2)

    with col1:
        project_name = st.text_input("Project Name *", placeholder="e.g., Cardiac Stent v2.0 Clinical Evaluation")
        device_name = st.text_input("Device Name", placeholder="e.g., CardioFlow Stent")

    with col2:
        device_class = st.selectbox("Device Class", ["", "I", "IIa", "IIb", "III"])
        description = st.text_area("Description", placeholder="Brief description of the project...")

    submit_col1, submit_col2, submit_col3 = st.columns([1, 1, 2])
    with submit_col1:
        submitted = st.form_submit_button("Create Project", use_container_width=True)

    if submitted:
        if not project_name:
            st.error("Project name is required")
        else:
            try:
                # Create project in database
                project_id = Project.create(
                    name=project_name,
                    device_name=device_name if device_name else None,
                    device_class=device_class if device_class else None,
                    description=description if description else None
                )

                # Create project workspace
                create_project_workspace(project_id)

                st.success(f"✓ Project created successfully!")
                st.session_state.current_project = project_id
                st.rerun()
            except Exception as e:
                st.error(f"Error creating project: {e}")

st.markdown("---")

# Existing projects
st.markdown("### Your Projects")

try:
    projects = Project.get_all()

    if not projects:
        st.info("No Projects Yet - Create your first project above to get started")
    else:
        # Display projects in grid
        cols_per_row = 3
        for i in range(0, len(projects), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(projects):
                    project = projects[idx]

                    with col:
                        # Get project stats
                        try:
                            stats = get_project_stats(project['id'])
                        except:
                            stats = {'total_files': 0, 'processed_files': 0, 'total_reports': 0}

                        # Status badge
                        status = project.get('status', 'draft')

                        # Project card using native Streamlit
                        with st.container(border=True):
                            st.subheader(project['name'])
                            st.caption(f"Status: {status.upper()}")

                            if project.get('device_name'):
                                st.markdown(f"**Device:** {project['device_name']}")
                            if project.get('device_class'):
                                st.caption(f"Class {project['device_class']}")

                            # Stats row
                            stat_cols = st.columns(3)
                            with stat_cols[0]:
                                st.metric("Files", stats.get('total_files', 0))
                            with stat_cols[1]:
                                st.metric("Processed", stats.get('processed_files', 0))
                            with stat_cols[2]:
                                st.metric("Reports", stats.get('total_reports', 0))

                            st.caption(f"Updated: {datetime.fromisoformat(project['updated_at']).strftime('%Y-%m-%d %H:%M')}")

                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)

                        with btn_col1:
                            if st.button("Select", key=f"select_{project['id']}", use_container_width=True):
                                st.session_state.current_project = project['id']
                                st.success(f"✓ Selected: {project['name']}")
                                st.rerun()

                        with btn_col2:
                            if st.button("Delete", key=f"delete_{project['id']}", use_container_width=True):
                                st.session_state[f"confirm_delete_{project['id']}"] = True

                        # Confirm delete
                        if st.session_state.get(f"confirm_delete_{project['id']}", False):
                            st.warning("Are you sure? This cannot be undone!")
                            confirm_col1, confirm_col2 = st.columns(2)

                            with confirm_col1:
                                if st.button("Yes, Delete", key=f"confirm_yes_{project['id']}", use_container_width=True):
                                    try:
                                        # Delete from database
                                        Project.delete(project['id'])
                                        # Delete workspace
                                        delete_project_workspace(project['id'])
                                        # Clear selection if this was selected
                                        if st.session_state.current_project == project['id']:
                                            st.session_state.current_project = None
                                        st.success("✓ Project deleted")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting project: {e}")

                            with confirm_col2:
                                if st.button("Cancel", key=f"confirm_no_{project['id']}", use_container_width=True):
                                    st.session_state[f"confirm_delete_{project['id']}"] = False
                                    st.rerun()

except Exception as e:
    st.error(f"Error loading projects: {e}")

# Sidebar
with st.sidebar:
    st.markdown("## Projects")

    if st.session_state.get('current_project'):
        try:
            current = Project.get_by_id(st.session_state.current_project)
            if current:
                st.success("✓ Project Selected")
                st.info(f"**{current['name']}**")

                if st.button("Continue to Upload Files →"):
                    st.switch_page("pages/2_Upload_Files.py")
        except:
            pass
    else:
        st.info("No project selected")

    st.markdown("---")
    st.markdown("### Navigation")
    if st.button("← Home"):
        st.switch_page("app.py")
