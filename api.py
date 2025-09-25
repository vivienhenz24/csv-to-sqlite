#!/usr/bin/env python3
"""Prototype HTTP API exposing county data from data.db."""

from __future__ import annotations

import argparse
import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

ALLOWED_MEASURES: Tuple[str, ...] = (
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter",
)

sqlite_connection: sqlite3.Connection | None = None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve county data from an existing SQLite database.")
    parser.add_argument("--database", default="data.db", help="Path to the SQLite database (default: data.db)")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind the HTTP server to")
    parser.add_argument("--port", type=int, default=8000, help="TCP port for the HTTP server")
    return parser.parse_args()


class CountyDataHandler(BaseHTTPRequestHandler):
    def _json_response(self, status: HTTPStatus, payload: Dict | List) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _client_error(self, status: HTTPStatus, message: str) -> None:
        self._json_response(status, {"error": message})

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        if sqlite_connection is None:
            self._client_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Database connection unavailable")
            return

        route = urlparse(self.path).path
        if route != "/county_data":
            self._client_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

        content_length = self.headers.get("Content-Length")
        if content_length is None:
            self._client_error(HTTPStatus.LENGTH_REQUIRED, "Missing Content-Length header")
            return

        try:
            raw_body = self.rfile.read(int(content_length))
        except (ValueError, OSError):
            self._client_error(HTTPStatus.BAD_REQUEST, "Invalid request body")
            return

        if raw_body.strip() == b"":
            self._client_error(HTTPStatus.BAD_REQUEST, "Empty request body")
            return

        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            self._client_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Content-Type must be application/json")
            return

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._client_error(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON")
            return

        if not isinstance(payload, dict):
            self._client_error(HTTPStatus.BAD_REQUEST, "JSON payload must be an object")
            return

        if payload.get("coffee") == "teapot":
            self._json_response(HTTPStatus.IM_A_TEAPOT, {"error": "I'm a teapot"})
            return

        zip_code = payload.get("zip")
        measure_name = payload.get("measure_name")

        if not zip_code or not measure_name:
            self._client_error(HTTPStatus.BAD_REQUEST, "zip and measure_name are required")
            return

        if not isinstance(zip_code, str) or len(zip_code) != 5 or not zip_code.isdigit():
            self._client_error(HTTPStatus.BAD_REQUEST, "zip must be a 5-digit string")
            return

        if not isinstance(measure_name, str) or measure_name not in ALLOWED_MEASURES:
            self._client_error(HTTPStatus.BAD_REQUEST, "measure_name is invalid")
            return

        try:
            cursor = sqlite_connection.execute(
                """
                SELECT chr.State, chr.County, chr.State_code, chr.County_code, chr.Year_span,
                       chr.Measure_name, chr.Measure_id, chr.Numerator, chr.Denominator,
                       chr.Raw_value, chr.Confidence_Interval_Lower_Bound,
                       chr.Confidence_Interval_Upper_Bound, chr.Data_Release_Year, chr.fipscode
                FROM county_health_rankings AS chr
                JOIN zip_county AS zc
                  ON zc.county = chr.County AND zc.state_abbreviation = chr.State
                WHERE zc.zip = ? AND chr.Measure_name = ?
                ORDER BY chr.Data_Release_Year
                """,
                (zip_code, measure_name),
            )
            rows = cursor.fetchall()
        except sqlite3.DatabaseError:
            self._client_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Database query failed")
            return

        if not rows:
            self._client_error(HTTPStatus.NOT_FOUND, "No data for requested zip and measure_name")
            return

        response_body: List[Dict[str, str]] = []
        for row in rows:
            row_dict = {column.lower(): row[column] for column in row.keys()}
            response_body.append(row_dict)

        self._json_response(HTTPStatus.OK, response_body)

    def do_GET(self) -> None:  # noqa: N802
        self._client_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003, D401
        """Log to stdout with handler prefix."""
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    global sqlite_connection

    args = parse_arguments()
    db_path = Path(args.database)

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    sqlite_connection = sqlite3.connect(db_path, check_same_thread=False)
    sqlite_connection.row_factory = sqlite3.Row

    server = HTTPServer((args.host, args.port), CountyDataHandler)
    print(f"Serving county data on http://{args.host}:{args.port}/county_data (CTRL+C to quit)")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()
        if sqlite_connection is not None:
            sqlite_connection.close()
            sqlite_connection = None


if __name__ == "__main__":
    main()
