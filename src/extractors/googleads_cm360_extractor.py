"""Extractor for GoogleAds and CM360 invoices."""
import re
from typing import List, Dict, Any
import pdfplumber
from src.extractors.base_extractor import BaseExtractor


class GoogleAdsCM360Extractor(BaseExtractor):
    """Extract data from GoogleAds and CM360 PDF invoices."""

    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract invoice data from GoogleAds/CM360 PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of invoice records with fields:
            - invoice_id
            - advertiser_id
            - description
            - unit
            - amount
            - invoice_type (GoogleAds or CM360)
        """
        records = []
        invoice_id = ""
        advertiser_id = ""
        vat_rate = None

        try:
            # Check if file exists
            import os
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

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

                # Determine invoice type
                invoice_type = self._determine_type(pdf)

                # Process other pages: extract table data
                for page_index, page in enumerate(pdf.pages, start=1):
                    if page_index == 1:
                        continue  # skip first page

                    page_text = page.extract_text() or ""
                    if "Summary of costs by account budget" in page_text:
                        continue

                    # Extract Advertiser ID per page
                    m2 = re.search(
                        r"Account ID[:\s]*([\d\-]{7,20})",
                        page_text,
                        re.IGNORECASE,
                    )
                    if m2:
                        advertiser_id = m2.group(1).replace("-", "").strip()

                    # Extract table rows
                    page_records = self._extract_table_from_page(
                        page,
                        invoice_id,
                        advertiser_id,
                        invoice_type,
                        vat_rate,
                    )
                    records.extend(page_records)

        except FileNotFoundError:
            raise
        except Exception as e:
            print(f"Error extracting GoogleAds/CM360 data: {e}")

        return records

    def _determine_type(self, pdf: pdfplumber.PDF) -> str:
        """Determine if invoice is GoogleAds or CM360."""
        combined_text = ""
        for page_num in range(min(3, len(pdf.pages))):
            page_text = pdf.pages[page_num].extract_text() or ""
            combined_text += page_text + "\n"

        if "Google Ads" in combined_text or "GoogleAds" in combined_text:
            return "GoogleAds"
        elif "CM360" in combined_text or "Campaign Manager" in combined_text:
            return "CM360"
        elif re.search(r"Account ID[:\s]", combined_text, re.IGNORECASE):
            return "CM360"
        return "Unknown"

    def _extract_table_from_page(
        self,
        page: pdfplumber.page.Page,
        invoice_id: str,
        advertiser_id: str,
        invoice_type: str,
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
        uom_word = None
        unit_word = None
        price_word = None
        quantity_word = None
        amount_word = None
        for w in words:
            t = w["text"].strip().lower()
            if t == "description":
                header_word = w
            elif t == "uom":
                uom_word = w
            elif t == "unit":
                # Check if next word is "Price" to distinguish from generic "unit"
                unit_word = w
            elif t == "price":
                price_word = w
            elif t in ("quantity", "qty"):
                quantity_word = w
            elif "amount" in t:
                amount_word = w

        # Check if this is CM360 invoice with detailed columns (has UoM, Unit, Price, Quantity)
        is_cm360_detailed = (invoice_type == "CM360" and uom_word and unit_word and price_word and quantity_word)

        if not header_word or not amount_word:
            return records

        # For CM360 with detailed columns, use all column positions
        if is_cm360_detailed:
            uom_x = uom_word["x0"]
            unit_price_x = unit_word["x0"]  # "Unit" header position
            quantity_x = quantity_word["x0"]
            amount_x = amount_word["x0"]
        else:
            # For GoogleAds, check if we have separate Quantity and Units columns
            quantity_word_ga = None
            units_word_ga = None
            for w in words:
                t = w["text"].strip().lower()
                if t in ("quantity", "qty"):
                    quantity_word_ga = w
                elif t in ("units", "unit"):
                    units_word_ga = w

            # Check if this is GoogleAds with separate Quantity and Units columns
            has_separate_units = (quantity_word_ga is not None and units_word_ga is not None)

            if has_separate_units:
                quantity_x = quantity_word_ga["x0"]
                units_x = units_word_ga["x0"]
                amount_x = amount_word["x0"]
            else:
                # Fallback: look for generic units column
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

            if is_cm360_detailed:
                # Parse CM360 with UoM, Unit Price, Quantity columns
                desc_parts, uom_parts, unit_price_parts, quantity_parts, amount_parts = [], [], [], [], []
                for w in line_sorted:
                    x, txt = w["x0"], w["text"].strip()
                    if x < uom_x - 8:
                        desc_parts.append(txt)
                    elif uom_x - 8 <= x < unit_price_x - 8:
                        uom_parts.append(txt)
                    elif unit_price_x - 8 <= x < quantity_x - 8:
                        unit_price_parts.append(txt)
                    elif quantity_x - 8 <= x < amount_x - 8:
                        quantity_parts.append(txt)
                    else:
                        amount_parts.append(txt)

                description = " ".join(desc_parts).strip()
                uom = " ".join(uom_parts).strip()
                unit_price = " ".join(unit_price_parts).strip()
                quantity = " ".join(quantity_parts).strip()
                amount = "".join(amount_parts).strip()

                if not description and last_good_desc:
                    description = last_good_desc

                amt_int = self.to_int_amount(amount)
                if amt_int is None or not description:
                    continue

                last_good_desc = description
                records.append(
                    {
                        "invoice_id": invoice_id,
                        "advertiser_id": advertiser_id,
                        "description": description,
                        "uom": uom,
                        "unit_price": unit_price,
                        "quantity": quantity,
                        "amount": amt_int,
                        "invoice_type": invoice_type,
                        "vat_rate": vat_rate,
                    }
                )
            else:
                # Parse GoogleAds or simple format
                if has_separate_units:
                    # GoogleAds with separate Quantity and Units columns
                    desc_parts, quantity_parts, uom_parts, amount_parts = [], [], [], []
                    for w in line_sorted:
                        x, txt = w["x0"], w["text"].strip()
                        if x < quantity_x - 8:
                            desc_parts.append(txt)
                        elif quantity_x - 8 <= x < units_x - 8:
                            quantity_parts.append(txt)
                        elif units_x - 8 <= x < amount_x - 8:
                            uom_parts.append(txt)
                        else:
                            amount_parts.append(txt)

                    description = " ".join(desc_parts).strip()
                    quantity = " ".join(quantity_parts).strip()
                    uom = " ".join(uom_parts).strip()
                    amount = "".join(amount_parts).strip()

                    # Track last good description even if no amount on this line
                    if description:
                        cleaned = description.replace(',', '').replace('.', '').replace(' ', '')
                        if not cleaned.isdigit():
                            last_good_desc = description

                    # Use last good description for rows with amounts but no proper description
                    if not description and last_good_desc:
                        description = last_good_desc
                    elif description:
                        cleaned = description.replace(',', '').replace('.', '').replace(' ', '')
                        if cleaned.isdigit() and last_good_desc:
                            description = last_good_desc

                    amt_int = self.to_int_amount(amount)
                    if amt_int is None or not description:
                        continue

                    records.append(
                        {
                            "invoice_id": invoice_id,
                            "advertiser_id": advertiser_id,
                            "description": description,
                            "quantity": quantity,
                            "uom": uom,
                            "amount": amt_int,
                            "invoice_type": invoice_type,
                            "vat_rate": vat_rate,
                        }
                    )
                else:
                    # Simple format with combined unit field
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
                        cleaned = description.replace(',', '').replace('.', '').replace(' ', '')
                        if not cleaned.isdigit():
                            last_good_desc = description

                    # Use last good description for rows with amounts but no proper description
                    if not description and last_good_desc:
                        description = last_good_desc
                    elif description:
                        cleaned = description.replace(',', '').replace('.', '').replace(' ', '')
                        if cleaned.isdigit() and last_good_desc:
                            description = last_good_desc

                    amt_int = self.to_int_amount(amount)
                    if amt_int is None or not description:
                        continue

                    records.append(
                        {
                            "invoice_id": invoice_id,
                            "advertiser_id": advertiser_id,
                            "description": description,
                            "unit": unit,
                            "amount": amt_int,
                            "invoice_type": invoice_type,
                            "vat_rate": vat_rate,
                        }
                    )

        return records
