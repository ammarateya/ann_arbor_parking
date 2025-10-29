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
- **Subscriber notifications**: email and/or webhook when your plate appears
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

### Email/Webhook Alerts

- The scraper checks for matching active subscriptions when saving a new citation and sends:
  - An individual email (if `EMAIL_*` env vars are configured)
  - A JSON POST to the provided `webhook_url`

Notes:

- For subscriber emails, the app uses the same SMTP credentials as the daily report. Set `EMAIL_*` accordingly.
- Apply DB changes for subscriptions by running the SQL in `docs/alter_schema_ocr.sql` on your Supabase database (idempotent).

### 3. Deploy API to Render

The API will automatically deploy when you push to main branch.

## 📡 API Endpoints

- `GET /` - Map UI
- `GET /about` - About
- `GET /api/health` - Health
- `GET /api/citations` - Map data
- `GET /api/search` - Search by plate, citation, or location
- `GET /stats` - Scraper statistics and storage info
- `POST /api/subscribe` - Body: plate OR location plus contact
  - Plate: `{ plate_state, plate_number, email? , webhook_url? }`
  - Location: `{ center_lat, center_lon, radius_m, email? , webhook_url? }`
- `POST /api/unsubscribe` - Body mirrors subscribe

At least one of `email` or `webhook_url` is required.

### Gmail API (optional, if SMTP doesn’t work)

- Install extras (already in `requirements.txt`): `google-api-python-client`, `google-auth`, `google-auth-oauthlib`.
- Create OAuth client (Desktop) and generate a token file with scope `gmail.send`.
- Set env vars:
  - `FROM_EMAIL` (sender address)
  - `GMAIL_TOKEN_FILE` (default `gmail_token.json`)
    The app will try SMTP first; if not configured, it will fall back to Gmail API.

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
