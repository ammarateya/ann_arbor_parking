from flask import Flask, jsonify, render_template, request
import os
import logging
from pathlib import Path
from db_manager import DatabaseManager
from storage_factory import StorageFactory
from email_notifier import EmailNotifier

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}

# Create a single DatabaseManager instance to reuse across requests
# This prevents creating multiple Supabase clients which can accumulate memory
_db_manager = None

def get_db_manager():
    """Get or create the shared DatabaseManager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(DB_CONFIG)
    return _db_manager

def get_og_image_url(base_url):
    """Get the Open Graph preview image URL, checking for og-preview.png first"""
    # Check if og-preview.png exists in static folder
    static_dir = Path(__file__).parent.parent / 'static'
    if (static_dir / 'og-preview.png').exists():
        return f"{base_url}/static/og-preview.png"
    # Fallback to parking-icon
    return f"{base_url}/static/parking-icon.png"

@app.route('/')
def index():
    """Main map page"""
    # Generate absolute URLs for Open Graph meta tags
    base_url = request.url_root.rstrip('/')
    og_url = f"{base_url}{request.path}"
    og_image = get_og_image_url(base_url)
    return render_template('map.html', og_url=og_url, og_image=og_image, base_url=base_url)

@app.route('/about/')
@app.route('/about')
def about():
    """About page explaining the scraping methodology"""
    # Generate absolute URLs for Open Graph meta tags
    base_url = request.url_root.rstrip('/')
    og_url = f"{base_url}{request.path}"
    og_image = get_og_image_url(base_url)
    return render_template('about.html', og_url=og_url, og_image=og_image, base_url=base_url)

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        db_manager = get_db_manager()
        last_citation = db_manager.get_last_successful_citation()
        
        return jsonify({
            'status': 'healthy',
            'service': 'parking-citation-scraper',
            'last_successful_citation': last_citation,
            'message': 'Scraper is running every 10 minutes'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/citations')
def get_citations():
    """Get all citations with location data"""
    try:
        db_manager = get_db_manager()
        
        # Try to get all citations that have a location field
        # Use postgrest syntax for row selection with pagination
        # Supabase PostgREST has a default limit of 1000, so we need to paginate
        try:
            # Exclude raw_html to save memory (it's 50-200KB per citation!)
            # Exclude vin, due_date, issuing_agency, status, scraped_at, image_urls, and created_at - not used in frontend, reduces payload size
            fields = 'citation_number,location,plate_state,plate_number,issue_date,amount_due,more_info_url,comments,violations,latitude,longitude'
            
            # Fetch all citations with pagination
            citations = []
            page_size = 1000
            offset = 0
            
            while True:
                result = (
                    db_manager.supabase
                    .table('citations')
                    .select(fields)
                    .not_.is_('location', 'null')
                    .order('issue_date', desc=True)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
                page_data = result.data if result.data else []
                if not page_data:
                    break
                citations.extend(page_data)
                # If we got fewer than page_size, we've reached the end
                if len(page_data) < page_size:
                    break
                offset += page_size
                
        except Exception as e:
            # If that fails due to RLS, try a different approach
            logger.warning(f"Query failed due to RLS or permissions: {e}")
            
            # Try with service role key if available
            service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            if service_key:
                from supabase import create_client
                supabase_url = os.getenv('SUPABASE_URL')
                if supabase_url:
                    service_client = create_client(supabase_url, service_key)
                    # Exclude raw_html to save memory
                    # Exclude vin, due_date, issuing_agency, status, scraped_at, image_urls, and created_at - not used in frontend, reduces payload size
                    fields = 'citation_number,location,plate_state,plate_number,issue_date,amount_due,more_info_url,comments,violations,latitude,longitude'
                    
                    # Fetch all citations with pagination using service client
                    citations = []
                    page_size = 1000
                    offset = 0
                    
                    while True:
                        result = (
                            service_client
                            .table('citations')
                            .select(fields)
                            .not_.is_('location', 'null')
                            .order('issue_date', desc=True)
                            .range(offset, offset + page_size - 1)
                            .execute()
                        )
                        page_data = result.data if result.data else []
                        if not page_data:
                            break
                        citations.extend(page_data)
                        # If we got fewer than page_size, we've reached the end
                        if len(page_data) < page_size:
                            break
                        offset += page_size
                else:
                    citations = []
            else:
                # Fallback: return empty list with helpful error
                return jsonify({
                    'status': 'error',
                    'error': 'Database query requires authentication. Please set SUPABASE_SERVICE_ROLE_KEY in your environment variables to bypass Row Level Security.',
                    'citations': [],
                    'count': 0,
                    'most_recent_citation_time': None
                }), 200  # Return 200 with empty data instead of error
        
        # Filter out citations without coordinates (they need to be geocoded on frontend)
        citations_with_coords = [c for c in citations if c.get('latitude') and c.get('longitude')]
        
        # Get the most recent citation timestamp and number directly from database
        # This ensures we get the actual latest even if it's not in the current result set
        most_recent_time = None
        most_recent_citation_number = None
        try:
            latest_result = (
                db_manager.supabase
                .table('citations')
                .select('issue_date,citation_number')
                .not_.is_('location', 'null')
                .not_.is_('issue_date', 'null')
                .not_.is_('latitude', 'null')
                .not_.is_('longitude', 'null')
                .order('issue_date', desc=True)
                .limit(1)
                .execute()
            )
            if latest_result.data and latest_result.data[0].get('issue_date'):
                most_recent_time = latest_result.data[0]['issue_date']
                most_recent_citation_number = latest_result.data[0].get('citation_number')
        except Exception as e:
            logger.warning(f"Failed to get most recent citation time: {e}")
            # Fallback: check citations_with_coords if database query fails
            if citations_with_coords:
                for citation in citations_with_coords:
                    issue_date = citation.get('issue_date')
                    if issue_date:
                        if most_recent_time is None or issue_date > most_recent_time:
                            most_recent_time = issue_date
                            most_recent_citation_number = citation.get('citation_number')
        
        # Return all citations
        return jsonify({
            'status': 'success',
            'citations': citations_with_coords,
            'count': len(citations_with_coords),
            'total': len(citations),
            'most_recent_citation_time': most_recent_time,
            'most_recent_citation_number': most_recent_citation_number
        })
    except Exception as e:
        import traceback
        logger.error(f"Error in get_citations: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'tip': 'Check that SUPABASE_SERVICE_ROLE_KEY is set for reading data'
        }), 500

@app.route('/api/search')
def search_citations():
    """Search citations by plate+state, citation number, or by location radius.

    Query params (any one mode):
      - mode=plate & plate_state=MI & plate_number=ABC123
      - mode=citation & citation_number=12345678
      - mode=location & lat=42.28 & lon=-83.74 & radius_m=500

    Notes:
      - Uses Supabase PostgREST filters (parameterized under the hood) to avoid injection.
      - For location, first filters by bounding box, then applies accurate haversine distance in Python.
    """
    try:
        mode = (request.args.get('mode') or '').strip().lower()
        db_manager = get_db_manager()

        # Optional time bound: ISO 8601 string; when provided, only return citations with
        # issue_date >= since_iso
        since_iso = (request.args.get('since') or '').strip() or None

        citations = []

        if mode == 'plate':
            plate_state = (request.args.get('plate_state') or '').strip().upper()
            plate_number = (request.args.get('plate_number') or '').strip()
            if not plate_state or not plate_number:
                return jsonify({'status': 'error', 'error': 'plate_state and plate_number are required'}), 400

            # Case-insensitive match for plate_number; exact for state
            # Exclude raw_html to save memory
            # Exclude vin, due_date, issuing_agency, status, scraped_at, image_urls, and created_at - not used in frontend, reduces payload size
            fields = 'citation_number,location,plate_state,plate_number,issue_date,amount_due,more_info_url,comments,violations,latitude,longitude'
            query = db_manager.supabase.table('citations').select(fields)
            query = query.eq('plate_state', plate_state).ilike('plate_number', plate_number)
            if since_iso:
                query = query.gte('issue_date', since_iso)
            result = query.execute()
            citations = result.data or []

        elif mode == 'citation':
            citation_number = request.args.get('citation_number')
            if not citation_number:
                return jsonify({'status': 'error', 'error': 'citation_number is required'}), 400
            try:
                citation_number_int = int(str(citation_number).strip())
            except ValueError:
                return jsonify({'status': 'error', 'error': 'citation_number must be an integer'}), 400

            # Exclude raw_html to save memory
            # Exclude vin, due_date, issuing_agency, status, scraped_at, image_urls, and created_at - not used in frontend, reduces payload size
            fields = 'citation_number,location,plate_state,plate_number,issue_date,amount_due,more_info_url,comments,violations,latitude,longitude'
            result = (
                db_manager
                .supabase
                .table('citations')
                .select(fields)
                .eq('citation_number', citation_number_int)
            )
            if since_iso:
                result = result.gte('issue_date', since_iso)
            result = result.execute()
            citations = result.data or []

        elif mode == 'location':
            try:
                lat = float(request.args.get('lat', ''))
                lon = float(request.args.get('lon', ''))
                radius_m = float(request.args.get('radius_m', ''))
            except ValueError:
                return jsonify({'status': 'error', 'error': 'lat, lon, and radius_m must be numbers'}), 400

            if radius_m <= 0 or radius_m > 100000:
                return jsonify({'status': 'error', 'error': 'radius_m must be between 1 and 100000 meters'}), 400

            # Compute simple bounding box to narrow results
            # 1 degree latitude ~ 111,000 meters; longitude scaled by cos(latitude)
            deg_lat = radius_m / 111000.0
            import math
            deg_lon = radius_m / (111000.0 * max(math.cos(math.radians(lat)), 1e-6))

            min_lat = lat - deg_lat
            max_lat = lat + deg_lat
            min_lon = lon - deg_lon
            max_lon = lon + deg_lon

            # Filter by bbox and presence of coordinates
            # Exclude raw_html to save memory (it's 50-200KB per citation!)
            # Exclude vin, due_date, issuing_agency, status, scraped_at, image_urls, and created_at - not used in frontend, reduces payload size
            fields = 'citation_number,location,plate_state,plate_number,issue_date,amount_due,more_info_url,comments,violations,latitude,longitude'
            bbox_query = (
                db_manager
                .supabase
                .table('citations')
                .select(fields)
                .not_.is_('latitude', 'null')
                .not_.is_('longitude', 'null')
                .gte('latitude', min_lat)
                .lte('latitude', max_lat)
                .gte('longitude', min_lon)
                .lte('longitude', max_lon)
            )
            if since_iso:
                bbox_query = bbox_query.gte('issue_date', since_iso)
            bbox_result = bbox_query.execute()
            candidates = bbox_result.data or []

            # Precise filter using haversine distance
            def haversine_m(lat1, lon1, lat2, lon2):
                R = 6371000.0
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
                return 2 * R * math.asin(math.sqrt(a))

            citations = []
            for c in candidates:
                try:
                    clat = float(c.get('latitude'))
                    clon = float(c.get('longitude'))
                except (TypeError, ValueError):
                    continue
                if haversine_m(lat, lon, clat, clon) <= radius_m:
                    citations.append(c)

        else:
            return jsonify({'status': 'error', 'error': 'invalid mode'}), 400

        # Only include rows with valid coordinates for map display consistency
        citations_with_coords = [c for c in citations if c.get('latitude') and c.get('longitude')]

        # Determine most recent issue date
        most_recent_time = None
        for c in citations_with_coords:
            d = c.get('issue_date')
            if d and (most_recent_time is None or d > most_recent_time):
                most_recent_time = d

        return jsonify({
            'status': 'success',
            'citations': citations_with_coords,
            'count': len(citations_with_coords),
            'most_recent_citation_time': most_recent_time
        })
    except Exception as e:
        import traceback
        logger.error(f"Error in search_citations: {e}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/stats')
def stats():
    """Get scraper statistics"""
    try:
        db_manager = get_db_manager()
        
        # Get total citations count using Supabase client
        total_citations_response = db_manager.supabase.from_('citations').select('count', count='exact').execute()
        total_citations = total_citations_response.count if total_citations_response.count is not None else 0
        
        # Get last successful citation
        last_citation = db_manager.get_last_successful_citation()
        
        # Get recent activity (citations scraped in last hour)
        from datetime import datetime, timedelta
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        recent_citations_response = db_manager.supabase.from_('citations').select('count', count='exact').gte('scraped_at', one_hour_ago).execute()
        recent_citations = recent_citations_response.count if recent_citations_response.count is not None else 0
                
        # Get cloud storage stats
        cloud_storage = StorageFactory.create_storage_service()
        storage_stats = db_manager.get_storage_stats()
        
        return jsonify({
            'total_citations': total_citations,
            'last_successful_citation': last_citation,
            'recent_citations_1h': recent_citations,
            'scraper_status': 'active',
            'cloud_storage': {
                'configured': cloud_storage.is_configured() if cloud_storage else False,
                'provider': os.getenv('STORAGE_PROVIDER', 'cloudflare_r2'),
                'total_images': storage_stats.get('total_images', 0),
                'total_size_mb': storage_stats.get('total_mb', 0),
                'citations_with_images': storage_stats.get('citations_with_images', 0)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """Create or upsert a subscription to notifications.

    Supports two modes:
      - Plate: { plate_state, plate_number }
      - Location: { center_lat, center_lon, radius_m }

    JSON body must include one of the above groups, plus email.
    """
    try:
        payload = request.get_json(force=True, silent=False) or {}
        plate_state = (payload.get('plate_state') or '').strip().upper()
        plate_number = (payload.get('plate_number') or '').strip()
        email = (payload.get('email') or '').strip() or None
        if not email:
            return jsonify({'status': 'error', 'error': 'email is required'}), 400

        db_manager = get_db_manager()
        # Plate subscription
        if plate_state and plate_number:
            result = db_manager.add_subscription(plate_state, plate_number, email=email)
            return jsonify({'status': 'success', 'subscription': result.get('data')}), 200

        # Location subscription
        try:
            center_lat = float(payload.get('center_lat')) if payload.get('center_lat') is not None else None
            center_lon = float(payload.get('center_lon')) if payload.get('center_lon') is not None else None
            radius_m = float(payload.get('radius_m')) if payload.get('radius_m') is not None else None
        except ValueError:
            return jsonify({'status': 'error', 'error': 'center_lat, center_lon, and radius_m must be numbers'}), 400

        if center_lat is not None and center_lon is not None and radius_m is not None:
            result = db_manager.add_location_subscription(center_lat, center_lon, radius_m, email=email)
            return jsonify({'status': 'success', 'subscription': result.get('data')}), 200

        return jsonify({'status': 'error', 'error': 'provide either plate_state+plate_number or center_lat+center_lon+radius_m'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    """Deactivate a subscription matching the plate or location and email."""
    try:
        payload = request.get_json(force=True, silent=False) or {}
        plate_state = (payload.get('plate_state') or '').strip().upper()
        plate_number = (payload.get('plate_number') or '').strip()
        email = (payload.get('email') or '').strip() or None

        if not email:
            return jsonify({'status': 'error', 'error': 'email is required'}), 400

        db_manager = get_db_manager()
        if plate_state and plate_number:
            result = db_manager.deactivate_subscription(plate_state, plate_number, email=email)
            return jsonify({'status': 'success', 'unsubscribed': result.get('data')}), 200

        try:
            center_lat = float(payload.get('center_lat')) if payload.get('center_lat') is not None else None
            center_lon = float(payload.get('center_lon')) if payload.get('center_lon') is not None else None
            radius_m = float(payload.get('radius_m')) if payload.get('radius_m') is not None else None
        except ValueError:
            return jsonify({'status': 'error', 'error': 'center_lat, center_lon, and radius_m must be numbers'}), 400

        if center_lat is not None and center_lon is not None and radius_m is not None:
            result = db_manager.deactivate_location_subscription(center_lat, center_lon, radius_m, email=email)
            return jsonify({'status': 'success', 'unsubscribed': result.get('data')}), 200

        return jsonify({'status': 'error', 'error': 'provide either plate_state+plate_number or center_lat+center_lon+radius_m'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
