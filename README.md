# Ann Arbor Parking Citation Scraper

An automated scraper that collects parking citations from Ann Arbor's citation portal, runs continuously on Render's free tier, and stores images with smart compression in cloud storage.

## 🚀 Quick Start

1. **Deploy to Render**: Follow instructions in [docs/DEPLOYMENT_INSTRUCTIONS.md](docs/DEPLOYMENT_INSTRUCTIONS.md)
2. **Choose Storage Provider**: Configure your preferred cloud storage
3. **Configure Environment**: Set up database and email credentials
4. **Monitor**: Check logs and receive email notifications

## 📁 Project Structure

```
├── src/                    # Core application code
│   ├── main_combined.py   # Main scraper + web server
│   ├── scraper.py         # Citation scraping logic
│   ├── db_manager.py      # Database operations
│   ├── email_notifier.py  # Email notifications
│   ├── backblaze_storage.py # Backblaze B2 storage
│   ├── cloud_storage.py   # Cloudflare R2 & Google Cloud
│   ├── image_compressor.py # Image compression service
│   ├── storage_factory.py # Storage provider factory
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
- **Image Compression**: Reduces storage by 60-80% with smart compression
- **Multiple Storage Options**: Backblaze B2, Cloudflare R2, Google Cloud
- **Email Notifications**: HTML reports sent to ammarat@umich.edu
- **Database Storage**: Supabase PostgreSQL for persistent storage
- **Health Monitoring**: Web endpoints for status checks
- **Respectful Scraping**: Includes delays to be respectful to target server

## 🗄️ Storage Options

### 🏆 **Cloudflare R2 (RECOMMENDED)**
- **Free Tier**: 10GB storage + 1M requests/month
- **Pros**: No egress fees, S3-compatible, reliable
- **Best For**: Production applications
- **Setup**: Create R2 bucket, get API keys

### 🎓 **Google Cloud Storage (Student Credits)**
- **Free Tier**: $300 credits (~1.5TB storage)
- **Pros**: Large free tier, reliable, good integration
- **Best For**: Students with .edu email
- **Setup**: Apply for student credits, create service account

### 💾 **Backblaze B2**
- **Free Tier**: 10GB storage
- **Pros**: Simple setup, good performance
- **Cons**: Limited free tier, egress fees
- **Best For**: Small projects

## 🗜️ Image Compression

All images are automatically compressed to reduce storage costs:
- **Resize**: Max 1200x1200 pixels
- **Quality**: 85% JPEG quality
- **Format**: Converted to JPEG for consistency
- **Savings**: Typically 60-80% size reduction

## 🔧 Configuration

### Environment Variables

```bash
# Storage Provider (choose one)
STORAGE_PROVIDER=cloudflare_r2  # Options: backblaze_b2, cloudflare_r2, google_cloud

# Cloudflare R2 (RECOMMENDED)
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_ACCOUNT_ID=your_r2_account_id
R2_BUCKET_NAME=parking-citations

# Google Cloud Storage (Student credits)
GCS_BUCKET_NAME=parking-citations
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Backblaze B2
B2_APPLICATION_KEY_ID=your_b2_application_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET_NAME=parking-citations

# Image Compression Settings
IMAGE_MAX_WIDTH=1200
IMAGE_MAX_HEIGHT=1200
IMAGE_QUALITY=85
```

## 📊 Monitoring

- **Health Check**: `GET /` - Service status
- **Statistics**: `GET /stats` - Scraper and storage statistics
- **Email Reports**: Automatic notifications after each run

## 💰 Cost Analysis

### With Image Compression (Recommended):
- **700MB → ~140MB** (80% reduction)
- **10GB storage** = ~7,000 citations with images
- **Cloudflare R2**: Free tier covers ~7,000 citations
- **Google Cloud**: Student credits cover ~10,000+ citations

### Storage Providers Comparison:
| Provider | Free Tier | Egress Fees | Best For |
|----------|-----------|-------------|----------|
| Cloudflare R2 | 10GB + 1M requests | None | Production |
| Google Cloud | $300 credits | Yes | Students |
| Backblaze B2 | 10GB | Yes | Small projects |

## 🛠️ Development

For local development:

```bash
pip install -r requirements.txt
python main.py
```

## 📚 Documentation

- [Deployment Instructions](docs/DEPLOYMENT_INSTRUCTIONS.md)
- [Database Schema](docs/schema.sql)
- [Storage Setup Guide](docs/STORAGE_SETUP.md)

## 🎯 Getting Started with Cloudflare R2

1. **Create Account**: Sign up at [Cloudflare](https://dash.cloudflare.com/)
2. **Enable R2**: Go to R2 Object Storage
3. **Create Bucket**: Name it `parking-citations`
4. **Get API Keys**: Create R2 Token with read/write permissions
5. **Set Environment Variables**: Add R2 credentials to Render
6. **Deploy**: Your scraper will automatically use R2!

## 📄 License

This project is for educational and research purposes.# Force fresh deployment Mon Oct 20 20:08:49 EDT 2025
# Trigger deployment Mon Oct 20 20:13:24 EDT 2025
# Test deployment Mon Oct 20 20:42:01 EDT 2025
