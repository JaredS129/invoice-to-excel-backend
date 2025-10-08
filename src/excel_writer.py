"""Excel writer for invoice data."""
from typing import List, Dict, Any
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo


class ExcelWriter:
    """Write invoice records to Excel file."""

    @staticmethod
    def write_invoices(records: List[Dict[str, Any]], output_path: str) -> None:
        """
        Write invoice records to Excel file with separate sheets per invoice type.

        Args:
            records: List of invoice records from various extractors
            output_path: Path to output Excel file

        Note:
            Creates separate worksheets for each invoice type:
            - GoogleAds sheet
            - CM360 sheet
            - DV360 sheet
            - GoogleVAT sheet
            - Meta sheet

            Each sheet has:
            - Type-specific columns
            - Data rows
            - Total row at bottom with sum of amounts
        """
        if not records:
            return

        # Group records by invoice type
        grouped_records = defaultdict(list)
        for record in records:
            invoice_type = record.get("invoice_type", "Unknown")
            grouped_records[invoice_type].append(record)

        # Create workbook
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Define column headers for each invoice type
        sheet_configs = {
            "GoogleAds": {
                "columns": ["invoice_id", "advertiser_id", "description", "uom", "quantity", "amount"],
                "headers": ["Invoice ID", "Advertiser ID", "Description", "UoM", "Quantity", "Amount"],
                "amount_col": "F",
            },
            "CM360": {
                "columns": ["invoice_id", "advertiser_id", "description", "uom", "unit_price", "quantity", "amount"],
                "headers": ["Invoice ID", "Advertiser ID", "Description", "UoM", "Unit Price", "Quantity", "Amount"],
                "amount_col": "G",
            },
            "DV360": {
                "columns": ["invoice_id", "advertiser_id", "description", "uom", "quantity", "amount"],
                "headers": ["Invoice ID", "Advertiser ID", "Description", "UoM", "Quantity", "Amount"],
                "amount_col": "F",
            },
            "GoogleVAT": {
                "columns": ["invoice_id", "invoice_ref", "uom", "quantity", "amount"],
                "headers": ["Invoice VAT", "Invoice Ref", "UoM", "Quantity", "Amount"],
                "amount_col": "E",
            },
            "Meta": {
                "columns": ["invoice_id", "account_id", "description", "amount"],
                "headers": ["Invoice Number", "Account ID", "Description", "Amount"],
                "amount_col": "D",
            },
        }

        # Create a sheet for each invoice type that has records
        for invoice_type in sorted(grouped_records.keys()):
            if invoice_type not in sheet_configs:
                continue

            config = sheet_configs[invoice_type]
            ws = wb.create_sheet(title=invoice_type)

            # Write headers
            ws.append(config["headers"])

            # Style headers
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Write data rows
            for record in grouped_records[invoice_type]:
                row = [record.get(col, "") for col in config["columns"]]
                ws.append(row)

            # Add SubTotal, VAT, and Total rows
            if ws.max_row > 1:  # Only add if there's data
                data_end_row = ws.max_row
                total_col_idx = config["columns"].index("amount")
                amount_col = config["amount_col"]

                # Get VAT rate from first record (should be same for all records in this invoice type)
                vat_rate = grouped_records[invoice_type][0].get("vat_rate", 0) or 0

                # SubTotal row
                subtotal_row = [""] * len(config["columns"])
                subtotal_row[total_col_idx - 1] = "SUB TOTAL"
                subtotal_row[total_col_idx] = f"=SUM({amount_col}2:{amount_col}{data_end_row})"
                ws.append(subtotal_row)
                subtotal_row_num = ws.max_row

                # VAT row
                vat_row = [""] * len(config["columns"])
                vat_row[total_col_idx - 1] = f"VAT ({vat_rate}%)"
                vat_row[total_col_idx] = f"=ROUND({amount_col}{subtotal_row_num}*{vat_rate}/100,0)"
                ws.append(vat_row)
                vat_row_num = ws.max_row

                # Total row
                total_row = [""] * len(config["columns"])
                total_row[total_col_idx - 1] = "TOTAL"
                total_row[total_col_idx] = f"={amount_col}{subtotal_row_num}+{amount_col}{vat_row_num}"
                ws.append(total_row)
                total_row_num = ws.max_row

                # Style summary rows
                for row_num in [subtotal_row_num, vat_row_num, total_row_num]:
                    for cell in ws[row_num]:
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

            # Create Excel table (excluding summary rows)
            if ws.max_row > 4:  # More than just header and 3 summary rows
                # Table should only include header + data rows (exclude SubTotal, VAT, Total)
                table_range = f"A1:{chr(64 + len(config['columns']))}{data_end_row}"
                table = Table(displayName=f"{invoice_type}Table", ref=table_range)
                style = TableStyleInfo(
                    name="TableStyleMedium9",
                    showFirstColumn=False,
                    showLastColumn=False,
                    showRowStripes=True,
                    showColumnStripes=False,
                )
                table.tableStyleInfo = style
                ws.add_table(table)

        # Save workbook
        wb.save(output_path)
