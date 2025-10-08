"""Extractor for DV360 invoices."""
import re
from typing import List, Dict, Any
import pdfplumber
from src.extractors.base_extractor import BaseExtractor


class DV360Extractor(BaseExtractor):
    """Extract data from DV360 PDF invoices."""

    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract invoice data from DV360 PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of invoice records with fields:
            - invoice_id
            - advertiser_id
            - description
            - unit
            - amount
            - invoice_type (DV360)
        """
        records = []
        invoice_id = ""
        advertiser_id = ""
        vat_rate = None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return records

                # First page: extract invoice ID and VAT rate
                first_page_text = pdf.pages[0].extract_text() or ""
                m = re.search(
                    r"Document number[:\s]*\s*(\d{9,10})",
                    first_page_text,
                    re.IGNORECASE,
                )
                if m:
                    invoice_id = m.group(1).strip()

                # Extract VAT rate (e.g., "VAT (8%)")
                vat_match = re.search(r"VAT\s*\((\d+(?:\.\d+)?)\s*%\)", first_page_text, re.IGNORECASE)
                if vat_match:
                    vat_rate = float(vat_match.group(1))

                # Process other pages: extract table data
                for page_index, page in enumerate(pdf.pages, start=1):
                    if page_index == 1:
                        continue  # skip first page

                    page_text = page.extract_text() or ""
                    if "Summary of costs by account budget" in page_text:
                        continue

                    # Extract Advertiser ID per page (note: "Advertiser Id" not "ID")
                    # Try multiple patterns to capture advertiser ID
                    page_advertiser_id = None

                    # Pattern 1: "Advertiser: <name> ID: 123456789"
                    m_adv = re.search(
                        r"Advertiser:[^I]*ID:\s*(\d{10,20})",
                        page_text,
                        re.IGNORECASE,
                    )
                    if m_adv:
                        page_advertiser_id = m_adv.group(1).strip()

                    # Pattern 2: "Advertiser Id: 123456789"
                    if not page_advertiser_id:
                        m2 = re.search(
                            r"Advertiser Id[:\s]*([\d\-]{10,20})",
                            page_text,
                            re.IGNORECASE,
                        )
                        if m2:
                            page_advertiser_id = m2.group(1).replace("-", "").strip()

                    # Use page-specific advertiser ID if found, otherwise keep previous
                    if page_advertiser_id:
                        advertiser_id = page_advertiser_id

                    # Extract table rows
                    page_records = self._extract_table_from_page(
                        page,
                        invoice_id,
                        advertiser_id,
                        vat_rate,
                    )
                    records.extend(page_records)

        except Exception as e:
            print(f"Error extracting DV360 data: {e}")

        return records

    def _extract_table_from_page(
        self,
        page: pdfplumber.page.Page,
        invoice_id: str,
        advertiser_id: str,
        vat_rate: float,
    ) -> List[Dict[str, Any]]:
        """Extract table rows from a single page."""
        records = []

        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            use_text_flow=True,
        )
        if not words:
            return records

        # Detect header words
        header_word = None
        quantity_word = None
        uom_word = None
        amount_word = None
        for w in words:
            t = w["text"].strip().lower()
            if t == "description":
                header_word = w
            elif t in ("quantity", "qty"):
                quantity_word = w
            elif t == "uom":
                uom_word = w
            elif "amount" in t:
                amount_word = w

        if not header_word or not amount_word:
            return records

        # Check if we have separate Quantity and UoM columns
        has_separate_uom = (quantity_word is not None and uom_word is not None)

        if has_separate_uom:
            quantity_x = quantity_word["x0"]
            uom_x = uom_word["x0"]
            amount_x = amount_word["x0"]
        else:
            # Fallback: look for generic "units" column
            units_word = None
            for w in words:
                t = w["text"].strip().lower()
                if t in ("units", "unit", "quantity", "qty"):
                    units_word = w
                    break

            if not units_word:
                return records

            units_x = units_word["x0"]
            amount_x = amount_word["x0"]

        # Find footer boundary
        footer_candidates = [
            w
            for w in words
            if w["text"].strip().lower().startswith("page")
            or "collections@google.com" in w["text"].lower()
        ]
        footer_top = min(
            (w["top"] for w in footer_candidates),
            default=page.height,
        ) - 2
        header_top = header_word["top"]

        # Extract table words
        table_words = [
            w for w in words if header_top + 2 < w["top"] < footer_top - 2
        ]
        lines = self.group_words_by_line(table_words, y_tol=3)

        last_good_desc = None
        for line in lines:
            line_sorted = sorted(line, key=lambda w: w["x0"])

            if has_separate_uom:
                # Parse with separate Quantity and UoM columns
                desc_parts, quantity_parts, uom_parts, amount_parts = [], [], [], []
                for w in line_sorted:
                    x, txt = w["x0"], w["text"].strip()
                    if x < quantity_x - 8:
                        desc_parts.append(txt)
                    elif quantity_x - 8 <= x < uom_x - 8:
                        quantity_parts.append(txt)
                    elif uom_x - 8 <= x < amount_x - 8:
                        uom_parts.append(txt)
                    else:
                        amount_parts.append(txt)

                description = " ".join(desc_parts).strip()
                quantity = " ".join(quantity_parts).strip()
                uom = " ".join(uom_parts).strip()
                amount = "".join(amount_parts).strip()

                # Track last good description even if no amount on this line
                if description:
                    last_good_desc = description

                # Use last good description for rows with amounts but no description
                if not description and last_good_desc:
                    description = last_good_desc

                amt_int = self.to_int_amount(amount)
                if amt_int is None or not description:
                    continue

                # If advertiser_id is empty, try to extract from description
                final_advertiser_id = advertiser_id
                if not final_advertiser_id:
                    # Pattern 1: "Advertiser: <name> ID: 123456789"
                    desc_match = re.search(r"Advertiser:[^I]*ID:\s*(\d{10,20})", description, re.IGNORECASE)
                    if desc_match:
                        final_advertiser_id = desc_match.group(1).strip()
                    else:
                        # Pattern 2: Look for ID in parentheses
                        desc_match2 = re.search(r"\((\d{10,20})\)", description)
                        if desc_match2:
                            final_advertiser_id = desc_match2.group(1).strip()

                records.append(
                    {
                        "invoice_id": invoice_id,
                        "advertiser_id": final_advertiser_id,
                        "description": description,
                        "quantity": quantity,
                        "uom": uom,
                        "amount": amt_int,
                        "invoice_type": "DV360",
                        "vat_rate": vat_rate,
                    }
                )
            else:
                # Fallback: parse with combined unit field
                desc_parts, unit_parts, amount_parts = [], [], []
                for w in line_sorted:
                    x, txt = w["x0"], w["text"].strip()
                    if x < units_x - 8:
                        desc_parts.append(txt)
                    elif units_x - 8 <= x < amount_x - 8:
                        unit_parts.append(txt)
                    else:
                        amount_parts.append(txt)

                description = " ".join(desc_parts).strip()
                unit = " ".join(unit_parts).strip()
                amount = "".join(amount_parts).strip()

                # Track last good description even if no amount on this line
                if description:
                    last_good_desc = description

                # Use last good description for rows with amounts but no description
                if not description and last_good_desc:
                    description = last_good_desc

                amt_int = self.to_int_amount(amount)
                if amt_int is None or not description:
                    continue

                # If advertiser_id is empty, try to extract from description
                final_advertiser_id = advertiser_id
                if not final_advertiser_id:
                    # Pattern 1: "Advertiser: <name> ID: 123456789"
                    desc_match = re.search(r"Advertiser:[^I]*ID:\s*(\d{10,20})", description, re.IGNORECASE)
                    if desc_match:
                        final_advertiser_id = desc_match.group(1).strip()
                    else:
                        # Pattern 2: Look for ID in parentheses
                        desc_match2 = re.search(r"\((\d{10,20})\)", description)
                        if desc_match2:
                            final_advertiser_id = desc_match2.group(1).strip()

                records.append(
                    {
                        "invoice_id": invoice_id,
                        "advertiser_id": final_advertiser_id,
                        "description": description,
                        "unit": unit,
                        "amount": amt_int,
                        "invoice_type": "DV360",
                        "vat_rate": vat_rate,
                    }
                )

        return records
