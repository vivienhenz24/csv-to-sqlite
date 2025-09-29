# CSV to SQLite Converter

A web application that converts CSV files to SQLite databases. This project can be deployed on Netlify as a serverless function.

 https://csv-to-sqlite-converter.netlify.app


## Features

- Upload CSV files through a modern web interface
- Convert CSV data to SQLite format
- Download the resulting SQLite database
- Drag and drop file upload support
- Responsive design

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your browser to `http://localhost:5000`

## Netlify Deployment

1. Connect your GitHub repository to Netlify
2. Set the build command: `pip install -r requirements.txt`
3. Set the publish directory: `.`
4. Deploy!

The application will be available as a static site with serverless functions for CSV processing.

## Usage

1. Visit the web application
2. Upload a CSV file by dragging and dropping or clicking to browse
3. Click "Convert to SQLite"
4. Download the resulting SQLite database file

## File Structure

- `app.py` - Flask web application
- `templates/index.html` - Web interface
- `netlify/functions/csv-converter.py` - Serverless function for Netlify
- `requirements.txt` - Python dependencies
- `netlify.toml` - Netlify configuration
- `csv_to_sqlite.py` - Original command-line script

