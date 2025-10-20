# Cloudflare R2 Setup Guide

## ✅ Your NEW R2 Credentials

Based on your new Cloudflare R2 API key, here are your credentials:

### Environment Variables for Render:

```bash
STORAGE_PROVIDER=cloudflare_r2
R2_ACCESS_KEY_ID=your_r2_access_key_id_here
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key_here
R2_ACCOUNT_ID=your_r2_account_id_here
R2_BUCKET_NAME=parking-citations
```

## 🚀 Next Steps

### 1. Create R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **R2 Object Storage**
3. Click **Create bucket**
4. Name it: `parking-citations`
5. Choose **US East** region (or your preference)
6. Click **Create bucket**

### 2. Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Create new **Web Service**
3. Connect your GitHub repo: `ammarateya/ann_arbor_parking`
4. Set these environment variables:

#### Required Environment Variables:

```
STORAGE_PROVIDER=cloudflare_r2
R2_ACCESS_KEY_ID=your_r2_access_key_id_here
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key_here
R2_ACCOUNT_ID=your_r2_account_id_here
R2_BUCKET_NAME=parking-citations
DB_HOST=db.kctfygcpobxjgpivujiy.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[Get from Supabase dashboard]
DB_PORT=5432
EMAIL_USER=ammarat@umich.edu
EMAIL_PASSWORD=[Gmail App Password]
NOTIFICATION_EMAIL=ammarat@umich.edu
```

### 3. Deploy Settings

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Plan**: Free

## 🎯 What Happens Next

Once deployed, your scraper will:

1. ✅ **Run every 10 minutes**
2. ✅ **Process citations ±100 from last successful**
3. ✅ **Download and compress images** (60-80% size reduction)
4. ✅ **Upload compressed images to R2**
5. ✅ **Send email reports** with upload statistics
6. ✅ **Store metadata** in Supabase database

## 📊 Expected Results

With image compression:

- **700MB → ~140MB** for your current citations
- **10GB R2 storage** = ~7,000 citations with images
- **No egress fees** for image downloads
- **Reliable storage** with Cloudflare's global network

## 🔍 Monitoring

- **Health Check**: `https://your-app.onrender.com/`
- **Statistics**: `https://your-app.onrender.com/stats`
- **Email Reports**: Automatic notifications to ammarat@umich.edu

## 🛠️ Troubleshooting

If you encounter issues:

1. **Check R2 bucket exists** and is accessible
2. **Verify environment variables** are set correctly
3. **Check Render logs** for error messages
4. **Test R2 connection** using the `/stats` endpoint

Your scraper is now ready to efficiently store compressed citation images in Cloudflare R2! 🚀
