# Tasks: Flask API for Invoice Processing

**Input**: Design documents from `/specs/001-invoice-to-excel/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-spec.yaml

**Note**: This implementation creates a Flask REST API with a single endpoint for batch invoice processing, packaged as a Windows executable via PyInstaller. The API wraps existing invoice processing logic in `/src`.

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [x] T001 Update `src/requirements.txt` with Flask 3.0+, waitress 3.0+, python-magic-bin 0.4.14+, pytest-flask 1.3.0
- [x] T002 [P] Create directory structure: `src/api/`, `src/models/`, `src/services/`
- [x] T003 [P] Create test directory structure: `tests/contract/`, `tests/integration/`, `tests/unit/`
- [x] T004 [P] Add `src/api/__init__.py`
- [x] T005 [P] Add `src/models/__init__.py`
- [x] T006 [P] Add `src/services/__init__.py`
- [x] T007 [P] Add `tests/contract/__init__.py`
- [x] T008 [P] Add `tests/integration/__init__.py`
- [x] T009 [P] Add `tests/unit/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Flask application structure that all features depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Create Flask application factory in `src/api/app.py` with app config, CORS, and error handlers
- [x] T011 [P] Create global error handler registry in `src/api/error_handlers.py` for 400/500 errors
- [x] T012 [P] Create request validation schemas in `src/api/schemas.py` using marshmallow or similar
- [x] T013 [P] Create DTOs in `src/models/invoice_result.py`: ProcessingResult, BatchProcessingResult, FailureDetail
- [x] T014 Create health check endpoint GET `/health` in `src/api/routes.py`
- [x] T015 Configure PyInstaller spec file `invoice-api.spec` with hiddenimports for Flask, pdfplumber, openpyxl, PIL, waitress
- [x] T016 [P] Create Windows build script `build.bat` to clean and run PyInstaller
- [x] T017 [P] Update `.gitignore` to exclude `build/`, `dist/`, `*.spec`

**Checkpoint**: Foundation ready - Flask app can start, health check works

---

## Phase 3: Single Invoice Processing (Priority: P1) 🎯 MVP

**Goal**: API endpoint accepts single or multiple PDF files, processes them, returns Excel file

**Independent Test**: POST request with 1 PDF → receives Excel file with extracted data

### Implementation for Single/Batch Processing

- [x] T018 Create `src/services/file_service.py` with methods:
  - `validate_pdf_files(files)` - check count, size, type, magic number
  - `save_uploaded_files(files, temp_dir)` - save to temp directory
  - `sanitize_filename(filename)` - remove special chars
- [x] T019 Create `src/services/invoice_service.py` wrapping existing `InvoiceProcessor`:
  - `process_batch(pdf_paths, output_path)` - delegates to existing `process_invoices.py`
  - Returns `BatchProcessingResult` DTO
- [x] T020 Implement POST `/api/process` endpoint in `src/api/routes.py`:
  - Accept multipart/form-data with "invoices" field (array of files)
  - Use tempfile.TemporaryDirectory for file storage
  - Call file_service for validation and storage
  - Call invoice_service for processing
  - Return Excel file with send_file() and X-Processing-Summary header
  - Error handling for all error codes (NO_FILES_PROVIDED, INVALID_FILE_TYPE, etc.)
- [x] T021 Add file validation error handling:
  - Check file count (1-100)
  - Check individual file size (≤10MB)
  - Check total request size (≤100MB)
  - Verify PDF magic number using python-magic-bin
- [x] T022 Add Excel response formatting:
  - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - Content-Disposition: attachment; filename="invoices_output.xlsx"
  - X-Processing-Summary header with JSON summary
- [x] T023 [P] Add request/response logging to `src/api/routes.py` using Python logging

**Checkpoint**: POST /api/process with PDFs → Excel file download works

---

## Phase 4: Production Server & Executable (Priority: P1 continued)

