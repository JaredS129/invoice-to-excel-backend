"""Base extractor class for all invoice extractors."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseExtractor(ABC):
    """Abstract base class for invoice data extractors."""

    @abstractmethod
    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract invoice data from a PDF file.

        Args:
            pdf_path: Absolute path to PDF file

        Returns:
            List of InvoiceRecord dictionaries with keys:
                - invoice_type: str
                - invoice_id: str
                - advertiser_id: Optional[str]
                - description: Optional[str]
                - unit: Optional[str]
                - amount: Union[int, float]
                - currency: Optional[str]

        Raises:
            FileNotFoundError: If PDF does not exist
            Exception: If PDF cannot be opened or processed
        """
        pass

    @staticmethod
    def to_int_amount(amount_str: Optional[str]) -> Optional[int]:
        """
        Convert amount string like '69,400,711' or '-652' to int.

        Args:
            amount_str: String representation of amount

        Returns:
            Integer amount or None if conversion fails
        """
        if not amount_str:
            return None

        s = amount_str.strip().replace(",", "").replace(" ", "")
        s = s.replace("(", "-").replace(")", "")

        if s in ("", "-", "--"):
            return None

        try:
            return int(s)
        except Exception:
            return None

    @staticmethod
    def group_words_by_line(words: List[Dict[str, Any]], y_tol: int = 3) -> List[List[Dict[str, Any]]]:
        """
        Group a list of word dicts by their top coordinate (line grouping).

        Args:
            words: List of word dictionaries from pdfplumber
            y_tol: Y-axis tolerance for grouping words on same line

        Returns:
            List of lines, where each line is a list of word dicts
        """
        if not words:
            return []

        words_sorted = sorted(words, key=lambda w: (w["top"], w["x0"]))
        lines = []
        current_line = [words_sorted[0]]
        current_top = words_sorted[0]["top"]

        for w in words_sorted[1:]:
            if abs(w["top"] - current_top) <= y_tol:
                current_line.append(w)
            else:
                lines.append(current_line)
                current_line = [w]
                current_top = w["top"]

        if current_line:
            lines.append(current_line)

        return lines
