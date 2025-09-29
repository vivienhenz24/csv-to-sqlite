#!/usr/bin/env python3
"""County Health Data API - CS1060 HW4 - Netlify Function"""

import json
import sqlite3
import os
from pathlib import Path

# Valid measure names as specified in the homework
VALID_MEASURES = {
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
    "Daily fine particulate matter"
}

def get_db_connection():
    """Get database connection to data.db"""
    # Look for data.db in the same directory as this function
    db_path = Path(__file__).parent.parent.parent / "data.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_input(value):
    """Basic input sanitization for SQL queries"""
    if not isinstance(value, str):
        return str(value)
    # Remove potentially dangerous characters
    return value.replace("'", "''").replace(";", "").replace("--", "")

def handler(event, context):
    """Netlify function handler for county_data endpoint"""
    
    # Only allow POST requests
    if event['httpMethod'] != 'POST':
        if event['httpMethod'] == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "County Health Data API - CS1060 HW4",
                    "method": "POST to /county_data",
                    "required_parameters": ["zip", "measure_name"],
                    "valid_measures": list(VALID_MEASURES)
                })
            }
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Method not allowed"})
            }
    
    try:
        # Parse request body
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Request body is required"})
            }
        
        data = json.loads(event['body'])
        
        # Check for coffee=teapot (Easter egg requirement)
        if data.get('coffee') == 'teapot':
            return {
                'statusCode': 418,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "I'm a teapot"})
            }
        
        # Validate required fields
        if 'zip' not in data or 'measure_name' not in data:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Both 'zip' and 'measure_name' are required"})
            }
        
        zip_code = sanitize_input(data['zip'])
        measure_name = sanitize_input(data['measure_name'])
        
        # Validate measure name
        if measure_name not in VALID_MEASURES:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": f"Invalid measure_name. Must be one of: {list(VALID_MEASURES)}"})
            }
        
        # Validate ZIP code format (5 digits)
        if not zip_code.isdigit() or len(zip_code) != 5:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "ZIP code must be exactly 5 digits"})
            }
        
        # Query database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query to join zip_county and county_health_rankings tables
        query = """
        SELECT chr.State as state,
               chr.County as county,
               chr.State_code as state_code,
               chr.County_code as county_code,
               chr.Year_span as year_span,
               chr.Measure_name as measure_name,
               chr.Measure_id as measure_id,
               chr.Numerator as numerator,
               chr.Denominator as denominator,
               chr.Raw_value as raw_value,
               chr.Confidence_Interval_Lower_Bound as confidence_interval_lower_bound,
               chr.Confidence_Interval_Upper_Bound as confidence_interval_upper_bound,
               chr.Data_Release_Year as data_release_year,
               chr.fipscode as fipscode
        FROM zip_county zc
        JOIN county_health_rankings chr ON 
            zc.county_state = chr.State AND
            zc.county = chr.County
        WHERE zc.zip = ? AND chr.Measure_name = ?
        """
        
        cursor.execute(query, (zip_code, measure_name))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "No data found for the specified ZIP code and measure"})
            }
        
        # Convert results to list of dictionaries
        output = []
        for row in results:
            output.append({
                "state": row['state'],
                "county": row['county'], 
                "state_code": row['state_code'],
                "county_code": row['county_code'],
                "year_span": row['year_span'],
                "measure_name": row['measure_name'],
                "measure_id": row['measure_id'],
                "numerator": row['numerator'],
                "denominator": row['denominator'],
                "raw_value": row['raw_value'],
                "confidence_interval_lower_bound": row['confidence_interval_lower_bound'],
                "confidence_interval_upper_bound": row['confidence_interval_upper_bound'],
                "data_release_year": row['data_release_year'],
                "fipscode": row['fipscode']
            })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(output)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Invalid JSON in request body"})
        }
    except sqlite3.Error as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Database error: {str(e)}"})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Internal server error: {str(e)}"})
        }
