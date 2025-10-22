# Ann Arbor Parking Citation Scraper

A real-time parking citation scraper and API for Ann Arbor, Michigan.

## 🚀 Architecture

- **Scraper**: Runs every 10 minutes via GitHub Actions (free for public repos)
- **API**: Hosted on Render for health checks and statistics
- **Database**: Supabase PostgreSQL
- **Storage**: Cloudflare R2 for citation images

## 📊 Features

- **Real-time scraping** every 10 minutes
- **OCR address extraction** for clean street addresses
- **Image storage** with compression
- **Email notifications** with citation summaries
- **REST API** for health checks and statistics
- **Bulk optimization** to avoid duplicate processing

## 🔧 Setup

### 1. Make Repository Public
This enables free GitHub Actions (unlimited minutes for public repos).

### 2. Add GitHub Secrets
Go to **Settings** → **Secrets and variables** → **Actions** and add:

```
DB_HOST=db.kctfygcpobxjgpivujiy.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_password
DB_PORT=5432
SUPABASE_URL=https://kctfygcpobxjgpivujiy.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=ammarat@umich.edu
EMAIL_PASSWORD=your_gmail_app_password
NOTIFICATION_EMAIL=ammarat@umich.edu
STORAGE_PROVIDER=cloudflare_r2
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_ACCOUNT_ID=your_r2_account_id
R2_BUCKET_NAME=parking-citations
R2_PUBLIC_URL=https://your-domain.com
IMAGE_MAX_WIDTH=1200
IMAGE_MAX_HEIGHT=1200
IMAGE_QUALITY=85
IMAGE_FORMAT=JPEG
```

### 3. Deploy API to Render
The API will automatically deploy when you push to main branch.

## 📡 API Endpoints

- `GET /` - Health check
- `GET /stats` - Scraper statistics and storage info

## 🔄 GitHub Actions

The scraper runs automatically:
- **Every 10 minutes** via cron schedule
- **On push** to main branch (for testing)
- **Manual trigger** available in GitHub Actions tab

## 📈 Performance

- **Bulk citation lookup** - 1 query instead of 200+ per session
- **Skip existing citations** - no duplicate processing
- **Image compression** - optimized storage usage
- **OCR optimization** - clean address extraction

## 🛠️ Tech Stack

- **Python 3.11**
- **Supabase** (PostgreSQL + Python client)
- **Cloudflare R2** (S3-compatible storage)
- **GitHub Actions** (cron jobs)
- **Render** (API hosting)
- **Flask** (web framework)
- **Pillow** (image processing)
- **pytesseract** (OCR)

## 📝 License

MIT License - Feel free to use for civic tech projects!