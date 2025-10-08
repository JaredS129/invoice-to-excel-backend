import pytest
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractors.googleads_cm360_extractor import GoogleAdsCM360Extractor
from src.extractors.dv360_extractor import DV360Extractor
from src.extractors.google_vat_extractor import GoogleVATExtractor
from src.extractors.meta_extractor import MetaExtractor


# Path to example invoices
INVOICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../invoices'))


class TestGoogleAdsCM360Extractor:
    def test_extract_googleads_invoice(self):
        """Test extraction from GoogleAds invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleAds.pdf')
        extractor = GoogleAdsCM360Extractor()
        records = extractor.extract(pdf_path)

        assert len(records) > 0, 'Should extract at least one record'

        # Check first record has required fields
        record = records[0]
        assert 'invoice_type' in record
        assert 'invoice_id' in record
        assert 'advertiser_id' in record
        assert 'description' in record
        assert 'amount' in record

        # Validate data types
        assert isinstance(record['invoice_id'], str)
        assert isinstance(record['amount'], (int, float))

    def test_extract_cm360_invoice(self):
        """Test extraction from CM360 invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_CM360.pdf')
        extractor = GoogleAdsCM360Extractor()
        records = extractor.extract(pdf_path)

        assert len(records) > 0, 'Should extract at least one record'
        assert records[0]['invoice_id'] is not None


class TestDV360Extractor:
    def test_extract_dv360_invoice(self):
        """Test extraction from DV360 invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_DV360.pdf')
        extractor = DV360Extractor()
        records = extractor.extract(pdf_path)

        assert len(records) > 0, 'Should extract at least one record'

        record = records[0]
        assert 'invoice_id' in record
        assert 'advertiser_id' in record
        assert 'description' in record
        assert 'quantity' in record
        assert 'uom' in record
        assert 'amount' in record


class TestGoogleVATExtractor:
    def test_extract_google_vat_invoice(self):
        """Test extraction from Google VAT invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example_GoogleVAT.pdf')
        extractor = GoogleVATExtractor()
        records = extractor.extract(pdf_path)

        assert len(records) > 0, 'Should extract at least one record'

        record = records[0]
        assert 'invoice_id' in record, 'Should have invoice_id'
        assert 'amount' in record, 'Should have amount'
        assert isinstance(record['amount'], (int, float))


class TestMetaExtractor:
    def test_extract_meta_invoice(self):
        """Test extraction from Meta invoice"""
        pdf_path = os.path.join(INVOICES_DIR, 'Example Meta.pdf')
        extractor = MetaExtractor()
        records = extractor.extract(pdf_path)

        assert len(records) > 0, 'Should extract at least one record'

        record = records[0]
        assert 'invoice_id' in record
        assert 'description' in record
        assert 'amount' in record
        assert 'currency' in record

        # Currency should be present for Meta invoices
        assert record['currency'] is not None


class TestExtractorErrorHandling:
    def test_extractor_handles_nonexistent_file(self):
        """Test that extractor handles non-existent files gracefully"""
        extractor = GoogleAdsCM360Extractor()

        with pytest.raises(Exception):
            extractor.extract('/nonexistent/file.pdf')

    def test_extractor_handles_corrupted_pdf(self):
        """Test that extractor handles corrupted PDFs gracefully"""
        # This would require a corrupted PDF file
        pass
