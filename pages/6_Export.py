"""
Page 6: Export
Export generated reports to DOCX
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.database.models import Project, GeneratedReport, ReportSection
from src.templates.docx_builder import DOCXBuilder
from config import OUTPUT_DIR, REPORT_TYPES

st.set_page_config(page_title="Export", layout="wide")

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
    <h1>Export Reports</h1>
    <p style="color: #8B949E; margin-top: 0.5rem;">
        Export and download generated reports for: <strong style="color: #00D4AA;">{project['name']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Get reports
reports = GeneratedReport.get_by_project(st.session_state.current_project)
completed_reports = [r for r in reports if r['status'] == 'completed']

# Stats
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(completed_reports)}</div>
        <div class="metric-label">Ready to Export</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_sections = sum(len(ReportSection.get_by_report(r['id'])) for r in completed_reports)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_sections}</div>
        <div class="metric-label">Total Sections</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">DOCX</div>
        <div class="metric-label">Format</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Export all button
if completed_reports:
    st.markdown("### Quick Export")

    if st.button("Export All Reports to DOCX", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        output_dir = OUTPUT_DIR / st.session_state.current_project
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, report in enumerate(completed_reports):
            status_text.text(f"Exporting {report['report_type']}...")

            try:
                # Get sections
                sections = ReportSection.get_by_report(report['id'])

                # Build DOCX
                builder = DOCXBuilder()
                report_title = REPORT_TYPES.get(report['report_type'], report['report_type'])
                device_name = project.get('device_name', 'Medical Device')

                output_path = output_dir / f"{report['report_type']}_{project['name']}.docx"

                builder.build_from_sections(
                    report_title=report_title,
                    device_name=device_name,
                    sections=sections,
                    output_path=output_path
                )

                # Update report with file path
                GeneratedReport.update(report['id'], file_path=str(output_path))

                st.success(f"✓ Exported {report['report_type']}")

            except Exception as e:
                st.error(f"Error exporting {report['report_type']}: {e}")

            progress_bar.progress((i + 1) / len(completed_reports))

        status_text.empty()
        progress_bar.empty()

        st.success(f"All reports exported to: {output_dir}")

    st.markdown("---")

# Individual reports
if not completed_reports:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon"></div>
        <h3>No Reports Ready</h3>
        <p>Generate reports first before exporting</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Generate Reports"):
        st.switch_page("pages/5_Generate_Reports.py")

else:
    st.markdown("### Individual Reports")

    for report in completed_reports:
        sections = ReportSection.get_by_report(report['id'])

        with st.expander(f"{REPORT_TYPES.get(report['report_type'], report['report_type'])}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Report Type:** {report['report_type']}")
                st.markdown(f"**Sections:** {len(sections)}")
                st.markdown(f"**Status:** {report['status'].title()}")

                if report.get('file_path'):
                    file_path = Path(report['file_path'])
                    if file_path.exists():
                        st.success(f"✓ Exported: {file_path.name}")

            with col2:
                # Export button
                if st.button("Export DOCX", key=f"export_{report['id']}"):
                    try:
                        builder = DOCXBuilder()
                        report_title = REPORT_TYPES.get(report['report_type'], report['report_type'])
                        device_name = project.get('device_name', 'Medical Device')

                        output_dir = OUTPUT_DIR / st.session_state.current_project
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_path = output_dir / f"{report['report_type']}_{project['name']}.docx"

                        builder.build_from_sections(
                            report_title=report_title,
                            device_name=device_name,
                            sections=sections,
                            output_path=output_path
                        )

                        GeneratedReport.update(report['id'], file_path=str(output_path))

                        st.success(f"✓ Exported!")
                        st.caption(f"Saved to: {output_path}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

                # Download button (if file exists)
                if report.get('file_path'):
                    file_path = Path(report['file_path'])
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                label="Download",
                                data=f,
                                file_name=file_path.name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"download_{report['id']}"
                            )

            # Section preview
            st.markdown("**Sections:**")
            for section in sections[:5]:  # Show first 5
                st.caption(f"• {section['section_number']}. {section['section_title']}")

            if len(sections) > 5:
                st.caption(f"... and {len(sections) - 5} more sections")

# Sidebar
with st.sidebar:
    st.markdown("## Export")

    st.markdown(f"**Project:** {project['name']}")
    st.markdown(f"**Reports Ready:** {len(completed_reports)}")

    st.markdown("---")

    st.markdown("### Navigation")
    if st.button("← Generate Reports"):
        st.switch_page("pages/5_Generate_Reports.py")
    if st.button("Settings"):
        st.switch_page("pages/7_Settings.py")
    if st.button("← Home"):
        st.switch_page("app.py")
