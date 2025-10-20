# Parking Citation Scraper - Render Deployment Instructions

## Overview

This project scrapes parking citations from Ann Arbor's citation portal and runs every 10 minutes on Render's free tier. It uses Supabase for the database and sends email notifications to ammarat@umich.edu.

## Prerequisites

1. GitHub repository with your code
2. Render account (free tier)
3. Supabase account (free tier)
4. Gmail account with App Password for email notifications

## Step 1: Set up Supabase Database

### Database Details:

- **Project ID**: kctfygcpobxjgpivujiy
- **URL**: https://kctfygcpobxjgpivujiy.supabase.co
- **Database Host**: db.kctfygcpobxjgpivujiy.supabase.co
- **Anon Key**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjdGZ5Z2Nwb2J4amdwaXZ1aml5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5MDAwODIsImV4cCI6MjA3NDQ3NjA4Mn0.vj02ZMtMfDDJXaVDZR9ZCj72moRzYtqKEl2GWEket7U

### Get Database Password:

1. Go to https://app.supabase.com/project/kctfygcpobxjgpivujiy/settings/database
2. Copy the database password (you'll need this for Render)

## Step 2: Set up Gmail App Password

1. Go to your Google Account settings
2. Enable 2-Factor Authentication if not already enabled
3. Go to Security → App passwords
4. Generate a new app password for "Mail"
5. Save this password (you'll need it for Render)

## Step 3: Deploy to Render

### Option A: Using Render Dashboard (Recommended)

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: parking-citation-scraper
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free

### Option B: Using render.yaml (Alternative)

1. Push your code to GitHub
2. Go to https://dashboard.render.com
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Select the render.yaml file

## Step 4: Configure Environment Variables

In your Render service dashboard, go to Environment and add these variables:

### Required Variables:

```
DB_HOST=db.kctfygcpobxjgpivujiy.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[Your Supabase database password]
DB_PORT=5432
SUPABASE_URL=https://kctfygcpobxjgpivujiy.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjdGZ5Z2Nwb2J4amdwaXZ1aml5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5MDAwODIsImV4cCI6MjA3NDQ3NjA4Mn0.vj02ZMtMfDDJXaVDZR9ZCj72moRzYtqKEl2GWEket7U
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=ammarat@umich.edu
EMAIL_PASSWORD=[Your Gmail App Password]
NOTIFICATION_EMAIL=ammarat@umich.edu
```

## Step 5: Deploy and Monitor

1. Click "Deploy" in Render
2. Wait for the build to complete
3. Check the logs to ensure the scraper starts successfully
4. The service will run continuously and scrape citations every 10 minutes

## Step 6: Verify Database Schema

Once the service is running, the database schema will be automatically created. You can verify this by:

1. Going to https://app.supabase.com/project/kctfygcpobxjgpivujiy/editor
2. Checking that the following tables exist:
   - `citations`
   - `scraper_state`
   - `scrape_logs`
   - `citation_images`

## How It Works

1. **Scheduling**: The scraper runs every 10 minutes using Python's `schedule` library
2. **Range**: Each run processes citations ±100 from the last successful citation found
3. **Database**: Uses Supabase PostgreSQL for persistent storage
4. **Notifications**: Sends HTML email reports to ammarat@umich.edu with:
   - Number of citations processed
   - List of successful citations found
   - Any errors encountered
5. **Respectful Scraping**: Includes delays between requests to be respectful to the target server

## Monitoring

- **Render Logs**: Check the service logs in Render dashboard
- **Email Reports**: You'll receive email notifications after each run
- **Database**: Query the Supabase database to see collected citations

## Free Tier Limitations

- **Render**: 750 hours/month (enough for continuous operation)
- **Supabase**: 500MB database, 2GB bandwidth
- **Email**: Gmail's standard limits apply

## Troubleshooting

1. **Service won't start**: Check environment variables are set correctly
2. **Database connection issues**: Verify Supabase project is active and password is correct
3. **Email not sending**: Check Gmail App Password is correct
4. **No citations found**: Check if the citation portal is accessible

## Cost

This setup uses only free tiers:

- Render: Free (750 hours/month)
- Supabase: Free (500MB database)
- Gmail: Free (with App Password)

Total cost: $0/month
