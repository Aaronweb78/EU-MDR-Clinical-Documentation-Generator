"""
Database models for EU MDR Clinical Documentation Generator
Using SQLite with direct SQL queries
"""
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
from config import DATABASE_PATH


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with all tables"""
    conn = get_connection()
    cursor = conn.cursor()

    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            device_name TEXT,
            device_class TEXT,
            description TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            status TEXT DEFAULT 'draft'
        )
    """)

    # Files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER,
            classification TEXT,
            classification_confidence REAL,
            is_key_document BOOLEAN DEFAULT 0,
            extracted_text_path TEXT,
            chunk_count INTEGER DEFAULT 0,
            processed BOOLEAN DEFAULT 0,
            processing_error TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Entities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_value TEXT NOT NULL,
            source_file_id TEXT,
            confidence REAL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (source_file_id) REFERENCES files(id) ON DELETE SET NULL
        )
    """)

    # Generated reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_reports (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            generated_at DATETIME,
            file_path TEXT,
            sections TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # Report sections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_sections (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            section_number INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            content TEXT,
            sources TEXT,
            generated_at DATETIME,
            edited BOOLEAN DEFAULT 0,
            edited_at DATETIME,
            FOREIGN KEY (report_id) REFERENCES generated_reports(id) ON DELETE CASCADE
        )
    """)

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


class Project:
    """Project model"""

    @staticmethod
    def create(name: str, device_name: str = None, device_class: str = None,
               description: str = None) -> str:
        """Create a new project"""
        project_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (id, name, device_name, device_class, description,
                                created_at, updated_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
        """, (project_id, name, device_name, device_class, description, now, now))
        conn.commit()
        conn.close()

        return project_id

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all projects"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(f.id) as file_count
            FROM projects p
            LEFT JOIN files f ON p.id = f.project_id
            GROUP BY p.id
            ORDER BY p.updated_at DESC
        """)
        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return projects

    @staticmethod
    def get_by_id(project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(project_id: str, **kwargs):
        """Update project fields"""
        kwargs['updated_at'] = datetime.now().isoformat()
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [project_id]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE projects SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(project_id: str):
        """Delete project and all associated data"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()


class File:
    """File model"""

    @staticmethod
    def create(project_id: str, filename: str, file_path: str,
               file_type: str, file_size: int) -> str:
        """Create a new file record"""
        file_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO files (id, project_id, filename, file_path, file_type,
                             file_size, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_id, project_id, filename, file_path, file_type, file_size, now, now))
        conn.commit()
        conn.close()

        return file_id

    @staticmethod
    def get_by_project(project_id: str) -> List[Dict[str, Any]]:
        """Get all files for a project"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM files
            WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,))
        files = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return files

    @staticmethod
    def get_by_id(file_id: str) -> Optional[Dict[str, Any]]:
        """Get file by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(file_id: str, **kwargs):
        """Update file fields"""
        kwargs['updated_at'] = datetime.now().isoformat()
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [file_id]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE files SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_classification(project_id: str, classification: str) -> List[Dict[str, Any]]:
        """Get files by classification"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM files
            WHERE project_id = ? AND classification = ?
            ORDER BY classification_confidence DESC
        """, (project_id, classification))
        files = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return files


class Entity:
    """Entity model"""

    @staticmethod
    def create(project_id: str, entity_type: str, entity_value: str,
               source_file_id: str = None, confidence: float = None) -> str:
        """Create a new entity"""
        entity_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entities (id, project_id, entity_type, entity_value,
                                source_file_id, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entity_id, project_id, entity_type, entity_value,
              source_file_id, confidence, now))
        conn.commit()
        conn.close()

        return entity_id

    @staticmethod
    def get_by_project(project_id: str) -> List[Dict[str, Any]]:
        """Get all entities for a project"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM entities
            WHERE project_id = ?
            ORDER BY entity_type, confidence DESC
        """, (project_id,))
        entities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return entities

    @staticmethod
    def get_by_type(project_id: str, entity_type: str) -> List[Dict[str, Any]]:
        """Get entities by type"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM entities
            WHERE project_id = ? AND entity_type = ?
            ORDER BY confidence DESC
        """, (project_id, entity_type))
        entities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return entities


class GeneratedReport:
    """Generated report model"""

    @staticmethod
    def create(project_id: str, report_type: str) -> str:
        """Create a new report"""
        report_id = str(uuid.uuid4())

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO generated_reports (id, project_id, report_type, status)
            VALUES (?, ?, ?, 'draft')
        """, (report_id, project_id, report_type))
        conn.commit()
        conn.close()

        return report_id

    @staticmethod
    def get_by_project(project_id: str) -> List[Dict[str, Any]]:
        """Get all reports for a project"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM generated_reports
            WHERE project_id = ?
            ORDER BY generated_at DESC
        """, (project_id,))
        reports = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reports

    @staticmethod
    def get_by_id(report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM generated_reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update(report_id: str, **kwargs):
        """Update report fields"""
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [report_id]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE generated_reports SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()


class ReportSection:
    """Report section model"""

    @staticmethod
    def create(report_id: str, section_number: int, section_title: str,
               content: str = None, sources: List[str] = None) -> str:
        """Create a new report section"""
        section_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        sources_json = json.dumps(sources) if sources else None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO report_sections (id, report_id, section_number,
                                        section_title, content, sources, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (section_id, report_id, section_number, section_title,
              content, sources_json, now))
        conn.commit()
        conn.close()

        return section_id

    @staticmethod
    def get_by_report(report_id: str) -> List[Dict[str, Any]]:
        """Get all sections for a report"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM report_sections
            WHERE report_id = ?
            ORDER BY section_number
        """, (report_id,))
        sections = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sections

    @staticmethod
    def update(section_id: str, content: str, edited: bool = True):
        """Update section content"""
        now = datetime.now().isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE report_sections
            SET content = ?, edited = ?, edited_at = ?
            WHERE id = ?
        """, (content, edited, now, section_id))
        conn.commit()
        conn.close()


class Settings:
    """Settings model"""

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a setting value"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        return default

    @staticmethod
    def set(key: str, value: Any):
        """Set a setting value"""
        if not isinstance(value, str):
            value = json.dumps(value)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """Get all settings"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {}
        for row in cursor.fetchall():
            try:
                settings[row['key']] = json.loads(row['value'])
            except:
                settings[row['key']] = row['value']
        conn.close()
        return settings


# Initialize database on import
init_database()
