"""Detector for Google VAT invoices."""
import pdfplumber
import re


def detect_google_vat(pdf_path: str) -> str:
    """
    Detect if PDF is a Google VAT invoice.

    Args:
        pdf_path: Path to PDF file

    Returns:
        "GoogleVAT" if Google VAT invoice
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

            # Check for Vietnamese text patterns specific to Google VAT invoices
            has_vat_number = re.search(r"Số\s*\(No\.\):", first_page_text)
            has_vat_amount = "Tiền hàng chưa thuế" in first_page_text or "Tien hang chua thue" in first_page_text

            if has_vat_number or has_vat_amount:
                return "GoogleVAT"

            return "Unknown"

    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"Error detecting Google VAT: {e}")
        return "Unknown"
