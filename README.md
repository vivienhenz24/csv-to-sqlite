# County Health Data API - CS1060 HW4

A Flask API that provides county health data by ZIP code and health measure. This project fulfills the requirements for CS1060 Homework 4: API Prototyping with Generative AI.

## Features

- **Part 1**: CSV to SQLite conversion script (`csv_to_sqlite.py`)
- **Part 2**: County health data API with `/county_data` endpoint
- Supports all required health measures
- Proper error handling (400, 404, 418)
- ZIP code to county data joining
- SQLite database with sanitized inputs

## Data Sources

- ZIP code to county mapping (`zip_county.csv`)
- County health rankings data (`county_health_rankings.csv`)

## Local Development

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. API will be available at `http://localhost:8080`

## API Usage

### Endpoint: POST /county_data

**Required Parameters:**
- `zip` - 5-digit ZIP code (e.g., "02138")
- `measure_name` - Health measure name (see valid options below)

**Valid Measure Names:**
- Violent crime rate
- Unemployment
- Children in poverty
- Diabetic screening
- Mammography screening
- Preventable hospital stays
- Uninsured
- Sexually transmitted infections
- Physical inactivity
- Adult obesity
- Premature Death
- Daily fine particulate matter

**Example Request:**
```bash
curl -H 'content-type:application/json' \
     -d '{"zip":"02138","measure_name":"Adult obesity"}' \
     http://localhost:8080/county_data
```

**Special Features:**
- Returns HTTP 418 if `coffee=teapot` is included in request
- Returns HTTP 400 for missing required parameters
- Returns HTTP 404 for invalid ZIP/measure combinations

## Files

- `csv_to_sqlite.py` - Command-line script for CSV to SQLite conversion
- `app.py` - Flask API server
- `data.db` - SQLite database with processed data
- `requirements.txt` - Python dependencies
- `index.html` - API documentation page

## Testing

The API correctly handles:
- Valid ZIP codes and health measures
- Invalid inputs with proper error codes
- The special "teapot" easter egg (HTTP 418)
- Cross-table joins between ZIP and county data

## Homework Compliance

This implementation fully satisfies CS1060 HW4 requirements:

**Part 1 (15 points):**
✅ `csv_to_sqlite.py` script created with generative AI  
✅ Accepts valid CSV files with header rows  
✅ Outputs SQLite database  
✅ Takes database name and CSV file as arguments  
✅ Works with provided data sources  

**Part 2 (35 points):**  
✅ API endpoint `/county_data` implemented  
✅ Accepts HTTP POST with JSON content  
✅ Returns county health data in correct schema  
✅ Validates ZIP code (5 digits) and measure name  
✅ Implements coffee=teapot → HTTP 418 easter egg  
✅ Returns HTTP 400 for missing parameters  
✅ Returns HTTP 404 for invalid data combinations  
✅ Sanitizes SQL inputs  
✅ Successfully joins ZIP and county health data