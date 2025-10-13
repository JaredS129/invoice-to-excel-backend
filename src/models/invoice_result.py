"""Data transfer objects for invoice processing results."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class FileProcessingDetail:
    """Details about a single file processing attempt."""

    filename: str
    invoice_type: str
    status: str  # 'success' or 'failed'
    records_extracted: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'filename': self.filename,
            'invoice_type': self.invoice_type,
            'status': self.status
        }
        if self.records_extracted is not None:
            result['records_extracted'] = self.records_extracted
        if self.error is not None:
            result['error'] = self.error
        return result


@dataclass
class FailureDetail:
    """Details about a failed invoice processing attempt."""

    filename: str
    invoice_type: str
    error: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ProcessingResult:
    """Result of processing a single invoice file."""

    success: bool
    filename: str
    invoice_type: str
    records: List[Dict[str, Any]]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class BatchProcessingResult:
    """Aggregated results from processing multiple invoices."""

    total: int
    successful: int
    failed: int
    failures: List[FailureDetail]
    files: List[FileProcessingDetail]
    output_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'total': self.total,
            'successful': self.successful,
            'failed': self.failed,
            'files': [f.to_dict() for f in self.files],
            'failures': [f.to_dict() for f in self.failures]
        }
        if self.output_path:
            result['output_path'] = self.output_path
        return result

    def to_summary_json(self) -> str:
        """
        Convert to JSON summary string for X-Processing-Summary header.

        Returns:
            JSON string with processing summary
        """
        import json
        return json.dumps(self.to_dict())
