"""Request validation schemas for invoice processing API."""
from werkzeug.datastructures import FileStorage


class InvoiceProcessingRequest:
    """Request validator for invoice processing endpoint."""

    @staticmethod
    def validate_files(files):
        """
        Validate uploaded PDF files.

        Args:
            files: List of FileStorage objects from request.files

        Returns:
            tuple: (is_valid, error_message, error_code)

        Raises:
            ValueError with error details if validation fails
        """
        if not files:
            return False, 'No PDF files were provided in the request', 'NO_FILES_PROVIDED'

        # Check file count
        if len(files) > 100:
            return False, f'Maximum 100 files allowed per request (received {len(files)})', 'TOO_MANY_FILES'

        # Validate each file
        total_size = 0
        for file in files:
            if not isinstance(file, FileStorage):
                continue

            # Check filename
            if not file.filename:
                return False, 'One or more files have no filename', 'INVALID_FILE'

            # Check file extension
            if not file.filename.lower().endswith('.pdf'):
                return False, f'File "{file.filename}" is not a valid PDF', 'INVALID_FILE_TYPE'

            # Get file size by seeking to end
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

        return True, None, None

    @staticmethod
    def validate_pdf_magic_number(file_stream):
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
