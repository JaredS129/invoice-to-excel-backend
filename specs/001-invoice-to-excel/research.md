# Research: Flask API & PyInstaller Packaging

**Feature**: Invoice Processing API
**Created**: 2025-10-08
**Status**: Complete

## Overview

This document consolidates research findings for building a Flask REST API that wraps existing invoice processing logic and packages it as a portable Windows executable using PyInstaller.

## Key Research Areas

### 1. Flask API Design for File Upload

**Decision**: Use Flask with `multipart/form-data` for batch file uploads

**Rationale**:
- Flask's `request.files` provides simple interface for handling multiple file uploads
- `werkzeug.datastructures.FileStorage` handles file streaming efficiently
- Native support for `multipart/form-data` encoding allows clients to upload multiple PDFs in single request
- Can use Flask-CORS for cross-origin support if needed later

**Alternatives Considered**:
- **FastAPI**: More modern with async support and automatic OpenAPI docs, but adds complexity for simple use case and PyInstaller packaging can be more challenging
- **Base64 JSON encoding**: Simpler for testing but inefficient for large files (33% size overhead)

**Implementation Pattern**:
```python
@app.route('/api/process', methods=['POST'])
def process_invoices():
    files = request.files.getlist('invoices')  # Accept multiple files
    # Process files and return Excel
```

### 2. PyInstaller Configuration for Flask Apps

**Decision**: Use PyInstaller in `--onefile` mode with explicit data file collection

**Rationale**:
- `--onefile` creates single executable - meets "portable" requirement
- Must use `--add-data` to include non-Python resources (though our app has none)
- Hidden imports for `pdfplumber` and `openpyxl` dependencies must be specified
- Windows-specific: Can add icon and version info for professional appearance

**Alternatives Considered**:
- **cx_Freeze**: Less popular, smaller community, harder to debug issues
- **Nuitka**: Compiles to C, faster but longer build times and more complex setup
- **PyInstaller --onedir**: Creates folder with dependencies - harder to distribute

**Configuration Pattern** (invoice-api.spec):
```python
a = Analysis(
    ['src/api/app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pdfplumber',
        'openpyxl',
        'PIL',  # pdfplumber dependency
        'werkzeug',
        'flask',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)
```

### 3. Temporary File Management

**Decision**: Use Python's `tempfile.TemporaryDirectory` with context managers

**Rationale**:
- Automatic cleanup when request completes (using `try/finally`)
- OS-level unique directory creation prevents conflicts between concurrent requests
- Works on Windows without permission issues
- No manual cleanup logic needed

**Alternatives Considered**:
- **Custom temp directory**: More control but requires manual cleanup and collision handling
- **In-memory processing**: Not viable for potentially large PDF files and Excel outputs
- **Persistent storage with cleanup jobs**: Over-engineered for stateless API

**Implementation Pattern**:
```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    # Save uploaded PDFs to tmpdir
    # Process invoices
    # Generate Excel in tmpdir
    # Send Excel file
    # Automatic cleanup on exit
```

### 4. Error Handling and Response Format

**Decision**: JSON responses with standard HTTP status codes and structured error format

**Rationale**:
- Consistent response format makes client integration easier
- HTTP status codes provide semantic meaning (400 for client errors, 500 for server errors)
- Structured errors with `error_code` and `message` fields enable client-side error handling
- Success responses include `data` field with processing summary

**Alternatives Considered**:
- **Binary Excel with error headers**: Mixed response types complicate client logic
- **Always return 200 with error in JSON**: Violates REST principles, harder to monitor
- **Streaming responses**: Overkill for batch processing, complicates error handling

**Response Format**:
```json
// Success
{
  "success": true,
  "data": {
    "total": 10,
    "successful": 9,
    "failed": 1,
    "failures": [
      {
        "filename": "invoice10.pdf",
        "error": "Could not detect invoice type"
      }
    ]
  }
}

// Error
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only PDF files are supported"
  }
}
```

### 5. Build Script for Windows

**Decision**: Create `build.bat` batch script with PyInstaller command

**Rationale**:
- Single command execution meets user requirement
- Batch script is native to Windows, no additional tools needed
- Can chain commands: clean previous build → run PyInstaller → test executable
- Easy to version control and customize

**Alternatives Considered**:
- **Makefile**: Requires make.exe on Windows (not standard)
- **Python build script**: Adds dependency, batch script sufficient
- **PowerShell script**: Modern but .bat has wider compatibility

**Build Script** (build.bat):
```batch
@echo off
echo Building Invoice Processing API executable...

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Run PyInstaller
python -m PyInstaller invoice-api.spec --clean

echo Build complete! Executable located at: dist\invoice-api.exe
```

### 6. Request Validation and File Type Checking

**Decision**: Validate files early using magic number detection (not just extension)

