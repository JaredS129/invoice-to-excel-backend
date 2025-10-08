# Quickstart Guide: Invoice Processing API

**Feature**: Invoice Processing API
**Created**: 2025-10-08
**Audience**: Developers integrating with or deploying the API

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Running the API (Development)](#running-the-api-development)
4. [Testing the API](#testing-the-api)
5. [Building the Windows Executable](#building-the-windows-executable)
6. [Running the Executable](#running-the-executable)
7. [API Usage Examples](#api-usage-examples)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### For Development

- **Python 3.12** or higher
- **pip** package manager
- **Git** (to clone repository)

### For Building Executable

- All development prerequisites
- **Windows 10+** operating system
- **Minimum 2GB free disk space** (for PyInstaller build)

### For Running Executable Only

- **Windows 10+** (no Python required)

---

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd invoice-to-excel-backend
git checkout 001-invoice-to-excel
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (Command Prompt)**:
```cmd
venv\Scripts\activate
```

**Windows (PowerShell)**:
```powershell
venv\Scripts\Activate.ps1
```

**Linux/macOS**:
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r src/requirements.txt
```

**Expected dependencies**:
- Flask (web framework)
- Waitress (production WSGI server)
- pdfplumber (PDF extraction)
- openpyxl (Excel generation)
- pytest (testing)
- python-magic-bin (file validation)

### 5. Verify Installation

```bash
python -c "import flask, pdfplumber, openpyxl; print('Dependencies OK')"
```

You should see: `Dependencies OK`

---

## Running the API (Development)

### Start Development Server

From repository root:

```bash
python -m src.api.app
```

**Expected output**:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Verify API is Running

Open browser or use curl:

```bash
curl http://localhost:5000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Testing the API

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Suites

**Unit tests only**:
```bash
pytest tests/unit/
```

**Integration tests only**:
```bash
pytest tests/integration/
```

**Contract tests (API spec compliance)**:
```bash
pytest tests/contract/
```

### Test with Sample PDFs

Assuming you have sample invoice PDFs in `samples/` directory:

```bash
curl -X POST http://localhost:5000/api/process \
  -F "invoices=@samples/dv360_invoice.pdf" \
  -F "invoices=@samples/googleads_invoice.pdf" \
  -o output.xlsx
```

Check `output.xlsx` - should contain processed data with separate sheets for each invoice type.

---

## Building the Windows Executable

### Prerequisites Check

Ensure you're on Windows with Python 3.12+ and all dependencies installed.

### Build Command

From repository root:

```cmd
build.bat
```

**What this does**:
1. Cleans previous build artifacts (`build/` and `dist/`)
2. Runs PyInstaller with `invoice-api.spec` configuration
3. Creates single executable at `dist/invoice-api.exe`

**Build output**:
```
Building Invoice Processing API executable...
...
Build complete! Executable located at: dist\invoice-api.exe
```

### Build Time

- **First build**: 3-5 minutes (downloads dependencies, analyzes imports)
- **Subsequent builds**: 1-2 minutes (uses cached analysis)

### Executable Size

Expected size: **100-150 MB**

This includes:
- Python runtime
- Flask and dependencies
- pdfplumber (with Pillow)
- openpyxl
- All extractor logic

---

## Running the Executable

### Start the API Server

From `dist/` directory:

```cmd
invoice-api.exe
```

**Expected output**:
```
Serving on http://0.0.0.0:5000
```

The API is now running and accessible at `http://localhost:5000`

### Run on Different Port

```cmd
set PORT=8080
invoice-api.exe
```

### Background Mode (Windows)

**Using start command**:
```cmd
start /B invoice-api.exe > api.log 2>&1
```

**Stop background server**:
```cmd
taskkill /IM invoice-api.exe /F
```

### Auto-start on Windows Boot

Create a shortcut to `invoice-api.exe` and place in:
```
C:\Users\<YourUser>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## API Usage Examples

### Example 1: Process Single Invoice

```bash
curl -X POST http://localhost:5000/api/process \
  -F "invoices=@invoice.pdf" \
  -o output.xlsx
```

### Example 2: Process Multiple Invoices

```bash
curl -X POST http://localhost:5000/api/process \
  -F "invoices=@invoice1.pdf" \
  -F "invoices=@invoice2.pdf" \
  -F "invoices=@invoice3.pdf" \
  -o output.xlsx
```

### Example 3: Process with Error Handling (Python)

```python
import requests

url = "http://localhost:5000/api/process"
files = [
    ('invoices', open('invoice1.pdf', 'rb')),
    ('invoices', open('invoice2.pdf', 'rb')),
]

response = requests.post(url, files=files)

if response.status_code == 200:
    # Success - save Excel file
    with open('output.xlsx', 'wb') as f:
        f.write(response.content)

    # Check processing summary
    summary = response.headers.get('X-Processing-Summary')
    print(f"Processing summary: {summary}")
else:
    # Error - parse JSON
    error = response.json()
    print(f"Error: {error['error']['message']}")
```

### Example 4: Process with Progress Tracking (PowerShell)

```powershell
$files = @(
    @{Name="invoices"; FileName="invoice1.pdf"; FilePath="C:\invoices\invoice1.pdf"},
    @{Name="invoices"; FileName="invoice2.pdf"; FilePath="C:\invoices\invoice2.pdf"}
)

$multipartContent = [System.Net.Http.MultipartFormDataContent]::new()
foreach ($file in $files) {
    $fileStream = [System.IO.File]::OpenRead($file.FilePath)
    $fileContent = [System.Net.Http.StreamContent]::new($fileStream)
    $multipartContent.Add($fileContent, $file.Name, $file.FileName)
}

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/process" `
    -Method Post `
    -Body $multipartContent `
    -OutFile "output.xlsx"

Write-Host "Processing complete. Excel saved to output.xlsx"
```

### Example 5: Health Check

```bash
curl http://localhost:5000/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError" when running API

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r src/requirements.txt
```

### Issue: "Port 5000 already in use"

**Cause**: Another application is using port 5000

**Solution**: Run on different port
```bash
set FLASK_RUN_PORT=8080
python -m src.api.app
```

Or for executable:
```bash
set PORT=8080
invoice-api.exe
```

### Issue: "File is not a valid PDF" error

**Cause**: Uploaded file is corrupted or not actually a PDF

**Solution**:
1. Verify file opens in PDF reader
2. Check file starts with `%PDF` magic number:
   ```bash
   head -c 4 yourfile.pdf
   # Should output: %PDF
   ```

### Issue: "Could not detect invoice type"

**Cause**: PDF doesn't match any supported invoice format

**Solution**:
1. Verify invoice is from supported platforms (DV360, Google Ads, CM360, Google VAT, Meta)
2. Check PDF is not password-protected
3. Ensure invoice follows standard format for its platform

### Issue: Executable build fails with "ImportError"

**Cause**: PyInstaller missed a hidden import

**Solution**: Edit `invoice-api.spec` and add missing module to `hiddenimports`:
```python
hiddenimports=[
    'pdfplumber',
    'openpyxl',
    'PIL',
    'werkzeug',
    'flask',
    'your_missing_module',  # Add here
],
```

Then rebuild:
```bash
build.bat
```

### Issue: Excel output is empty

**Cause**: All invoices failed to process

**Solution**:
1. Check `X-Processing-Summary` header for failure details
2. Try processing one invoice at a time to isolate issue
3. Verify invoice PDFs are readable and correctly formatted

### Issue: Request timeout (5 minutes exceeded)

**Cause**: Too many invoices or very large PDFs

**Solution**:
1. Process in smaller batches (e.g., 20-30 at a time)
2. Reduce PDF file sizes if possible
3. Check for corrupted PDFs causing extraction to hang

### Issue: Memory error during processing

**Cause**: Insufficient RAM for large batch

**Solution**:
1. Reduce batch size (try 10-20 invoices per request)
2. Close other applications to free memory
3. Check individual PDF sizes (very large PDFs may need to be split)

---

## Next Steps

### For Developers

1. **Review API Contract**: See [contracts/api-spec.yaml](./contracts/api-spec.yaml)
2. **Understand Data Model**: See [data-model.md](./data-model.md)
3. **Read Implementation Plan**: See [plan.md](./plan.md)
4. **Generate Tasks**: Run `/speckit.tasks` to create implementation checklist

### For Integrators

1. **Test with Sample Data**: Use your actual invoice PDFs to verify compatibility
2. **Implement Error Handling**: Handle all error codes from [contracts/api-spec.yaml](./contracts/api-spec.yaml)
3. **Monitor Processing**: Use `X-Processing-Summary` header for batch monitoring
4. **Plan Deployment**: Decide on server infrastructure (local vs. network-accessible)

### For End Users

1. **Deploy Executable**: Copy `invoice-api.exe` to target Windows machine
2. **Start Server**: Run executable (optionally set up auto-start)
3. **Integrate with Workflow**: Use curl, PowerShell, or custom tools to send invoices
4. **Verify Output**: Check Excel files have correct data and formatting

---

## Support

For issues or questions:
1. Check this Quickstart guide
2. Review [Troubleshooting](#troubleshooting) section
3. Consult [data-model.md](./data-model.md) for data structure details
4. See [contracts/api-spec.yaml](./contracts/api-spec.yaml) for complete API reference

