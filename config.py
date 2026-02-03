"""
Configuration settings for EU MDR Clinical Documentation Generator
"""
from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
PROJECTS_DIR = DATA_DIR / "projects"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
TEMPLATES_DIR = BASE_DIR / "templates"
PROMPTS_DIR = BASE_DIR / "prompts"
ASSETS_DIR = BASE_DIR / "assets"

# Database
DATABASE_PATH = DATA_DIR / "app.db"

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
OLLAMA_TEMPERATURE = 0.3
OLLAMA_MAX_TOKENS = 2000

# Embedding settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_CHUNKS_FOR_CONTEXT = 10

# Processing settings
MAX_CONTEXT_TOKENS = 6000
BATCH_SIZE = 10

# Document categories for classification
DOCUMENT_CATEGORIES = {
    "device_description": {
        "description": "Device specifications, design documents, drawings, materials",
        "keywords": ["specification", "design", "drawing", "BOM", "materials", "dimensions"]
    },
    "intended_use": {
        "description": "Intended purpose, indications for use, IFU, labeling",
        "keywords": ["intended use", "indication", "IFU", "instructions for use", "contraindication"]
    },
    "risk_management": {
        "description": "Risk analysis, FMEA, FTA, hazard analysis, ISO 14971",
        "keywords": ["risk", "FMEA", "hazard", "fault tree", "ISO 14971", "severity", "probability"]
    },
    "biocompatibility": {
        "description": "Biocompatibility testing per ISO 10993",
        "keywords": ["biocompatibility", "ISO 10993", "cytotoxicity", "sensitization", "irritation"]
    },
    "clinical_study": {
        "description": "Clinical investigation reports, clinical trial data",
        "keywords": ["clinical study", "clinical investigation", "trial", "patient", "endpoint", "efficacy"]
    },
    "literature": {
        "description": "Published literature, journal articles, systematic reviews",
        "keywords": ["published", "journal", "study", "abstract", "conclusion", "peer-reviewed"]
    },
    "performance_testing": {
        "description": "Bench testing, performance verification, validation",
        "keywords": ["test report", "verification", "validation", "performance", "bench test"]
    },
    "sterilization": {
        "description": "Sterilization validation, sterility assurance",
        "keywords": ["sterilization", "sterility", "SAL", "bioburden", "EO", "gamma"]
    },
    "software": {
        "description": "Software documentation, IEC 62304",
        "keywords": ["software", "IEC 62304", "algorithm", "cybersecurity", "SOUP"]
    },
    "post_market": {
        "description": "Post-market data, complaints, vigilance, PMS",
        "keywords": ["complaint", "adverse event", "vigilance", "PMS", "PMCF", "feedback"]
    },
    "regulatory": {
        "description": "Previous submissions, certificates, regulatory correspondence",
        "keywords": ["510k", "CE mark", "certificate", "notified body", "submission"]
    },
    "quality": {
        "description": "Quality system documents, SOPs, manufacturing",
        "keywords": ["SOP", "quality", "manufacturing", "process", "DHF", "DMR"]
    },
    "labeling": {
        "description": "Labels, packaging, marketing materials",
        "keywords": ["label", "packaging", "UDI", "symbol", "marketing"]
    },
    "other": {
        "description": "Documents that don't fit other categories",
        "keywords": []
    }
}

# Entity extraction fields
DEVICE_ENTITIES = {
    "device_name": "Official device name",
    "device_model": "Model number/identifier",
    "device_class": "MDR classification (I, IIa, IIb, III)",
    "manufacturer": "Manufacturer name",
    "intended_purpose": "Primary intended use statement",
    "indications": "List of indications for use",
    "contraindications": "List of contraindications",
    "target_population": "Patient population",
    "anatomical_location": "Where device is used/implanted",
    "device_materials": "Materials in contact with patient",
    "sterile": "Yes/No if sterile",
    "single_use": "Yes/No if single use",
    "implantable": "Yes/No if implantable",
    "active_device": "Yes/No if active",
    "contains_software": "Yes/No if contains software",
    "contains_medicinal": "Yes/No if contains medicinal substance",
    "equivalent_devices": "List of equivalent/predicate devices",
    "applicable_standards": "List of harmonized standards applied"
}

# Report types
REPORT_TYPES = {
    "CEP": "Clinical Evaluation Plan",
    "CER": "Clinical Evaluation Report",
    "SSCP": "Summary of Safety and Clinical Performance",
    "LSR": "Literature Search Report"
}

# UI theme colors
THEME = {
    "bg_primary": "#0E1117",
    "bg_secondary": "#1E2128",
    "bg_tertiary": "#262B36",
    "accent_primary": "#00D4AA",
    "accent_secondary": "#3B82F6",
    "text_primary": "#FAFAFA",
    "text_secondary": "#8B949E",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "border": "#30363D"
}

# File type extensions
SUPPORTED_EXTENSIONS = {
    "pdf": [".pdf"],
    "docx": [".docx", ".doc"],
    "xlsx": [".xlsx", ".xls"],
    "txt": [".txt"]
}

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR, PROJECTS_DIR, CHROMA_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
