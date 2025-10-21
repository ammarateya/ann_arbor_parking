from flask import Flask, jsonify
import os
from db_manager import DatabaseManager
from storage_factory import StorageFactory

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}

@app.route('/')
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
        recent_citations_response = db_manager.supabase.from_('citations').select('count', count='exact').gte('scraped_at', 'now() - interval \'1 hour\'').execute()
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
