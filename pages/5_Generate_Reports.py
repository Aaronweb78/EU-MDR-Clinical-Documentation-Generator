"""
Page 5: Generate Reports
Select and generate CEP, CER, SSCP, LSR reports
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Project, GeneratedReport, ReportSection, Entity
from src.database.operations import get_entities_dict
from src.generation.llm_client import OllamaClient
from src.generation.section_generator import SectionGenerator
from src.generation.cep_generator import CEPGenerator
from src.generation.cer_generator import CERGenerator
from src.generation.sscp_generator import SSCPGenerator
from src.generation.lsr_generator import LSRGenerator
from src.knowledge_base.vector_store import VectorStore
from src.knowledge_base.retriever import Retriever
from src.ingestion.embedder import TextEmbedder

st.set_page_config(page_title="Generate Reports", layout="wide")

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
    <h1>Generate Reports</h1>
    <p style="color: #8B949E; margin-top: 0.5rem;">
        Generate EU MDR clinical documentation for: <strong style="color: #00D4AA;">{project['name']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Get existing reports
existing_reports = GeneratedReport.get_by_project(st.session_state.current_project)

# Stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(existing_reports)}</div>
        <div class="metric-label">Reports</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    completed = sum(1 for r in existing_reports if r['status'] == 'completed')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #10B981;">{completed}</div>
        <div class="metric-label">Completed</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    in_progress = sum(1 for r in existing_reports if r['status'] == 'in_progress')
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #F59E0B;">{in_progress}</div>
        <div class="metric-label">In Progress</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">4</div>
        <div class="metric-label">Report Types</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Select reports to generate
st.markdown("### Select Reports to Generate")

col1, col2 = st.columns(2)

with col1:
    generate_cep = st.checkbox("Clinical Evaluation Plan (CEP)", value=True)
    generate_cer = st.checkbox("Clinical Evaluation Report (CER)", value=True)

with col2:
    generate_sscp = st.checkbox("Summary of Safety and Clinical Performance (SSCP)", value=True)
    generate_lsr = st.checkbox("Literature Search Report (LSR)", value=True)

selected_reports = []
if generate_cep:
    selected_reports.append('CEP')
if generate_cer:
    selected_reports.append('CER')
if generate_sscp:
    selected_reports.append('SSCP')
if generate_lsr:
    selected_reports.append('LSR')

if selected_reports:
    st.info(f"**{len(selected_reports)} report(s) selected:** {', '.join(selected_reports)}")
else:
    st.warning("Please select at least one report to generate")

st.markdown("---")

# Generation button
st.markdown("### Start Generation")

if st.button("Generate Selected Reports", type="primary", disabled=len(selected_reports) == 0):
    st.session_state.generating = True
    st.session_state.selected_reports = selected_reports
    st.rerun()

# Generation process
if st.session_state.get('generating', False):
    st.markdown("---")
    st.markdown("### Generation Progress")

    # Initialize components
    with st.spinner("Initializing generation components..."):
        try:
            llm_client = OllamaClient()
            vector_store = VectorStore()
            embedder = TextEmbedder()
            retriever = Retriever(vector_store, embedder)
            section_generator = SectionGenerator(llm_client, retriever)

            # Initialize report generators
            generators = {
                'CEP': CEPGenerator(section_generator),
                'CER': CERGenerator(section_generator),
                'SSCP': SSCPGenerator(section_generator),
                'LSR': LSRGenerator(section_generator)
            }

            # Get device info from entities
            entities = get_entities_dict(st.session_state.current_project)
            device_info = {
                'device_name': project.get('device_name', 'Unknown Device'),
                'device_class': project.get('device_class', ''),
                'manufacturer': entities.get('manufacturer', [{'value': ''}])[0].get('value', ''),
                'intended_purpose': entities.get('intended_purpose', [{'value': ''}])[0].get('value', ''),
            }

        except Exception as e:
            st.error(f"Error initializing components: {e}")
            st.session_state.generating = False
            st.stop()

    # Generate each selected report
    selected_reports = st.session_state.selected_reports

    for report_type in selected_reports:
        st.markdown(f"#### Generating {report_type}")

        # Create report record
        report_id = GeneratedReport.create(
            project_id=st.session_state.current_project,
            report_type=report_type
        )

        GeneratedReport.update(report_id, status='in_progress')

        generator = generators[report_type]
        sections_config = generator.get_sections()

        progress_bar = st.progress(0)
        status_text = st.empty()

        generated_sections = []

        for i, section_config in enumerate(sections_config):
            status_text.text(f"Generating section {i+1}/{len(sections_config)}: {section_config['title']}...")

            try:
                result = generator.generate_section(
                    project_id=st.session_state.current_project,
                    section_config=section_config,
                    device_info=device_info
                )

                if result['success']:
                    # Save section to database
                    ReportSection.create(
                        report_id=report_id,
                        section_number=result['section_number'],
                        section_title=result['section_title'],
                        content=result['content'],
                        sources=result.get('sources', [])
                    )

                    generated_sections.append(result)
                    st.success(f"✓ {section_config['title']}")
                else:
                    st.error(f"✗ Failed: {section_config['title']}")

            except Exception as e:
                st.error(f"Error generating {section_config['title']}: {e}")

            progress_bar.progress((i + 1) / len(sections_config))

        status_text.empty()
        progress_bar.empty()

        # Update report status
        GeneratedReport.update(report_id, status='completed')

        st.success(f"{report_type} generation complete!")
        st.markdown("---")

    # All done
    st.markdown("### All Reports Generated!")

    if st.button("→ View & Export Reports", type="primary"):
        st.session_state.generating = False
        st.switch_page("pages/6_Export.py")

    if st.button("Finish"):
        st.session_state.generating = False
        st.rerun()

# Show existing reports
if existing_reports and not st.session_state.get('generating', False):
    st.markdown("---")
    st.markdown("### Generated Reports")

    for report in existing_reports:
        with st.expander(f"{report['report_type']} - {report['status'].title()}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                sections = ReportSection.get_by_report(report['id'])
                st.markdown(f"**Sections:** {len(sections)}")
                st.caption(f"Generated: {report.get('generated_at', 'N/A')}")

            with col2:
                if st.button("View/Export", key=f"view_{report['id']}"):
                    st.switch_page("pages/6_Export.py")

# Sidebar
with st.sidebar:
    st.markdown("## Generate Reports")

    st.markdown(f"**Project:** {project['name']}")

    st.markdown("---")

    st.markdown("### Navigation")
    if st.button("← Review Classification"):
        st.switch_page("pages/4_Review_Classification.py")
    if st.button("→ Export"):
        st.switch_page("pages/6_Export.py")
    if st.button("← Home"):
        st.switch_page("app.py")
