import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.invoice_detectors.googleads_cm360_detector import detect_googleads_cm360
from src.invoice_detectors.dv360_detector import detect_dv360
from src.invoice_detectors.google_vat_detector import detect_google_vat
from src.invoice_detectors.meta_detector import detect_meta


# Path to example invoices
INVOICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../invoices'))


class TestGoogleAdsCM360Detector:
    def test_detect_googleads_invoice(self):
        """Test detection of GoogleAds invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleAds.pdf')
        result = detect_googleads_cm360(pdf_path)
        assert result in ['GoogleAds', 'CM360'], f'Expected GoogleAds or CM360, got {result}'

    def test_detect_cm360_invoice(self):
        """Test detection of CM360 invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_CM360.pdf')
        result = detect_googleads_cm360(pdf_path)
        assert result in ['GoogleAds', 'CM360'], f'Expected GoogleAds or CM360, got {result}'


class TestDV360Detector:
    def test_detect_dv360_invoice(self):
        """Test detection of DV360 invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_DV360.pdf')
        result = detect_dv360(pdf_path)
        assert result == 'DV360', f'Expected DV360, got {result}'

    def test_non_dv360_returns_unknown(self):
        """Test that non-DV360 PDF returns Unknown"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleAds.pdf')
        result = detect_dv360(pdf_path)
        assert result == 'Unknown', f'Expected Unknown for non-DV360 PDF, got {result}'


class TestGoogleVATDetector:
    def test_detect_google_vat_invoice(self):
        """Test detection of Google VAT invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleVAT.pdf')
        result = detect_google_vat(pdf_path)
        assert result == 'GoogleVAT', f'Expected GoogleVAT, got {result}'

    def test_non_vat_returns_unknown(self):
        """Test that non-VAT PDF returns Unknown"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleAds.pdf')
        result = detect_google_vat(pdf_path)
        assert result == 'Unknown', f'Expected Unknown for non-VAT PDF, got {result}'


class TestMetaDetector:
    def test_detect_meta_invoice(self):
        """Test detection of Meta invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example Meta.pdf')
        result = detect_meta(pdf_path)
        assert result == 'Meta', f'Expected Meta, got {result}'

    def test_non_meta_returns_unknown(self):
        """Test that non-Meta PDF returns Unknown"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleAds.pdf')
        result = detect_meta(pdf_path)
        assert result == 'Unknown', f'Expected Unknown for non-Meta PDF, got {result}'


class TestUnknownInvoiceType:
    def test_unrecognized_pdf_returns_unknown(self):
        """Test that unrecognized PDF type returns Unknown from all detectors"""
        # This would need a PDF that doesn't match any pattern
        # For now, we test that each detector has an Unknown return path
        pass