**Rationale**:
- File extension can be spoofed - magic numbers are reliable
- Early validation fails fast before processing
- `python-magic-bin` package works on Windows without system dependencies
- Prevents processing malformed or malicious files

**Alternatives Considered**:
- **Extension-only check**: Easy to bypass, unreliable
- **Try-catch during processing**: Wastes resources, unclear error messages
- **Delegating to pdfplumber**: Error messages less user-friendly

**Implementation Pattern**:
```python
import magic

def validate_pdf(file_stream):
    """Validate file is actually a PDF using magic numbers."""
    header = file_stream.read(4)
    file_stream.seek(0)  # Reset stream

    if header != b'%PDF':
        raise ValueError("File is not a valid PDF")
```

### 7. Concurrent Request Handling

**Decision**: Use Flask's default Werkzeug server for development, Waitress for production

**Rationale**:
- Werkzeug (Flask default) is single-threaded - fine for local/dev use
- Waitress is pure-Python WSGI server that works on Windows without compilation
- Waitress supports thread pool (configurable concurrency)
- Packaged in executable - no external web server needed

**Alternatives Considered**:
- **Gunicorn**: Unix-only, won't work on Windows
- **uWSGI**: Requires compilation, complex setup
- **Embedded HTTP server**: Reinventing the wheel

**Implementation Pattern**:
```python
# Production mode
from waitress import serve

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True)
    else:
        # Production server for executable
        serve(app, host='0.0.0.0', port=5000, threads=5)
```

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Web Framework | Flask | 3.0+ | REST API implementation |
| WSGI Server | Waitress | 3.0+ | Production HTTP server (Windows-compatible) |
| PDF Processing | pdfplumber | 0.10+ | Existing invoice extraction logic |
| Excel Generation | openpyxl | 3.1+ | Existing Excel writing logic |
| Packaging | PyInstaller | 6.0+ | Create portable Windows executable |
| File Validation | python-magic-bin | 0.4+ | PDF magic number validation (Windows) |
| Testing | pytest | 7.4+ | Unit and integration testing |
| API Testing | pytest-flask | 1.3+ | Flask-specific test utilities |

## Dependencies Update

**New entries for requirements.txt**:
```
Flask>=3.0.0
waitress>=3.0.0
python-magic-bin>=0.4.14  # Windows-compatible
pytest-flask>=1.3.0
```

**Existing dependencies** (keep as-is):
```
pdfplumber>=0.10.0
openpyxl>=3.1.0
pytest>=7.4.0
```

## Implementation Notes

### Import Path Adjustments

The existing code uses relative imports from `src/` root. With new API structure:
- Existing extractors: No changes needed (already using absolute imports from `src.extractors`)
- Existing detectors: No changes needed (already using absolute imports from `src.invoice_detectors`)
- New API code: Use absolute imports (`from src.services.invoice_service import ...`)

### Process Flow

1. Client sends POST to `/api/process` with PDF files
2. Flask receives multipart/form-data request
3. `file_service.py` validates and saves files to temp directory
4. `invoice_service.py` iterates through PDFs:
   - Uses existing `InvoiceProcessor` class
   - Detects type with existing detector logic
   - Extracts data with existing extractor classes
5. `excel_writer.py` generates Excel file in temp directory (existing code)
6. Flask sends Excel file as response with proper headers
7. Temp directory auto-cleaned on request completion

### Build and Run Workflow

**Development**:
```bash
python -m src.api.app  # Run Flask dev server
pytest tests/          # Run tests
```

**Build Executable**:
```bash
build.bat  # Creates dist/invoice-api.exe
```

**Run Executable**:
```bash
dist/invoice-api.exe  # Starts server on http://localhost:5000
```

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| PyInstaller hidden import issues | Explicitly list all dependencies in .spec file; test with real PDFs |
| Large executable size | Accept tradeoff for portability; ~100-150MB expected with dependencies |
| Concurrent request file conflicts | Use unique temp directories per request (tempfile.TemporaryDirectory) |
| Long processing timeout | Set appropriate timeout (5 min), provide progress logging |
| Memory exhaustion on large batches | Limit max files per request (100), validate file sizes |

## Open Questions Resolved

1. **Q: How to handle Excel file delivery?**
   - A: Direct file download via `send_file()` with proper MIME type and attachment headers

2. **Q: Should API be synchronous or async?**
   - A: Synchronous is sufficient - processing is CPU-bound (PDF parsing), not I/O-bound

3. **Q: How to test the built executable?**
   - A: Create test script that calls the API with sample PDFs and validates Excel output

4. **Q: Should we maintain backward compatibility with CLI (`process_invoices.py`)?**
   - A: Yes, keep it - no conflicts, useful for testing/debugging without API layer

