#!/usr/bin/env python3
"""County Health Data API - CS1060 HW4"""

import json
import sqlite3
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

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
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_input(value):
    """Basic input sanitization for SQL queries"""
    if not isinstance(value, str):
        return str(value)
    # Remove potentially dangerous characters
    return value.replace("'", "''").replace(";", "").replace("--", "")

@app.route('/county_data', methods=['POST'])
def county_data():
    """
    API endpoint to get county health data by ZIP code and measure name.
    
    Expected JSON input:
    {
        "zip": "02138",
        "measure_name": "Adult obesity",
        "coffee": "teapot"  # optional - triggers 418 error
    }
    """
    
    # Check content type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    # Check for coffee=teapot (Easter egg requirement)
    if data.get('coffee') == 'teapot':
        return jsonify({"error": "I'm a teapot"}), 418
    
    # Validate required fields
    if 'zip' not in data or 'measure_name' not in data:
        return jsonify({"error": "Both 'zip' and 'measure_name' are required"}), 400
    
    zip_code = sanitize_input(data['zip'])
    measure_name = sanitize_input(data['measure_name'])
    
    # Validate measure name
    if measure_name not in VALID_MEASURES:
        return jsonify({"error": f"Invalid measure_name. Must be one of: {list(VALID_MEASURES)}"}), 400
    
    # Validate ZIP code format (5 digits)
    if not zip_code.isdigit() or len(zip_code) != 5:
        return jsonify({"error": "ZIP code must be exactly 5 digits"}), 400
    
    try:
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
            return jsonify({"error": "No data found for the specified ZIP code and measure"}), 404
        
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
        
        return jsonify(output)
        
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def index():
    """Simple index page explaining the API"""
    return jsonify({
        "message": "County Health Data API - CS1060 HW4",
        "endpoints": {
            "POST /county_data": "Get county health data by ZIP code and measure name"
        },
        "required_parameters": ["zip", "measure_name"],
        "valid_measures": list(VALID_MEASURES)
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == '__main__':
    # Check if data.db exists
    if not os.path.exists('data.db'):
        print("Error: data.db not found. Please run csv_to_sqlite.py first.")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5000)