# Ann Arbor Parking Citation Scraper

An automated scraper that collects parking citations from Ann Arbor's citation portal and runs continuously on Render's free tier.

## 🚀 Quick Start

1. **Deploy to Render**: Follow instructions in [docs/DEPLOYMENT_INSTRUCTIONS.md](docs/DEPLOYMENT_INSTRUCTIONS.md)
2. **Configure Environment**: Set up Supabase and email credentials
3. **Monitor**: Check logs and receive email notifications

## 📁 Project Structure

```
├── src/                    # Core application code
│   ├── main_combined.py   # Main scraper + web server
│   ├── scraper.py         # Citation scraping logic
│   ├── db_manager.py      # Database operations
│   ├── email_notifier.py  # Email notifications
│   └── web_server.py      # Health check endpoints
├── scripts/               # Utility scripts
├── docs/                  # Documentation and schemas
├── logs/                  # Log files
├── images/               # Downloaded citation images
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment config
└── Dockerfile          # Container configuration
```

## ⚙️ Features

- **Automated Scraping**: Runs every 10 minutes
- **Smart Range**: Processes citations ±100 from last successful citation
- **Email Notifications**: HTML reports sent to ammarat@umich.edu
- **Database Storage**: Supabase PostgreSQL for persistent storage
- **Health Monitoring**: Web endpoints for status checks
- **Respectful Scraping**: Includes delays to be respectful to target server

## 🔧 Configuration

See [env.template](env.template) for required environment variables.

## 📊 Monitoring

- **Health Check**: `GET /` - Service status
- **Statistics**: `GET /stats` - Scraper statistics
- **Email Reports**: Automatic notifications after each run

## 💰 Cost

This setup uses only free tiers:
- **Render**: Free (750 hours/month)
- **Supabase**: Free (500MB database)
- **Total Cost**: $0/month

## 📚 Documentation

- [Deployment Instructions](docs/DEPLOYMENT_INSTRUCTIONS.md)
- [Database Schema](docs/schema.sql)
- [OCR Enhancement Scripts](scripts/)

## 🛠️ Development

For local development, install dependencies and run:

```bash
pip install -r requirements.txt
python main.py
```

## 📄 License

This project is for educational and research purposes.