# Implementation Plan: Flask API for Invoice Processing

**Branch**: `001-invoice-to-excel` | **Date**: 2025-10-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-invoice-to-excel/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a Flask REST API that wraps the existing invoice processing logic in `/src`, exposing a single endpoint that accepts batches of PDF invoices (supporting 5 types: DV360, GoogleAds, CM360, GoogleVAT, Meta), and returns the generated Excel file. The API must be packaged as a portable Windows executable using PyInstaller so it can run on Windows machines without Python installed.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Flask 3.x, PyInstaller 6.x, pdfplumber 0.10+, openpyxl 3.1+
**Storage**: Temporary file system storage for uploaded PDFs and generated Excel files
**Testing**: pytest 7.4+ for unit and integration tests
**Target Platform**: Windows 10+ (portable executable via PyInstaller)
**Project Type**: Web API (single project structure with Flask backend)
**Performance Goals**: Process batches of 100 invoices within 5 minutes (30 seconds per invoice average)
**Constraints**:
- Executable must be self-contained (no Python installation required)
- Memory usage should remain under 500MB for typical batches
- Must handle file uploads up to 100MB total size
- Response timeout set to 5 minutes for batch processing
**Scale/Scope**:
- Support concurrent processing of up to 5 batch requests
- Handle batches of 1-100 invoices per request
- Single endpoint API (focused scope)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ PASSED (Constitution template not customized - default pass)

The constitution file contains only template placeholders, so there are no specific project principles to violate. Standard engineering practices will be followed:
- Clear API contract definition
- Comprehensive testing strategy
- Simple, maintainable code structure
- Proper error handling and logging

## Project Structure

### Documentation (this feature)

```
specs/001-invoice-to-excel/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api-spec.yaml    # OpenAPI 3.0 specification
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── api/
│   ├── __init__.py
│   ├── app.py           # Flask application factory
│   ├── routes.py        # API endpoint definitions
│   ├── schemas.py       # Request/response validation schemas
│   └── error_handlers.py # Global error handling
├── models/
│   ├── __init__.py
│   └── invoice_result.py # Data transfer objects
├── services/
│   ├── __init__.py
│   ├── invoice_service.py # Orchestrates processing using existing extractors
│   └── file_service.py    # Handles file uploads and temp storage
├── extractors/          # [EXISTING CODE - minimal adjustments]
│   ├── __init__.py
│   ├── base_extractor.py
│   ├── dv360_extractor.py
│   ├── googleads_cm360_extractor.py
│   ├── google_vat_extractor.py
│   └── meta_extractor.py
├── invoice_detectors/   # [EXISTING CODE - no changes]
│   ├── __init__.py
│   ├── dv360_detector.py
│   ├── googleads_cm360_detector.py
│   ├── google_vat_detector.py
│   └── meta_detector.py
├── excel_writer.py      # [EXISTING CODE - no changes]
├── process_invoices.py  # [EXISTING CODE - may be deprecated or kept for CLI]
├── __main__.py          # [EXISTING CODE - may be deprecated]
├── __init__.py
└── requirements.txt     # Updated with Flask, PyInstaller

tests/
├── contract/
│   ├── __init__.py
│   └── test_api_contract.py # Test API spec compliance
├── integration/
│   ├── __init__.py
│   ├── test_api_endpoints.py # Full request/response tests
│   └── test_invoice_processing.py # End-to-end processing tests
└── unit/
    ├── __init__.py
    ├── test_invoice_service.py
    └── test_file_service.py

build/                   # PyInstaller build artifacts (gitignored)
dist/                    # Final executable output (gitignored)
invoice-api.spec        # PyInstaller configuration file
build.bat               # Windows batch script for single-command build
```

**Structure Decision**: Single project structure selected because this is a focused Flask API wrapping existing processing logic. The API layer (`api/`), service layer (`services/`), and existing extraction logic are all part of one cohesive application. No separate frontend or mobile components are needed.

## Complexity Tracking

*No Constitution violations to track - constitution file uses template defaults*

