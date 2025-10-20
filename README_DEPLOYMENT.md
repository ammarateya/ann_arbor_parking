# Parking Citation Scraper

A Python-based scraper that automatically collects parking citations from Ann Arbor's citation portal and runs continuously on Render's free tier.

## Features

- **Automated Scraping**: Runs every 10 minutes
- **Smart Range**: Processes citations ±100 from the last successful citation
- **Email Notifications**: Sends HTML reports to ammarat@umich.edu
- **Database Storage**: Uses Supabase PostgreSQL for persistent storage
- **Health Monitoring**: Web endpoints for health checks and statistics
- **Respectful Scraping**: Includes delays to be respectful to the target server

## Quick Start

1. **Deploy to Render**: Follow the detailed instructions in `DEPLOYMENT_INSTRUCTIONS.md`
2. **Set Environment Variables**: Configure database and email settings
3. **Monitor**: Check logs and receive email notifications

## Files

- `main_combined.py` - Main application (scraper + web server)
- `scraper.py` - Citation scraping logic
- `db_manager.py` - Database operations
- `email_notifier.py` - Email notification system
- `web_server.py` - Health check endpoints
- `render.yaml` - Render deployment configuration
- `requirements.txt` - Python dependencies

## Environment Variables

See `env.template` for required environment variables.

## Database Schema

The application automatically creates these tables:

- `citations` - Stores citation data
- `scraper_state` - Tracks last successful citation
- `scrape_logs` - Logs scraping attempts
- `citation_images` - Image URL tracking

## Monitoring

- **Health Check**: `GET /` - Service status
- **Statistics**: `GET /stats` - Scraper statistics
- **Email Reports**: Automatic notifications after each run

## Free Tier Usage

- **Render**: 750 hours/month (sufficient for continuous operation)
- **Supabase**: 500MB database, 2GB bandwidth
- **Total Cost**: $0/month

## Support

For issues or questions, check the deployment instructions or service logs.
