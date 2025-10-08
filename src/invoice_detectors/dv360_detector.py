"""Detector for DV360 invoices."""
import pdfplumber
import re


def detect_dv360(pdf_path: str) -> str:
    """
    Detect if PDF is a DV360 invoice.

    Args:
        pdf_path: Path to PDF file

    Returns:
        "DV360" if DV360 invoice
        "Unknown" if not

    Raises:
        FileNotFoundError: If PDF does not exist
        Exception: If PDF cannot be opened
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return "Unknown"

            # Extract text from first few pages
            combined_text = ""
            for page_num in range(min(3, len(pdf.pages))):
                page_text = pdf.pages[page_num].extract_text() or ""
                combined_text += page_text + "\n"

            # DV360 must have explicit "Display and Video 360" or "DV360" text
            # Note: CM360 also has "Advertiser Id", so we cannot use that alone
            if "Display and Video 360" in combined_text or "DV360" in combined_text:
                return "DV360"

            return "Unknown"

    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"Error detecting DV360: {e}")
        return "Unknown"
