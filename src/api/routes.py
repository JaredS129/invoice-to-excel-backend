"""API routes for invoice processing."""
import os
import tempfile
import logging
from flask import Blueprint, request, jsonify, send_file
from src.services.file_service import FileService
from src.services.invoice_service import InvoiceService
from src.api.error_handlers import APIError

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with API health status
    """
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    }), 200


@api_bp.route('/process', methods=['POST'])
def process_invoices():
    """
    Process batch of invoice PDFs and return Excel file.

    Accepts:
        multipart/form-data with 'invoices' field containing PDF files

    Returns:
        Excel file (.xlsx) with extracted invoice data
        X-Processing-Summary header with JSON processing summary

    Raises:
        APIError: For validation failures or processing errors
    """
    logger.info('Received invoice processing request')

    # Get uploaded files
    files = request.files.getlist('invoices')

    if not files:
        logger.error('No files provided in request')
        raise APIError(
            'No PDF files were provided in the request',
            status_code=400,
            error_code='NO_FILES_PROVIDED'
        )

    logger.info(f'Processing {len(files)} files')

    # Validate files
    is_valid, error_msg, error_code = FileService.validate_pdf_files(files)
    if not is_valid:
        logger.error(f'File validation failed: {error_msg}')
        raise APIError(error_msg, status_code=400, error_code=error_code)

    # Use temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Save uploaded files
            logger.info(f'Saving files to temporary directory: {temp_dir}')
            pdf_paths = FileService.save_uploaded_files(files, temp_dir)

            # Define output path for Excel file
            output_excel = os.path.join(temp_dir, 'invoices_output.xlsx')

            # Process invoices
            logger.info('Starting invoice processing')
            invoice_service = InvoiceService()
            result = invoice_service.process_batch(pdf_paths, output_excel)

            logger.info(f'Processing complete: {result.successful}/{result.total} successful')

            # Check if any files were processed successfully
            if result.successful == 0:
                logger.error('All files failed to process')
                raise APIError(
                    f'All {result.total} files failed to process',
                    status_code=400,
                    error_code='ALL_FILES_FAILED'
                )

            # Read Excel file into memory before temp dir cleanup
            # This prevents Windows file locking issues
            with open(output_excel, 'rb') as f:
                excel_data = f.read()

        except APIError:
            # Re-raise API errors
            raise
        except Exception as e:
            logger.error(f'Unexpected error during processing: {str(e)}', exc_info=True)
            raise APIError(
                'An unexpected error occurred during processing',
                status_code=500,
                error_code='INTERNAL_ERROR'
            )

    # Send file from memory (after temp dir is cleaned up)
    from io import BytesIO
    response = send_file(
        BytesIO(excel_data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='invoices_output.xlsx'
    )

    # Add processing summary header
    response.headers['X-Processing-Summary'] = result.to_summary_json()

    logger.info('Successfully sent Excel response')
    return response
