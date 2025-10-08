# Windows Executable Build Instructions

## Prerequisites

- Windows 10 or later
- Python 3.12 installed
- All dependencies from `src/requirements.txt` installed

## Build Process

### 1. Install Dependencies

```cmd
pip install -r src/requirements.txt
```

This will install:
- Flask 3.0+
- Flask-CORS 4.0+
- waitress 3.0+
- pdfplumber 0.10+
- openpyxl 3.1+
- PyInstaller 6.0+
- python-magic-bin 0.4.14+
- pytest and pytest-flask (for testing)

### 2. Run Build Script

```cmd
build.bat
```

This will:
1. Clean any previous builds (`build/` and `dist/` directories)
2. Run PyInstaller with the `invoice-api.spec` configuration
3. Create `dist/invoice-api.exe` (100-150MB expected size)

### 3. Verify Build

The executable will be located at:
```
dist/invoice-api.exe
```

Expected size: 100-150 MB (includes Python runtime and all dependencies)

## Running the Executable

### Start the Server

```cmd
dist\invoice-api.exe
```

Expected output:
```
Serving on http://0.0.0.0:5000
```

### Test the API

#### Health Check
```cmd
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

#### Process Invoice
```cmd
curl -X POST http://localhost:5000/api/process ^
  -F "invoices=@path\to\invoice.pdf" ^
  -o output.xlsx
```

Expected:
- Status: 200 OK
- Output: `output.xlsx` file with extracted invoice data
- Header: `X-Processing-Summary` with JSON processing details

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode (default: `production`)
- `PORT`: Server port (default: `5000`)

Example:
```cmd
set PORT=8080
dist\invoice-api.exe
```

## Troubleshooting

### Build Issues

**Issue**: Missing module errors during build
**Solution**: Ensure all hiddenimports are listed in `invoice-api.spec`

**Issue**: Build takes very long (>10 minutes)
**Solution**: Normal for first build. Subsequent builds use cache and are faster.

**Issue**: Executable size exceeds 150MB
**Solution**: Normal - includes Python runtime, Flask, PDF processing, and Excel generation libraries.

### Runtime Issues

**Issue**: "Port already in use" error
**Solution**: Another process is using port 5000. Change port with `set PORT=8080`

**Issue**: Invoice processing fails
**Solution**: Check that PDF files are valid and not password-protected

**Issue**: Excel file not generated
**Solution**: Check write permissions in output directory and available disk space

## Testing with Sample Invoices

Sample invoice files are provided in `/invoices/`:
- `Example_CM360.pdf` - Campaign Manager 360
- `Example_DV360.pdf` - Display & Video 360
- `Example_GGAds.pdf` - Google Ads
- `Example_GGVAT.pdf` - Google VAT
- `Example Meta.pdf` - Meta (Facebook)

Test batch processing:
```cmd
curl -X POST http://localhost:5000/api/process ^
  -F "invoices=@invoices\Example_CM360.pdf" ^
  -F "invoices=@invoices\Example_DV360.pdf" ^
  -F "invoices=@invoices\Example_GGAds.pdf" ^
  -F "invoices=@invoices\Example_GGVAT.pdf" ^
  -F "invoices=@Example Meta.pdf" ^
  -o all_invoices.xlsx
```

Expected result: Single Excel file with 5 sheets (one per invoice type).

## Distribution

To distribute the executable:
1. Copy `dist/invoice-api.exe` to target machine
2. No Python installation required on target machine
3. Executable is self-contained with all dependencies

## Build Artifacts

Files generated during build (gitignored):
- `build/` - Temporary build files
- `dist/` - Final executable
- `invoice-api.spec` - PyInstaller configuration (tracked in git)

## Notes

- First build takes 5-10 minutes
- Subsequent builds take 1-2 minutes (using cache)
- Executable runs on Windows 10+ without Python installed
- Console window shows server logs and status
