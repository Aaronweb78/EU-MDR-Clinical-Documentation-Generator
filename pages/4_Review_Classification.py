"""
Page 4: Review Classification
Review and adjust document classifications
"""
import streamlit as st
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Project, File
from config import DOCUMENT_CATEGORIES

st.set_page_config(page_title="Review Classification", layout="wide")

# Load CSS
css_file = Path(__file__).parent.parent / "assets" / "style.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Check project
if not st.session_state.get('current_project'):
    st.warning("No project selected")
    if st.button("← Go to Projects"):
        st.switch_page("pages/1_Projects.py")
    st.stop()

project = Project.get_by_id(st.session_state.current_project)

# Header
st.markdown(f"""
<div class="main-header">
    <h1>Review Classification</h1>
    <p style="color: #8B949E; margin-top: 0.5rem;">
        Review and adjust document categories for: <strong style="color: #00D4AA;">{project['name']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Get files
files = File.get_by_project(st.session_state.current_project)
classified_files = [f for f in files if f['classification']]

# Stats
categories_count = {}
for f in classified_files:
    cat = f['classification']
    categories_count[cat] = categories_count.get(cat, 0) + 1

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(classified_files)}</div>
        <div class="metric-label">Classified</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(categories_count)}</div>
        <div class="metric-label">Categories</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    avg_confidence = sum(f['classification_confidence'] or 0 for f in classified_files) / len(classified_files) if classified_files else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{avg_confidence:.2f}</div>
        <div class="metric-label">Avg Confidence</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    key_docs = sum(1 for f in classified_files if f.get('is_key_document'))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{key_docs}</div>
        <div class="metric-label">Key Documents</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Category distribution
st.markdown("### Category Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    if categories_count:
        chart_data = pd.DataFrame({
            'Category': list(categories_count.keys()),
            'Count': list(categories_count.values())
        })
        st.bar_chart(chart_data.set_index('Category'))
    else:
        st.info("No classified files yet")

with col2:
    st.markdown("#### Categories")
    for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"**{cat}**: {count} files")

st.markdown("---")

# Filter options
st.markdown("### Filter & Review")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    category_filter = st.selectbox(
        "Filter by Category",
        ["All"] + list(DOCUMENT_CATEGORIES.keys())
    )

with filter_col2:
    confidence_filter = st.slider(
        "Min Confidence",
        0.0, 1.0, 0.0, 0.1
    )

with filter_col3:
    key_doc_filter = st.checkbox("Show only key documents")

# Apply filters
filtered_files = classified_files

if category_filter != "All":
    filtered_files = [f for f in filtered_files if f['classification'] == category_filter]

if confidence_filter > 0:
    filtered_files = [f for f in filtered_files if (f['classification_confidence'] or 0) >= confidence_filter]

if key_doc_filter:
    filtered_files = [f for f in filtered_files if f.get('is_key_document')]

st.markdown(f"**Showing {len(filtered_files)} files**")

# File list with edit capability
if not filtered_files:
    st.info("No files match the selected filters")
else:
    for file in filtered_files:
        with st.expander(f"{file['filename']}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"**Current Category:** {file['classification']}")
                st.caption(f"Confidence: {file['classification_confidence']:.2f}")

                # Change category
                new_category = st.selectbox(
                    "Change to:",
                    list(DOCUMENT_CATEGORIES.keys()),
                    index=list(DOCUMENT_CATEGORIES.keys()).index(file['classification']),
                    key=f"cat_{file['id']}"
                )

                if new_category != file['classification']:
                    if st.button("Update Category", key=f"update_{file['id']}"):
                        File.update(
                            file['id'],
                            classification=new_category,
                            classification_confidence=1.0
                        )
                        st.success("✓ Updated")
                        st.rerun()

            with col2:
                st.markdown("**Category Description:**")
                st.caption(DOCUMENT_CATEGORIES[file['classification']]['description'])

                # Mark as key document
                is_key = st.checkbox(
                    "Mark as Key Document",
                    value=file.get('is_key_document', False),
                    key=f"key_{file['id']}"
                )

                if is_key != file.get('is_key_document', False):
                    File.update(file['id'], is_key_document=is_key)
                    st.rerun()

            with col3:
                st.markdown("**File Info:**")
                st.caption(f"Type: {file['file_type'].upper()}")
                st.caption(f"Chunks: {file.get('chunk_count', 0)}")

                # Preview button
                if st.button("Preview", key=f"preview_{file['id']}"):
                    st.session_state[f"show_preview_{file['id']}"] = not st.session_state.get(f"show_preview_{file['id']}", False)

            # Show preview if requested
            if st.session_state.get(f"show_preview_{file['id']}", False):
                text_path = file.get('extracted_text_path')
                if text_path and Path(text_path).exists():
                    with open(text_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                        preview = text[:500] + "..." if len(text) > 500 else text
                        st.text_area("Preview:", preview, height=150, key=f"preview_text_{file['id']}")

# Bulk actions
st.markdown("---")
st.markdown("### Bulk Actions")

bulk_col1, bulk_col2, bulk_col3 = st.columns(3)

with bulk_col1:
    if st.button("Mark All Filtered as Key Documents"):
        for file in filtered_files:
            File.update(file['id'], is_key_document=True)
        st.success("✓ Updated all filtered files")
        st.rerun()

with bulk_col2:
    st.info(f"{len(filtered_files)} files selected")

# Sidebar
with st.sidebar:
    st.markdown("## Review")

    st.markdown(f"**Project:** {project['name']}")
    st.markdown(f"**Classified:** {len(classified_files)}")

    st.markdown("---")

    st.markdown("### Next Steps")

    if len(classified_files) > 0:
        if st.button("→ Generate Reports", use_container_width=True):
            st.switch_page("pages/5_Generate_Reports.py")

    st.markdown("---")

    st.markdown("### Navigation")
    if st.button("← Process Files"):
        st.switch_page("pages/3_Process_Files.py")
    if st.button("← Home"):
        st.switch_page("app.py")