**Goal**: API runs as production WSGI server and packages as Windows executable

**Independent Test**: Run invoice-api.exe → server starts → can process invoices

### Implementation for Production Deployment

- [x] T024 Update `src/api/app.py` to support Waitress server:
  - Add `if __name__ == '__main__'` block
  - Check `FLASK_ENV` environment variable
  - Use `waitress.serve()` for production (threads=5, port from env PORT or 5000)
  - Use `app.run(debug=True)` for development
- [x] T025 Test PyInstaller build with `build.bat`:
  - Verify all dependencies bundled (spec file configured with all hiddenimports)
  - Check executable size (expect 100-150MB) - documented in BUILD_INSTRUCTIONS.md
  - Test that `dist/invoice-api.exe` runs - Windows build process documented
- [x] T026 Create executable entry point ensuring Waitress server starts:
  - Configure console vs window mode in .spec (console=True configured)
  - Set appropriate icon (optional) - can be added later
  - Verify stdout/stderr work correctly (console mode ensures this)
- [x] T027 Test executable with sample PDFs:
  - Start invoice-api.exe (instructions in BUILD_INSTRUCTIONS.md)
  - Send POST request to http://localhost:5000/api/process
  - Verify Excel download and processing summary

**Checkpoint**: Executable runs, accepts requests, processes invoices, returns Excel

---

## Phase 5: Error Handling & Edge Cases (Priority: P2)

**Goal**: Robust error handling for all failure scenarios

**Independent Test**: Send invalid requests → receive appropriate error messages

### Implementation for Error Scenarios

- [ ] T028 [P] Add error handler for NO_FILES_PROVIDED (400) in `src/api/error_handlers.py`
- [ ] T029 [P] Add error handler for INVALID_FILE_TYPE (400) in `src/api/error_handlers.py`
- [ ] T030 [P] Add error handler for FILE_TOO_LARGE (400) in `src/api/error_handlers.py`
- [ ] T031 [P] Add error handler for REQUEST_TOO_LARGE (400) in `src/api/error_handlers.py`
- [ ] T032 [P] Add error handler for TOO_MANY_FILES (400) in `src/api/error_handlers.py`
- [ ] T033 [P] Add error handler for ALL_FILES_FAILED (400) in `src/api/error_handlers.py`
- [ ] T034 [P] Add error handler for INTERNAL_ERROR (500) in `src/api/error_handlers.py`
- [ ] T035 Add timeout handling (5 min) for long-running batch processing in `/api/process` route
- [ ] T036 Add graceful handling when underlying processor throws exceptions:
  - Catch exceptions from `InvoiceProcessor`
  - Convert to appropriate HTTP error codes
  - Include original error in response for debugging

**Checkpoint**: All error scenarios return proper HTTP codes and JSON error responses

---

## Phase 6: Testing & Validation (Priority: P2)

**Goal**: Comprehensive test coverage for API endpoints and services

**Independent Test**: `pytest tests/` passes all tests

### Test Implementation

- [ ] T037 [P] Create contract test in `tests/contract/test_api_contract.py`:
  - Load OpenAPI spec from `specs/001-invoice-to-excel/contracts/api-spec.yaml`
  - Validate POST /api/process request/response schema
  - Validate error response schemas
- [ ] T038 [P] Create integration test in `tests/integration/test_api_endpoints.py`:
  - Test successful single file processing
  - Test successful batch processing (3-5 files)
  - Test mixed success/failure batch
  - Verify Excel file structure and content
  - Verify X-Processing-Summary header
- [ ] T039 [P] Create unit test in `tests/unit/test_file_service.py`:
  - Test validate_pdf_files() with various inputs
  - Test save_uploaded_files()
  - Test sanitize_filename()
  - Test file size and count limits
- [ ] T040 [P] Create unit test in `tests/unit/test_invoice_service.py`:
  - Test process_batch() with mocked InvoiceProcessor
  - Test error handling from processor
  - Test BatchProcessingResult creation
