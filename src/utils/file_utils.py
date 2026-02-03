"""
File handling utilities
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import hashlib


def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return Path(filename).suffix.lower()


def get_file_type(filename: str) -> Optional[str]:
    """Determine file type from extension"""
    ext = get_file_extension(filename)

    type_mapping = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'docx',
        '.xlsx': 'xlsx',
        '.xls': 'xlsx',
        '.txt': 'txt'
    }

    return type_mapping.get(ext)


def is_supported_file(filename: str) -> bool:
    """Check if file type is supported"""
    return get_file_type(filename) is not None


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes"""
    return file_path.stat().st_size if file_path.exists() else 0


def format_file_size(size_bytes: int) -> str:
    """Format file size for display"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing special characters"""
    # Remove path components
    filename = Path(filename).name

    # Replace spaces and special chars
    safe_name = "".join(c if c.isalnum() or c in '.-_' else '_' for c in filename)

    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed_file"

    return safe_name


def ensure_unique_filename(directory: Path, filename: str) -> str:
    """Ensure filename is unique in directory by adding counter if needed"""
    file_path = directory / filename
    if not file_path.exists():
        return filename

    name = Path(filename).stem
    ext = Path(filename).suffix
    counter = 1

    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_filename
        counter += 1


def copy_file(source: Path, destination: Path) -> bool:
    """Copy file from source to destination"""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False


def move_file(source: Path, destination: Path) -> bool:
    """Move file from source to destination"""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False


def delete_file(file_path: Path) -> bool:
    """Delete file"""
    try:
        if file_path.exists():
            file_path.unlink()
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def create_directory(directory: Path) -> bool:
    """Create directory if it doesn't exist"""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False


def list_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """List files in directory, optionally filtered by extensions"""
    if not directory.exists():
        return []

    files = []
    for item in directory.iterdir():
        if item.is_file():
            if extensions is None or item.suffix.lower() in extensions:
                files.append(item)

    return sorted(files)


def get_directory_size(directory: Path) -> int:
    """Get total size of all files in directory"""
    total_size = 0
    for item in directory.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
    return total_size


def read_text_file(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """Read text file content"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file with latin-1: {e}")
            return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def write_text_file(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """Write text to file"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False


def get_relative_path(file_path: Path, base_path: Path) -> Path:
    """Get relative path from base path"""
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        return file_path


def validate_path(path: Path) -> bool:
    """Validate that path exists and is accessible"""
    try:
        return path.exists() and os.access(path, os.R_OK)
    except Exception:
        return False


def get_file_info(file_path: Path) -> Dict:
    """Get comprehensive file information"""
    if not file_path.exists():
        return {}

    stat = file_path.stat()

    return {
        'name': file_path.name,
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'extension': file_path.suffix,
        'type': get_file_type(file_path.name),
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'is_file': file_path.is_file(),
        'is_dir': file_path.is_dir()
    }
