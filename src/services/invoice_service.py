"""Invoice processing service wrapping existing extraction logic."""
from typing import List
from src.process_invoices import InvoiceProcessor
from src.excel_writer import ExcelWriter
from src.models.invoice_result import BatchProcessingResult, FailureDetail


class InvoiceService:
    """Service for processing invoice PDFs and generating Excel output."""

    def __init__(self):
        """Initialize invoice service with processor."""
        self.processor = InvoiceProcessor()

    def process_batch(self, pdf_paths: List[str], output_path: str) -> BatchProcessingResult:
        """
        Process a batch of invoice PDFs and generate Excel file.

        Args:
            pdf_paths: List of paths to PDF files
            output_path: Path where Excel file should be saved

        Returns:
            BatchProcessingResult with processing summary
        """
        all_records = []
        failures = []

        # Process each PDF
        for pdf_path in pdf_paths:
            # Extract filename for error reporting
            filename = pdf_path.split('/')[-1]

            try:
                # Process single invoice
                result = self.processor.process_invoice(pdf_path)

                if result['success']:
                    # Add records to aggregated list
                    all_records.extend(result['records'])
                else:
                    # Record failure
                    failures.append(FailureDetail(
                        filename=filename,
                        invoice_type=result.get('invoice_type', 'Unknown'),
                        error=result.get('error', 'Unknown error')
                    ))

            except Exception as e:
                # Catch any unexpected errors
                failures.append(FailureDetail(
                    filename=filename,
                    invoice_type='Unknown',
                    error=f'Unexpected error: {str(e)}'
                ))

        # Write Excel file if we have any records
        excel_path = None
        if all_records:
            try:
                ExcelWriter.write_invoices(all_records, output_path)
                excel_path = output_path
            except Exception as e:
                # If Excel generation fails, record it
                failures.append(FailureDetail(
                    filename='Excel Generation',
                    invoice_type='System',
                    error=f'Failed to generate Excel: {str(e)}'
                ))

        # Build result summary
        total = len(pdf_paths)
        failed = len(failures)
        successful = total - failed

        return BatchProcessingResult(
            total=total,
            successful=successful,
            failed=failed,
            failures=failures,
            output_path=excel_path
        )
