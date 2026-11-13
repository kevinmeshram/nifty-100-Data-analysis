"""Excel loader: read raw files, clean column names, normalise years and tickers."""
import logging
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.etl.normaliser import normalize_ticker, normalize_year

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
RAW_DIR = ROOT / os.getenv("RAW_DIR", "data/raw")

# ASSUMPTION: these column names are guesses. Fix them after Step 4.
YEAR_COLUMNS = ["year"]
TICKER_COLUMNS = ["company_id", "ticker", "symbol"]

log = logging.getLogger(__name__)


def clean_column_name(name):
    """'Net Profit (Rs Cr)' -> 'net_profit_rs_cr'."""
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def list_excel_files(folder=RAW_DIR):
    """Return all Excel files in a folder. Skip temporary '~$' files."""
    return sorted(
        path for path in Path(folder).glob("*.xls*") if not path.name.startswith("~$")
    )


def read_excel_file(path, sheet_name=0):
    """Read one sheet and give the columns clean names."""
    df = pd.read_excel(path, sheet_name=sheet_name)
    df.columns = [clean_column_name(column) for column in df.columns]
    return df


def _apply(df, column, func, rejected, reasons):
    """Apply a normaliser to one column. Mark rows that raise ValueError."""
    new_values = []
    for index, value in df[column].items():
        try:
            new_values.append(func(value))
        except ValueError as error:
            new_values.append(None)
            rejected[index] = True
            reasons[index] += f"{column}: {error}; "
    return pd.Series(new_values, index=df.index)


def normalise_frame(df):
    """Return (clean_rows, rejected_rows). Bad rows get a reject_reason."""
    df = df.copy()
    rejected = pd.Series(False, index=df.index)
    reasons = pd.Series("", index=df.index)

    for column in YEAR_COLUMNS:
        if column in df.columns:
            df[column] = _apply(df, column, normalize_year, rejected, reasons).astype("Int64")
    for column in TICKER_COLUMNS:
        if column in df.columns:
            df[column] = _apply(df, column, normalize_ticker, rejected, reasons)

    clean_rows = df[~rejected].copy()
    rejected_rows = df[rejected].copy()
    rejected_rows["reject_reason"] = reasons[rejected]

    # Guard: a wrong column list must not delete all data without a sign.
    if len(df) > 0 and len(clean_rows) == 0:
        raise ValueError("All rows were rejected. Check YEAR_COLUMNS and TICKER_COLUMNS.")
    return clean_rows, rejected_rows


def inspect_files(folder=RAW_DIR):
    """Print sheets, columns, and row counts of every Excel file. Print no values."""
    files = list_excel_files(folder)
    print(f"Folder: {folder}")
    print(f"Excel files found: {len(files)}")
    for path in files:
        sheets = pd.read_excel(path, sheet_name=None)
        for sheet_name, df in sheets.items():
            columns = [clean_column_name(column) for column in df.columns]
            print(f"\n{path.name} | sheet: {sheet_name} | rows: {len(df)}")
            print("  columns:", columns)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    inspect_files()