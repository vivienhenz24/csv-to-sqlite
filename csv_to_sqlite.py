#!/usr/bin/env python3
"""Convert a CSV file into a SQLite table."""

import argparse
import csv
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a CSV file into a SQLite database.")
    parser.add_argument("database", help="Path to the SQLite database file to create or update.")
    parser.add_argument("csv_file", help="Path to the CSV file to load.")
    return parser.parse_args()

def ensure_identifier(name: str, kind: str) -> str:
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid {kind} name: {name}")
    return name

def sanitize_headers(headers: Iterable[str]) -> List[str]:
    sanitized = []
    for column in headers:
        column = column.strip().lstrip("\ufeff")
        sanitized.append(ensure_identifier(column, "column"))
    return sanitized

def derive_table_name(csv_path: str) -> str:
    base_name = Path(csv_path).name
    table_name = Path(base_name).stem
    return ensure_identifier(table_name, "table")

def load_csv_to_sqlite(database: str, csv_file: str) -> None:
    table_name = derive_table_name(csv_file)

    with open(csv_file, newline="", encoding="utf-8") as input_csv:
        reader = csv.reader(input_csv)
        try:
            header_row = next(reader)
        except StopIteration:
            raise ValueError("CSV file is empty.") from None

        columns = sanitize_headers(header_row)
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)
        column_definitions = ", ".join(f"{column} TEXT" for column in columns)

        with sqlite3.connect(database) as connection:
            cursor = connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(f"CREATE TABLE {table_name} ({column_definitions})")

            insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
            for row in reader:
                if not row:
                    continue
                if len(row) != len(columns):
                    # Normalize row length to column count by truncating or padding blanks.
                    row = (row + [""] * len(columns))[: len(columns)]
                cursor.execute(insert_sql, row)
            connection.commit()

def main() -> None:
    args = parse_args()
    load_csv_to_sqlite(args.database, args.csv_file)

if __name__ == "__main__":
    main()
