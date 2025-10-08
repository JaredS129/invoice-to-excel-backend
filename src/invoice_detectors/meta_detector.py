"""Detector for Meta invoices."""
import pdfplumber
import re


def detect_meta(pdf_path: str) -> str:
    """
    Detect if PDF is a Meta invoice.

    Args:
        pdf_path: Path to PDF file

    Returns:
        "Meta" if Meta invoice
        "Unknown" if not

    Raises:
        FileNotFoundError: If PDF does not exist
        Exception: If PDF cannot be opened
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return "Unknown"

            # Extract first page text
            first_page_text = pdf.pages[0].extract_text() or ""

            # Check for "Invoice #:" AND "Meta" in text
            has_invoice_number = re.search(r"Invoice\s*#:", first_page_text, re.IGNORECASE)
            has_meta = "Meta" in first_page_text or "Facebook" in first_page_text

            if has_invoice_number and has_meta:
                return "Meta"

            return "Unknown"

    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"Error detecting Meta: {e}")
        return "Unknown"
