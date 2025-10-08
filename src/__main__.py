"""
Entry point for embedded Python runtime via serious_python.

This module is invoked by the Flutter app when processing invoices.
It reads configuration from environment variables and delegates to
the process_invoices module.
"""
import sys
import json
import os


def main():
    """Main entry point for embedded Python execution."""
    try:
        # Read inputs from environment variables
        output_path = os.environ.get('OUTPUT_PATH')
        pdf_files_json = os.environ.get('PDF_FILES')

        # Validate inputs
        if not output_path:
            error_result = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "failures": [],
                "error": "Missing OUTPUT_PATH environment variable"
            }
            print(json.dumps(error_result))
            sys.stdout.flush()
            sys.exit(1)

        if not pdf_files_json:
            error_result = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "failures": [],
                "error": "Missing PDF_FILES environment variable"
            }
            print(json.dumps(error_result))
            sys.stdout.flush()
            sys.exit(1)

        # Parse PDF files list
        try:
            pdf_files_data = json.loads(pdf_files_json)
        except json.JSONDecodeError as e:
            error_result = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "failures": [],
                "error": f"Invalid JSON in PDF_FILES: {str(e)}"
            }
            print(json.dumps(error_result))
            sys.stdout.flush()
            sys.exit(1)

        # Extract file paths from the data
        if isinstance(pdf_files_data, list):
            # List of file path strings or dicts with 'path' key
            pdf_paths = []
            for item in pdf_files_data:
                if isinstance(item, str):
                    pdf_paths.append(item)
                elif isinstance(item, dict) and 'path' in item:
                    pdf_paths.append(item['path'])
        else:
            error_result = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "failures": [],
                "error": "PDF_FILES must be a JSON array"
            }
            print(json.dumps(error_result))
            sys.stdout.flush()
            sys.exit(1)

        if not pdf_paths:
            error_result = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "failures": [],
                "error": "No PDF files provided"
            }
            print(json.dumps(error_result))
            sys.stdout.flush()
            sys.exit(1)

        # Import and run the invoice processor
        from process_invoices import main as process_main

        # Call the processor with CLI-style arguments
        sys.argv = ['process_invoices.py', output_path] + pdf_paths

        # Execute processing
        result_code = process_main()

        # Exit with the result code from processor
        sys.exit(result_code if result_code is not None else 0)

    except Exception as e:
        # Catch-all error handler
        error_result = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "failures": [],
            "error": f"Unexpected error: {str(e)}"
        }
        print(json.dumps(error_result))
        sys.stdout.flush()
        sys.exit(1)


if __name__ == '__main__':
    main()
