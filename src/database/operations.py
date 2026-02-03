"""
Database operations and helper functions
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import shutil
from .models import Project, File, Entity, GeneratedReport, ReportSection, Settings
from config import PROJECTS_DIR


def create_project_workspace(project_id: str):
    """Create directory structure for a project"""
    project_dir = PROJECTS_DIR / project_id
    (project_dir / "input").mkdir(parents=True, exist_ok=True)
    (project_dir / "processed").mkdir(parents=True, exist_ok=True)
    (project_dir / "output").mkdir(parents=True, exist_ok=True)


def delete_project_workspace(project_id: str):
    """Delete project directory structure"""
    project_dir = PROJECTS_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)


def get_project_stats(project_id: str) -> Dict[str, Any]:
    """Get project statistics"""
    files = File.get_by_project(project_id)
    entities = Entity.get_by_project(project_id)
    reports = GeneratedReport.get_by_project(project_id)

    processed_files = sum(1 for f in files if f['processed'])
    classified_files = sum(1 for f in files if f['classification'])

    return {
        "total_files": len(files),
        "processed_files": processed_files,
        "classified_files": classified_files,
        "total_entities": len(entities),
        "total_reports": len(reports),
        "completion_rate": (processed_files / len(files) * 100) if files else 0
    }


def get_files_by_status(project_id: str) -> Dict[str, List[Dict]]:
    """Get files grouped by processing status"""
    files = File.get_by_project(project_id)

    return {
        "pending": [f for f in files if not f['processed']],
        "processed": [f for f in files if f['processed'] and not f['processing_error']],
        "failed": [f for f in files if f['processing_error']]
    }


def get_classification_summary(project_id: str) -> Dict[str, int]:
    """Get count of files by classification"""
    files = File.get_by_project(project_id)
    summary = {}

    for file in files:
        if file['classification']:
            summary[file['classification']] = summary.get(file['classification'], 0) + 1

    return summary


def get_entities_dict(project_id: str) -> Dict[str, Any]:
    """Get entities as a dictionary by type"""
    entities = Entity.get_by_project(project_id)
    entities_dict = {}

    for entity in entities:
        entity_type = entity['entity_type']
        if entity_type not in entities_dict:
            entities_dict[entity_type] = []
        entities_dict[entity_type].append({
            'value': entity['entity_value'],
            'confidence': entity['confidence'],
            'source_file_id': entity['source_file_id']
        })

    return entities_dict


def get_report_with_sections(report_id: str) -> Optional[Dict[str, Any]]:
    """Get report with all its sections"""
    report = GeneratedReport.get_by_id(report_id)
    if not report:
        return None

    sections = ReportSection.get_by_report(report_id)
    report['sections'] = sections

    return report


def get_project_reports_summary(project_id: str) -> Dict[str, Any]:
    """Get summary of all reports for a project"""
    reports = GeneratedReport.get_by_project(project_id)

    summary = {}
    for report in reports:
        sections = ReportSection.get_by_report(report['id'])
        summary[report['report_type']] = {
            'id': report['id'],
            'status': report['status'],
            'generated_at': report['generated_at'],
            'file_path': report['file_path'],
            'section_count': len(sections),
            'completed_sections': sum(1 for s in sections if s['content'])
        }

    return summary


def bulk_update_classifications(updates: List[Dict[str, Any]]):
    """Bulk update file classifications"""
    for update in updates:
        File.update(
            update['file_id'],
            classification=update['classification'],
            classification_confidence=update.get('confidence', 1.0)
        )


def get_source_context(project_id: str, categories: List[str],
                       limit: int = 10) -> List[Dict[str, Any]]:
    """Get source context for report generation"""
    all_files = []

    for category in categories:
        files = File.get_by_classification(project_id, category)
        all_files.extend(files)

    # Sort by key documents first, then by confidence
    all_files.sort(
        key=lambda x: (not x.get('is_key_document', False),
                      -x.get('classification_confidence', 0))
    )

    return all_files[:limit]
