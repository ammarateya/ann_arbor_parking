from flask import Flask, jsonify, render_template
import os
import logging
from db_manager import DatabaseManager
from storage_factory import StorageFactory

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}

@app.route('/')
def index():
    """Main map page"""
    return render_template('map.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        db_manager = DatabaseManager(DB_CONFIG)
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
        db_manager = DatabaseManager(DB_CONFIG)
        
        # Try to get all citations that have a location field
        # Use postgrest syntax for row selection
        try:
            # First try with regular query
            result = db_manager.supabase.table('citations').select('*').not_.is_('location', 'null').execute()
            citations = result.data if result.data else []
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
                    result = service_client.table('citations').select('*').not_.is_('location', 'null').execute()
                    citations = result.data if result.data else []
                else:
                    citations = []
            else:
                # Fallback: return empty list with helpful error
                return jsonify({
                    'status': 'error',
                    'error': 'Database query requires authentication. Please set SUPABASE_SERVICE_ROLE_KEY in your environment variables to bypass Row Level Security.',
                    'citations': [],
                    'count': 0
                }), 200  # Return 200 with empty data instead of error
        
        # Filter out citations without coordinates (they need to be geocoded on frontend)
        citations_with_coords = [c for c in citations if c.get('latitude') and c.get('longitude')]
        
        # Group by location and return citations
        return jsonify({
            'status': 'success',
            'citations': citations_with_coords,
            'count': len(citations_with_coords),
            'total': len(citations)
        })
    except Exception as e:
        import traceback
        logger.error(f"Error in get_citations: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'tip': 'Check that SUPABASE_SERVICE_ROLE_KEY is set for reading data'
        }), 500

@app.route('/stats')
def stats():
    """Get scraper statistics"""
    try:
        db_manager = DatabaseManager(DB_CONFIG)
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
