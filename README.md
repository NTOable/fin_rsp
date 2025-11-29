# Inventory Management System (IMS Pro)

A modern inventory management dashboard with PostgreSQL database integration.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Web browser

## Database Setup

1. Make sure PostgreSQL is running on your machine
2. Create the table by running the SQL script:
   ```bash
   psql -U postgres -d postgres -f item_table.sql
   ```
   Or execute the SQL in your PostgreSQL client (pgAdmin, DBeaver, etc.)

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify database credentials in `app.py`:
   ```python
   DB_CONFIG = {
       'dbname': 'postgres',
       'user': 'postgres',
       'password': 'admin',
       'host': 'localhost',
       'port': '5432'
   }
   ```

## Running the Application

1. **Start the Flask API server:**
   ```bash
   python app.py
   ```
   The server will start at `http://localhost:5000`

2. **Open the Dashboard:**
   - Open `preview_ui.html` in your web browser
   - Or use a local server: `python -m http.server 8080` and visit `http://localhost:8080/preview_ui.html`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/items` | Get all items |
| GET | `/api/items/<id>` | Get single item |
| POST | `/api/items` | Add new item |
| PUT | `/api/items/<id>` | Update item |
| DELETE | `/api/items/<id>` | Delete item |
| POST | `/api/items/bulk` | Add multiple items |
| GET | `/api/stats` | Get inventory statistics |
| GET | `/api/health` | Health check |

## Features

- ✅ View all inventory items
- ✅ Add new items (manual input)
- ✅ Edit existing items
- ✅ Delete items
- ✅ Search and filter
- ✅ Export to CSV
- ✅ Analytics dashboard
- ✅ Generate reports
- ✅ Settings configuration
- ✅ Offline mode (works without API)

## Connection Status

The dashboard shows connection status in the top bar:
- **Connected** (green): API is running and connected to database
- **Offline Mode** (yellow): API not available, using local data

## Troubleshooting

1. **API not connecting:**
   - Make sure Flask server is running (`python app.py`)
   - Check if PostgreSQL is running
   - Verify database credentials

2. **Database errors:**
   - Run the SQL script to create the table
   - Check if PostgreSQL is accessible on port 5432

3. **CORS errors:**
   - The Flask app has CORS enabled by default
   - Make sure you're accessing via localhost

## Project Structure

```
UI/
├── app.py              # Flask API server
├── preview_ui.html     # Frontend dashboard
├── item_table.sql      # Database schema
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Credits

© 2025 CIIT OS Group 3

