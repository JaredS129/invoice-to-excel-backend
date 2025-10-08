"""Extractor for Google VAT invoices."""
import re
from typing import List, Dict, Any
import pdfplumber
from src.extractors.base_extractor import BaseExtractor


class GoogleVATExtractor(BaseExtractor):
    """Extract data from Google VAT PDF invoices."""

    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract invoice data from Google VAT PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List with single invoice record containing:
            - invoice_id (Số Invoice VAT)
            - invoice_ref (Số Invoice tham chiếu Google System)
            - uom (Đơn vị tính - Unit)
            - quantity (Số lượng - Quantity)
            - amount (Số tiền)
            - invoice_type (GoogleVAT)
        """
        invoice_vat = None
        invoice_ref = None
        amount = None
        vat_rate = None
        uom = None
        quantity = None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                # Extract "Số Invoice VAT"
                vat_match = re.search(r"Số\s*\(No.\):\s*(\d+)", text)
                if vat_match:
                    invoice_vat = vat_match.group(1)

                # Extract "Số Invoice tham chiếu Google System"
                ref_match = re.search(
                    r"\(Reference No/Search code\):\s*(\d+)",
                    text,
                )
                if ref_match:
                    invoice_ref = ref_match.group(1)

                # Extract "Số tiền"
                amount_match = re.search(r"Tiền hàng chưa thuế\s+([\d\.]+)", text)
                if amount_match:
                    amount_str = amount_match.group(1).replace(".", "")
                    amount = int(amount_str)

                # Extract VAT rate from table (typically 8%)
                # Look for pattern like "110.297 8% 8.824" in table
                vat_rate_match = re.search(r"[\d\.,]+\s+(\d+)%\s+[\d\.,]+", text)
                if vat_rate_match:
                    vat_rate = float(vat_rate_match.group(1))

                # Extract Unit (Đơn vị tính) and Quantity (Số lượng) from table
                # Pattern: Row number followed by UoM and Quantity
                # Example: "1 Dịch vụ 1 110.297 110.297 8% 8.824 119.121"
                # The pattern is: [row_number] [UoM] [Quantity] [amounts...]
                table_match = re.search(
                    r"^\d+\s+([^\d\s]+(?:\s+[^\d\s]+)*?)\s+(\d+)\s+[\d\.]+\s+[\d\.]+\s+\d+%",
                    text,
                    re.MULTILINE
                )
                if table_match:
                    uom = table_match.group(1).strip()
                    quantity = table_match.group(2).strip()

        except Exception as e:
            print(f"Error extracting Google VAT data: {e}")

        # Return single record if all fields extracted
        if invoice_vat and invoice_ref and amount is not None:
            return [
                {
                    "invoice_id": invoice_vat,
                    "invoice_ref": invoice_ref,
                    "uom": uom or "",
                    "quantity": quantity or "",
                    "amount": amount,
                    "invoice_type": "GoogleVAT",
                    "vat_rate": vat_rate,
                }
            ]

        return []
