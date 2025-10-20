"""
File handling utilities
"""
from pathlib import Path
from PyPDF2 import PdfReader
from config import Config


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def truncate_filename(filename: str, max_length: int = 20) -> str:
    """Smart filename truncation that preserves extension"""
    if len(filename) <= max_length:
        return filename
    
    # Get filename without extension
    last_dot_index = filename.rfind('.')
    if last_dot_index > 0:
        name = filename[:last_dot_index]
        extension = filename[last_dot_index:]
    else:
        name = filename
        extension = ''
    
    # Truncate name only, keep extension
    available_length = max_length - len(extension) - 3  # 3 for "..."
    if available_length > 0:
        return name[:available_length] + '...' + extension
    else:
        # Extension too long, truncate everything
        return filename[:max_length - 3] + '...'


def count_pdf_pages(pdf_path: str) -> int:
    """Count pages in a PDF file using PyPDF2"""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        print(f'PDF page count failed: {e}')
        return 0
