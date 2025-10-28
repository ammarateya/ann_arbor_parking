# Parking Citations Map

A beautiful, interactive map interface for visualizing parking citations in Ann Arbor, MI.

## Features

- 📍 **Interactive Map**: View all parking citations plotted on a map of Ann Arbor
- 🎨 **iOS-Style UI**: Clean, modern interface inspired by Find My Friends
- 💰 **Color-Coded Markers**:
  - Blue: Citations under $30
  - Orange: Citations between $30-$50
  - Red: Citations $50 or more
- 📊 **Statistics Dashboard**: Real-time count and total amount of citations
- 🔍 **Detailed Popups**: Click on any marker to see full citation details
- 📅 **Date Information**: View issue dates, due dates, and citation status
- 🖼️ **Image Links**: Direct links to view citation images

## How It Works

### 1. Database Setup

First, you need to run the SQL migration to add geocoding columns:

```bash
# Connect to your database and run:
psql -h your_host -U your_user -d your_database -f docs/alter_schema_ocr.sql
```

### 2. Geocode Existing Citations

If you already have citations in your database, you need to geocode them first:

```bash
python geocode_citations.py
```

This will:

- Find all citations without coordinates
- Geocode their addresses using OpenStreetMap's Nominatim API
- Update the database with latitude/longitude

**Note**: The geocoding API has rate limits, so this may take a while for large datasets. Be patient!

### 3. Start the Web Server

Start the application as usual:

```bash
python main.py
```

### 4. View the Map

Open your browser and navigate to:

```
http://localhost:5000/
```

## New Citations

New citations scraped by the system are automatically geocoded when they're saved to the database. You don't need to manually geocode them!

## API Endpoints

- `GET /` - Main map interface
- `GET /api/citations` - Get all geocoded citations (JSON)
- `GET /api/stats` - Get scraper statistics (JSON)
- `GET /api/health` - Health check endpoint

## Technical Details

### Map Technology

- **Leaflet.js**: Open-source mapping library
- **Dark Theme**: CartoDB dark basemap
- **Nominatim Geocoding**: OpenStreetMap's free geocoding service

### Database Schema

Citations now include:

- `latitude` (double precision)
- `longitude` (double precision)
- `geocoded_at` (timestamp)

### Geocoding

The system uses OpenStreetMap's Nominatim API to convert street addresses to GPS coordinates. This is done:

1. Automatically for new citations as they're scraped
2. In batch via `geocode_citations.py` for existing citations

Rate limiting: 1 second delay between geocoding requests to respect API limits.

## Troubleshooting

### No markers showing on map?

1. Check that citations have been geocoded:

   ```bash
   python geocode_citations.py
   ```

2. Verify citations have location data:
   ```sql
   SELECT citation_number, location, latitude, longitude
   FROM citations
   WHERE latitude IS NULL
   LIMIT 10;
   ```

### Slow geocoding?

- The Nominatim API limits requests to 1 per second
- For large datasets (1000+ citations), expect several hours
- Geocoding happens asynchronously, so you can continue using the system

### Citations not updating?

- New citations are automatically geocoded
- The map refreshes on page reload
- Check the scraper logs for geocoding errors

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design
- Touch-friendly controls