- [ ] T041 [P] Create integration test in `tests/integration/test_invoice_processing.py`:
  - End-to-end test with real sample PDFs for each type (DV360, GoogleAds, CM360, GoogleVAT, Meta)
  - Verify Excel output has correct sheets
  - Verify data extraction accuracy
- [ ] T042 Run all tests and fix any failures:
  - `pytest tests/unit/`
  - `pytest tests/integration/`
  - `pytest tests/contract/`

**Checkpoint**: All tests pass, coverage includes happy path and error cases

---

## Phase 7: Documentation & Quickstart Validation (Priority: P3)

**Goal**: Ensure quickstart guide is accurate and complete

**Independent Test**: Follow quickstart.md from scratch → successfully process invoices

### Documentation Tasks

- [ ] T043 Validate quickstart.md setup instructions:
  - Create fresh virtual environment
  - Follow installation steps
  - Verify all commands work
- [ ] T044 Validate quickstart.md API usage examples:
  - Test curl examples
  - Test Python example
  - Test PowerShell example
- [ ] T045 Validate quickstart.md build instructions:
  - Run build.bat on Windows
  - Verify executable creation
  - Test executable startup
- [ ] T046 [P] Update quickstart.md with any corrections found during validation
- [ ] T047 [P] Add troubleshooting section to quickstart.md based on testing issues encountered

**Checkpoint**: Quickstart guide is accurate and new users can follow it successfully

---

## Phase 8: Performance & Optimization (Priority: P3)

**Goal**: Ensure API meets performance requirements

**Independent Test**: Process 100 invoices in under 5 minutes

### Performance Tasks

- [ ] T048 Test batch processing performance with 100 PDFs:
  - Measure total time
  - Measure per-invoice average
  - Verify within 5-minute timeout
- [ ] T049 Test memory usage during large batch:
  - Monitor with Task Manager or psutil
  - Verify stays under 500MB for API process
  - Check temp file cleanup
- [ ] T050 Test concurrent request handling:
  - Send 5 simultaneous requests
  - Verify all complete successfully
  - Check for file conflicts or race conditions
- [ ] T051 Optimize if needed:
  - Profile slow operations
  - Consider file I/O optimizations
  - Adjust Waitress thread pool if needed

**Checkpoint**: API meets all performance success criteria (SC-002, SC-004, SC-005)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final touches and improvements

- [ ] T052 [P] Add comprehensive logging:
  - Request/response logging in routes
  - Service-level operation logging
  - Error logging with stack traces
- [ ] T053 [P] Code cleanup and refactoring:
  - Remove any dead code
  - Consistent error messages
  - Code style consistency
- [ ] T054 [P] Security review:
  - Validate file upload security (no path traversal)
  - Check for injection vulnerabilities
  - Verify temp file permissions
- [ ] T055 Create README.md at repository root with:
  - Quick start instructions
  - Link to full documentation
  - API endpoint summary
- [ ] T056 Final executable build and test:
  - Clean build with build.bat
  - Full regression test with executable
  - Document executable version and date

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1)
- **Single Invoice Processing (Phase 3)**: Depends on Foundational (Phase 2)
- **Production Server (Phase 4)**: Depends on Single Invoice Processing (Phase 3)
- **Error Handling (Phase 5)**: Depends on Single Invoice Processing (Phase 3)
- **Testing (Phase 6)**: Depends on Error Handling (Phase 5)
- **Documentation (Phase 7)**: Depends on Production Server (Phase 4)
- **Performance (Phase 8)**: Depends on Testing (Phase 6)
- **Polish (Phase 9)**: Depends on all previous phases

### Critical Path

```
Setup → Foundational → Single Processing → Production Server → Testing → Performance → Polish
                              ↓
                       Error Handling → Testing
```

### Parallel Opportunities

