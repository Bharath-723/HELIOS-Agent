"""
modules/spreadsheet_agent.py — HELIOS Local Spreadsheet Agent
===============================================================
Local-first spreadsheet processing engine for Excel (.xlsx, .xls) and CSV (.csv) files.
Supports sheet inspection, column filtering, summary statistics, aggregate calculations (e.g. failure rates),
and workbook exports using pandas and openpyxl.
"""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

log = logging.getLogger("helios.spreadsheet_agent")


class SpreadsheetAgent:
    """Local spreadsheet analysis and manipulation engine."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path) if file_path else None

    def read_spreadsheet(self, file_path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        p = Path(file_path) if file_path else self.file_path
        if not p or not p.exists():
            raise FileNotFoundError(f"Spreadsheet file '{file_path}' not found.")

        ext = p.suffix.lower()
        log.info("Reading spreadsheet '%s' (type: %s)", p.name, ext)

        if ext == ".csv":
            df = pd.read_csv(p)
            return {"Sheet1": df}
        elif ext in {".xlsx", ".xls"}:
            excel = pd.ExcelFile(p)
            return {sheet: excel.parse(sheet) for sheet in excel.sheet_names}
        else:
            raise ValueError(f"Unsupported spreadsheet format: '{ext}'")

    def summarize(self, file_path: Optional[str] = None) -> str:
        try:
            sheets = self.read_spreadsheet(file_path)
            lines = []
            for name, df in sheets.items():
                lines.append(f"--- Sheet: '{name}' ({len(df)} rows, {len(df.columns)} columns) ---")
                lines.append(f"Columns: {', '.join(str(c) for c in df.columns)}")
                lines.append("Head Preview:")
                lines.append(df.head(5).to_string(index=False))
                lines.append("")
            return "\n".join(lines)
        except Exception as exc:
            log.error("Spreadsheet summarize error: %s", exc, exc_info=True)
            return f"[Spreadsheet Error: {exc}]"

    def filter_failed_inspections(self, file_path: Optional[str] = None) -> pd.DataFrame:
        sheets = self.read_spreadsheet(file_path)
        first_sheet = next(iter(sheets.values()))

        # Look for status columns
        status_col = None
        for col in first_sheet.columns:
            if "status" in str(col).lower() or "result" in str(col).lower() or "finding" in str(col).lower():
                status_col = col
                break

        if status_col:
            failed_df = first_sheet[first_sheet[status_col].astype(str).str.lower().str.contains("fail|non-compliant|defect|critical|warning", na=False)]
            return failed_df
        return first_sheet

    def calculate_failure_rate(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        sheets = self.read_spreadsheet(file_path)
        first_sheet = next(iter(sheets.values()))

        total_records = len(first_sheet)
        if total_records == 0:
            return {"total": 0, "failures": 0, "failure_rate_pct": 0.0, "by_plant": {}}

        status_col = None
        for col in first_sheet.columns:
            if "status" in str(col).lower() or "result" in str(col).lower() or "finding" in str(col).lower():
                status_col = col
                break

        plant_col = None
        for col in first_sheet.columns:
            if "plant" in str(col).lower() or "unit" in str(col).lower() or "facility" in str(col).lower() or "location" in str(col).lower():
                plant_col = col
                break

        failures = 0
        if status_col:
            failures = len(first_sheet[first_sheet[status_col].astype(str).str.lower().str.contains("fail|non-compliant|defect|critical|warning", na=False)])

        failure_rate = (failures / total_records) * 100.0

        by_plant = {}
        if plant_col and status_col:
            for plant, group in first_sheet.groupby(plant_col):
                p_tot = len(group)
                p_fail = len(group[group[status_col].astype(str).str.lower().str.contains("fail|non-compliant|defect|critical|warning", na=False)])
                by_plant[str(plant)] = {
                    "total": p_tot,
                    "failures": p_fail,
                    "failure_rate_pct": round((p_fail / p_tot) * 100.0, 2) if p_tot > 0 else 0.0
                }

        return {
            "total_inspections": total_records,
            "failed_inspections": failures,
            "overall_failure_rate_pct": round(failure_rate, 2),
            "by_plant": by_plant
        }

    def create_summary_workbook(self, input_path: str, output_path: str) -> str:
        stats = self.calculate_failure_rate(input_path)
        failed_df = self.filter_failed_inspections(input_path)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            failed_df.to_excel(writer, sheet_name="Failed Inspections", index=False)
            
            # Summary Sheet
            summary_data = [
                {"Metric": "Total Inspections", "Value": stats["total_inspections"]},
                {"Metric": "Failed Inspections", "Value": stats["failed_inspections"]},
                {"Metric": "Overall Failure Rate (%)", "Value": stats["overall_failure_rate_pct"]}
            ]
            for plant, p_stats in stats["by_plant"].items():
                summary_data.append({"Metric": f"Failure Rate - {plant} (%)", "Value": p_stats["failure_rate_pct"]})

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)

        log.info("Created summary workbook at '%s'", output_path)
        return f"Successfully created summary workbook at '{output_path}'"
