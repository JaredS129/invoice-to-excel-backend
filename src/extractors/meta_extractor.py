"""Extractor for Meta invoices."""
import re
from typing import List, Dict, Any
import pdfplumber
from src.extractors.base_extractor import BaseExtractor


class MetaExtractor(BaseExtractor):
    """Extract data from Meta PDF invoices."""

    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract invoice data from Meta PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of invoice line item records, each containing:
            - invoice_id
            - account_id
            - description
            - amount
            - currency
            - invoice_type (Meta)
        """
        invoice_number = None
        account_id = None
        currency = None
        vat_rate = None
        records = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

                # Extract invoice-level fields
                invoice_match = re.search(r"Invoice\s*#:\s*(\d+)", text)
                if invoice_match:
                    invoice_number = invoice_match.group(1).strip()

                account_match = re.search(
                    r"Account Id\s*/\s*Group:\s*(\d+)",
                    text,
                )
                if account_match:
                    account_id = account_match.group(1).strip()

                currency_match = re.search(r"Currency:\s*([A-Z]+)", text)
                if currency_match:
                    currency = currency_match.group(1).strip()

                # Extract VAT rate (e.g., "VAT @0%:")
                vat_match = re.search(r"VAT\s*@\s*(\d+(?:\.\d+)?)\s*%", text, re.IGNORECASE)
                if vat_match:
                    vat_rate = float(vat_match.group(1))

                # Extract table rows for line items
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or not table[0]:
                            continue

                        # Check if this is the line items table
                        headers = [h.strip() if h else "" for h in table[0]]
                        has_description = any("Description" in h for h in headers)
                        has_total = any("Total" in h for h in headers)

                        if not (has_description and has_total):
                            continue

                        # Find column indices
                        desc_idx = None
                        total_idx = None
                        for idx, h in enumerate(headers):
                            if "Description" in h:
                                desc_idx = idx
                            elif "Total" in h:
                                total_idx = idx

                        if desc_idx is None or total_idx is None:
                            continue

                        # Extract line items
                        for row in table[1:]:
                            if not row or len(row) <= max(desc_idx, total_idx):
                                continue

                            description = row[desc_idx]
                            amount_str = row[total_idx]

                            if not description or not amount_str:
                                continue

                            # Clean description (remove newlines)
                            description = description.strip().replace("\n", " ")

                            # Parse amount
                            amount_str = amount_str.strip().replace(",", "")
                            try:
                                if currency == "USD":
                                    amount = float(amount_str)
                                else:
                                    # VND or other integer-based currencies
                                    if "." in amount_str:
                                        amount = float(amount_str)
                                    else:
                                        amount = int(amount_str)
                            except ValueError:
                                continue

                            # Add record
                            records.append({
                                "invoice_id": invoice_number,
                                "account_id": account_id,
                                "description": description,
                                "amount": amount,
                                "currency": currency or "",
                                "invoice_type": "Meta",
                                "vat_rate": vat_rate,
                            })

        except Exception as e:
            print(f"Error extracting Meta data: {e}")

        return records
