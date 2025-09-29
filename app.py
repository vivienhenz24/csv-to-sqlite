#!/usr/bin/env python3
"""Web application for CSV to SQLite conversion using Flask."""

import csv
import io
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List

from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def ensure_identifier(name: str, kind: str) -> str:
    """Ensure the name is a valid SQL identifier."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid {kind} name: {name}")
    return name

def sanitize_headers(headers: Iterable[str]) -> List[str]:
    """Sanitize CSV headers to be valid SQL column names."""
    sanitized = []
    for column in headers:
        column = column.strip().lstrip("\ufeff")
        sanitized.append(ensure_identifier(column, "column"))
    return sanitized

def derive_table_name(filename: str) -> str:
    """Derive table name from filename."""
    base_name = Path(filename).name
    table_name = Path(base_name).stem
    return ensure_identifier(table_name, "table")

def convert_csv_to_sqlite(csv_content: str, filename: str) -> bytes:
    """Convert CSV content to SQLite database in memory."""
    table_name = derive_table_name(filename)
    
    # Create in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Parse CSV content
    csv_reader = csv.reader(io.StringIO(csv_content))
    try:
        header_row = next(csv_reader)
    except StopIteration:
        raise ValueError("CSV file is empty.")
    
    columns = sanitize_headers(header_row)
    placeholders = ", ".join(["?"] * len(columns))
    column_list = ", ".join(columns)
    column_definitions = ", ".join(f"{column} TEXT" for column in columns)
    
    # Create table
    cursor.execute(f"CREATE TABLE {table_name} ({column_definitions})")
    
    # Insert data
    insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
    for row in csv_reader:
        if not row:
            continue
        if len(row) != len(columns):
            # Normalize row length to column count by truncating or padding blanks
            row = (row + [""] * len(columns))[: len(columns)]
        cursor.execute(insert_sql, row)
    
    # Export to bytes
    conn.commit()
    
    # Get database as bytes
    db_bytes = b''.join(conn.iterdump().encode('utf-8'))
    conn.close()
    
    return db_bytes

@app.route('/')
def index():
    """Main page with file upload form."""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """Handle CSV to SQLite conversion."""
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        
        # Convert to SQLite
        db_bytes = convert_csv_to_sqlite(csv_content, file.filename)
        
        # Return SQLite file
        output_filename = Path(file.filename).stem + '.db'
        return send_file(
            io.BytesIO(db_bytes),
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/x-sqlite3'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