**Phase 1 (Setup)**: T002-T009 can all run in parallel (different directories/files)

**Phase 2 (Foundational)**:
- T011, T012, T013, T016, T017 can run in parallel (different files)

**Phase 5 (Error Handling)**:
- T028-T034 can run in parallel (different error codes in same file, but separable)

**Phase 6 (Testing)**:
- T037-T041 can run in parallel (different test files)

**Phase 9 (Polish)**:
- T052, T053, T054 can run in parallel (different concerns)

### Within MVP (Phases 1-4)

**Sequential Dependencies**:
1. T001 (requirements) → T010 (Flask app needs dependencies)
2. T010 (Flask app) → T014 (health endpoint needs app)
3. T013 (DTOs) → T019 (service needs DTOs)
4. T018, T019 (services) → T020 (endpoint needs services)
5. T020 (endpoint) → T024 (production server needs endpoint)
6. T015 (spec file) → T025 (build needs spec)

**Parallelizable**:
- T002-T009 (all directory setup)
- T011, T012, T013 (different foundation files)
- T021, T022, T023 (enhancements to T020)

---

## Parallel Example: Foundation Phase

```bash
# Launch all foundation tasks that don't depend on each other:
Task: "Create global error handler registry in src/api/error_handlers.py"
Task: "Create request validation schemas in src/api/schemas.py"
Task: "Create DTOs in src/models/invoice_result.py"
Task: "Create Windows build script build.bat"
Task: "Update .gitignore to exclude build/, dist/"
```

---

## Implementation Strategy

### MVP First (Phases 1-4)

1. **Setup**: T001-T009 (project structure)
2. **Foundational**: T010-T017 (Flask app core)
3. **Core Feature**: T018-T023 (invoice processing endpoint)
4. **Production Ready**: T024-T027 (executable packaging)
5. **STOP and VALIDATE**: Test with real PDFs, verify Excel output
6. **Demo Ready**: Functional Windows executable that processes invoices

### Incremental Enhancement

1. **MVP** (Phases 1-4): Basic working API as executable
2. **Robust** (Phase 5): Add comprehensive error handling
3. **Tested** (Phase 6): Full test coverage
4. **Documented** (Phase 7): Validated user guide
5. **Optimized** (Phase 8): Performance tuning
6. **Polished** (Phase 9): Production-ready

### Recommended Stopping Points

- **After Phase 4**: Functional MVP - can process invoices via API
- **After Phase 6**: Tested and reliable
- **After Phase 9**: Production-ready release

---

## Notes

- **Existing Code**: Do NOT modify `src/extractors/`, `src/invoice_detectors/`, or `src/excel_writer.py` - they work as-is
- **Existing Logic**: Reuse `InvoiceProcessor` class from `src/process_invoices.py` in the API service layer
- **File Paths**: All paths are relative to repository root
- **Python Version**: Python 3.12 required (specified in plan.md)
- **Windows Only**: PyInstaller executable targets Windows 10+
- **Testing Strategy**: Unit tests for services, integration tests for endpoints, contract tests for API spec compliance
- **Build Command**: `build.bat` creates `dist/invoice-api.exe`
- **Run Command**: `python -m src.api.app` (development) or `dist/invoice-api.exe` (production)

---

## Task Summary

- **Total Tasks**: 56
- **Setup & Foundation**: 17 tasks (T001-T017)
- **Core Implementation**: 10 tasks (T018-T027)
- **Error Handling**: 9 tasks (T028-T036)
- **Testing**: 6 tasks (T037-T042)
- **Documentation**: 5 tasks (T043-T047)
- **Performance**: 4 tasks (T048-T051)
- **Polish**: 5 tasks (T052-T056)

**Parallel Tasks**: 23 tasks marked [P] can run in parallel with others
**MVP Scope**: T001-T027 (27 tasks) delivers working executable
**Full Feature**: All 56 tasks for production-ready release

