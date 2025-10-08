"""Unified entry point for invoice processing."""
import sys
import json
from typing import List, Dict, Any
from pathlib import Path

from src.invoice_detectors.googleads_cm360_detector import detect_googleads_cm360
from src.invoice_detectors.dv360_detector import detect_dv360
from src.invoice_detectors.google_vat_detector import detect_google_vat
from src.invoice_detectors.meta_detector import detect_meta
from src.extractors.googleads_cm360_extractor import GoogleAdsCM360Extractor
from src.extractors.dv360_extractor import DV360Extractor
from src.extractors.google_vat_extractor import GoogleVATExtractor
from src.extractors.meta_extractor import MetaExtractor
from src.excel_writer import ExcelWriter


class InvoiceProcessor:
    """Process invoices with automatic type detection and extraction."""

    def __init__(self):
        """Initialize processor with extractors."""
        self.extractors = {
            "GoogleAds": GoogleAdsCM360Extractor(),
            "CM360": GoogleAdsCM360Extractor(),
            "DV360": DV360Extractor(),
            "GoogleVAT": GoogleVATExtractor(),
            "Meta": MetaExtractor(),
        }

    def detect_invoice_type(self, pdf_path: str) -> str:
        """
        Detect invoice type from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Invoice type (GoogleAds, CM360, DV360, GoogleVAT, Meta, or Unknown)
        """
        # Try each detector in order of specificity
        # Check Meta first since it has unique patterns and can conflict with CM360
        invoice_type = detect_meta(pdf_path)
        if invoice_type != "Unknown":
            return invoice_type

        invoice_type = detect_google_vat(pdf_path)
        if invoice_type != "Unknown":
            return invoice_type

        invoice_type = detect_dv360(pdf_path)
        if invoice_type != "Unknown":
            return invoice_type

        # GoogleAds/CM360 has broader patterns, check last
        invoice_type = detect_googleads_cm360(pdf_path)
        if invoice_type != "Unknown":
            return invoice_type

        return "Unknown"

    def process_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a single invoice.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Result dictionary with:
            - success: bool
            - invoice_type: str
            - records: List[Dict] (if successful)
            - error: str (if failed)
        """
        try:
            # Detect type
            invoice_type = self.detect_invoice_type(pdf_path)
            if invoice_type == "Unknown":
                return {
                    "success": False,
                    "invoice_type": "Unknown",
                    "error": "Could not detect invoice type",
                }

            # Extract data
            extractor = self.extractors.get(invoice_type)
            if not extractor:
                return {
                    "success": False,
                    "invoice_type": invoice_type,
                    "error": f"No extractor available for {invoice_type}",
                }

            records = extractor.extract(pdf_path)
            return {
                "success": True,
                "invoice_type": invoice_type,
                "records": records,
            }

        except Exception as e:
            return {
                "success": False,
                "invoice_type": "Unknown",
                "error": str(e),
            }

    def process_batch(
        self,
        pdf_paths: List[str],
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Process batch of invoices and write to Excel.

        Args:
            pdf_paths: List of PDF file paths
            output_path: Output Excel file path

        Returns:
            Summary dictionary with:
            - total: int (total files)
            - successful: int
            - failed: int
            - failures: List[Dict] (failed files with reasons)
        """
        all_records = []
        failures = []

        for pdf_path in pdf_paths:
            result = self.process_invoice(pdf_path)
            if result["success"]:
                all_records.extend(result["records"])
            else:
                failures.append(
                    {
                        "file": pdf_path,
                        "invoice_type": result["invoice_type"],
                        "error": result["error"],
                    }
                )

        # Write to Excel if we have records
        if all_records:
            ExcelWriter.write_invoices(all_records, output_path)

        return {
            "total": len(pdf_paths),
            "successful": len(pdf_paths) - len(failures),
            "failed": len(failures),
            "failures": failures,
            "output_path": output_path if all_records else None,
        }


def main():
    """
    CLI entry point.

    Expected arguments:
        python process_invoices.py <output_path> <pdf_path1> <pdf_path2> ...
    """
    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Usage: process_invoices.py <output_path> <pdf_path1> ...",
                }
            )
        )
        sys.stdout.flush()
        sys.exit(1)

    output_path = sys.argv[1]
    pdf_paths = sys.argv[2:]

    # Validate PDF paths
    for pdf_path in pdf_paths:
        if not Path(pdf_path).exists():
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": f"PDF file not found: {pdf_path}",
                    }
                )
            )
            sys.stdout.flush()
            sys.exit(1)

    # Process batch
    processor = InvoiceProcessor()
    result = processor.process_batch(pdf_paths, output_path)

    # Output JSON result
    print(json.dumps(result))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
