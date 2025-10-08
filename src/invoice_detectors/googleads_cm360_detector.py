"""Detector for GoogleAds and CM360 invoices."""
import pdfplumber
import re


def detect_googleads_cm360(pdf_path: str) -> str:
    """
    Detect if PDF is a GoogleAds or CM360 invoice.

    Args:
        pdf_path: Path to PDF file

    Returns:
        "GoogleAds" if Google Ads invoice
        "CM360" if CM360 invoice
        "Unknown" if neither

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

            # Check for GoogleAds indicators
            if "Google Ads" in combined_text or "GoogleAds" in combined_text:
                return "GoogleAds"

            # Check for CM360 indicators
            if "CM360" in combined_text or "Campaign Manager" in combined_text:
                return "CM360"

            # Check if it has Account ID pattern (common pattern)
            # If it has Account ID but no explicit marker, might be CM360
            if re.search(r"Account ID[:\s]", combined_text, re.IGNORECASE):
                return "CM360"

            return "Unknown"

    except FileNotFoundError:
        raise
    except Exception as e:
        # Log error but return Unknown instead of crashing
        print(f"Error detecting GoogleAds/CM360: {e}")
        return "Unknown"
