i# Step-by-Step: Add Cloudflare Worker for a2-parking

## Step 1: Sign up / Log in to Cloudflare (Free)

1. Go to [cloudflare.com](https://cloudflare.com) and sign up (or log in)
2. Click "Add a site"
3. Enter: `ammarateya.com`
4. Cloudflare will scan your current DNS records and import them
5. They'll give you 2 nameservers to update at your DNS provider

## Step 2: Update Nameservers

1. Go to your domain registrar (where you bought `ammarateya.com`)
2. Find "Nameservers" or "DNS Settings"
3. Replace with Cloudflare's nameservers (e.g., `lenora.ns.cloudflare.com`)
4. Save - this takes 5-30 minutes to propagate

Your site keeps working! All your DNS records stay the same.

## Step 3: Create the Worker

### Option A: Using Cloudflare Dashboard (Easiest)

1. Go to [Workers & Pages](https://dash.cloudflare.com) in Cloudflare Dashboard
2. Click "Create application" → **"Create Worker"** (NOT "Create Worker Site")
3. Name it: `a2-parking-worker`
4. Click "Deploy"
5. Click "Edit code" in the deployed Worker
6. Replace the code with this:

```javascript
addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // Handle /a2-parking route - proxy to Render
  if (url.pathname.startsWith("/a2-parking")) {
    // Rewrite the path to remove /a2-parking prefix
    const renderPath = url.pathname.replace("/a2-parking", "") || "/";
    const renderUrl = `https://ann-arbor-parking.onrender.com${renderPath}${url.search}`;

    // Forward the request to Render
    const response = await fetch(renderUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  // For all other routes, pass through
  return fetch(request);
}
```

7. Click "Save and Deploy"

### Option B: Using Wrangler CLI (Advanced)

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create new Worker
wrangler init a2-parking-worker

# Copy the code from cloudflare-worker.js to src/index.js
# Then deploy
wrangler publish
```

## Step 4: Add Custom Domain Route (REQUIRED!)

1. In Cloudflare Dashboard → Select your domain `ammarateya.com` (not the Worker)
2. Go to **Workers & Pages** tab (left sidebar)
3. Click **"Add route"** button
4. Route: `ammarateya.com/a2-parking/*`
5. Worker: Select `a2-parking-worker`
6. Click **"Save"**

⚠️ **Without this step, the Worker won't work!**

## Step 5: Test!

Visit: `https://ammarateya.com/a2-parking`

You should see your parking map app!

## Troubleshooting

- **"No route found"**: Make sure the route is `ammarateya.com/a2-parking/*` (with the wildcard)
- **CORS errors**: The Worker forwards headers correctly
- **Assets not loading**: Check that your app uses relative paths (should work)

## What You Get

✅ Your main site at `ammarateya.com` (GitHub Pages) stays the same
✅ Your parking app at `ammarateya.com/a2-parking`
✅ Free SSL on both
✅ All Cloudflare features (CDN, DDoS protection, etc.)

**Total cost: $0**
