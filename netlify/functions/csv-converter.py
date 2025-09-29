import json
import csv
import io
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List

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

def convert_csv_to_sqlite(csv_content: str, filename: str) -> str:
    """Convert CSV content to SQLite database and return as SQL dump."""
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
    
    # Export to SQL dump
    conn.commit()
    sql_dump = '\n'.join(conn.iterdump())
    conn.close()
    
    return sql_dump

def handler(event, context):
    """Netlify function handler."""
    try:
        # Parse the request
        if event['httpMethod'] != 'POST':
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Get the CSV content from the request body
        body = json.loads(event['body'])
        csv_content = body.get('csv_content', '')
        filename = body.get('filename', 'data.csv')
        
        if not csv_content:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No CSV content provided'})
            }
        
        # Convert CSV to SQLite
        sql_dump = convert_csv_to_sqlite(csv_content, filename)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/sql',
                'Content-Disposition': f'attachment; filename="{Path(filename).stem}.sql"'
            },
            'body': sql_dump
        }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
