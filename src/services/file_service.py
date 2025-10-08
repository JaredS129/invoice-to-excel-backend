"""File handling service for invoice processing."""
import os
import re
from pathlib import Path
from typing import List, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class FileService:
    """Service for handling file uploads and validation."""

    @staticmethod
    def validate_pdf_files(files: List[FileStorage]) -> Tuple[bool, str, str]:
        """
        Validate uploaded PDF files.

        Args:
            files: List of FileStorage objects from Flask request

        Returns:
            Tuple of (is_valid, error_message, error_code)
        """
        if not files or len(files) == 0:
            return False, 'No PDF files were provided in the request', 'NO_FILES_PROVIDED'

        # Check file count
        if len(files) > 100:
            return False, f'Maximum 100 files allowed per request (received {len(files)})', 'TOO_MANY_FILES'

        # Validate each file
        total_size = 0
        for file in files:
            if not file or not file.filename:
                return False, 'One or more files have no filename', 'INVALID_FILE'

            # Check file extension
            if not file.filename.lower().endswith('.pdf'):
                return False, f'File "{file.filename}" is not a valid PDF', 'INVALID_FILE_TYPE'

            # Get file size
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset to beginning

            # Check individual file size (10MB)
            if size > 10 * 1024 * 1024:
                size_mb = size / (1024 * 1024)
                return False, f'File "{file.filename}" exceeds 10MB limit (actual: {size_mb:.1f}MB)', 'FILE_TOO_LARGE'

            total_size += size

        # Check total request size (100MB)
        if total_size > 100 * 1024 * 1024:
            total_mb = total_size / (1024 * 1024)
            return False, f'Total request size ({total_mb:.1f}MB) exceeds 100MB limit', 'REQUEST_TOO_LARGE'

        return True, '', ''

    @staticmethod
    def validate_pdf_magic_number(file_stream) -> bool:
        """
        Validate PDF magic number (%PDF).

        Args:
            file_stream: File-like object

        Returns:
            bool: True if valid PDF, False otherwise
        """
        # Read first 4 bytes
        header = file_stream.read(4)
        file_stream.seek(0)  # Reset to beginning

        # Check for PDF magic number
        return header == b'%PDF'

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing special characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for file system
        """
        # Use werkzeug's secure_filename for basic sanitization
        base = secure_filename(filename)

        # Additional cleanup: remove any remaining special chars
        base = re.sub(r'[^\w\s\-\.]', '_', base)

        # Ensure we have a filename
        if not base or base == '.pdf':
            base = 'invoice.pdf'

        return base

    @staticmethod
    def save_uploaded_files(files: List[FileStorage], temp_dir: str) -> List[str]:
        """
        Save uploaded files to temporary directory.

        Args:
            files: List of FileStorage objects
            temp_dir: Path to temporary directory

        Returns:
            List of saved file paths

        Raises:
            IOError: If file cannot be saved
        """
        saved_paths = []

        for idx, file in enumerate(files):
            # Sanitize filename
            safe_name = FileService.sanitize_filename(file.filename)

            # Ensure unique filename by adding index if needed
            name_parts = safe_name.rsplit('.', 1)
            if len(name_parts) == 2:
                unique_name = f"{name_parts[0]}_{idx}.{name_parts[1]}"
            else:
                unique_name = f"{safe_name}_{idx}"

            # Build full path
            file_path = os.path.join(temp_dir, unique_name)

            # Save file
            file.save(file_path)
            saved_paths.append(file_path)

        return saved_paths
