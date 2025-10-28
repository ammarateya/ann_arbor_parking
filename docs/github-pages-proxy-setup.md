# Setting up a2-parking subdirectory on GitHub Pages

Since your apex domain `ammarateya.com` is hosted on GitHub Pages, here's how to add the parking map app at `/a2-parking`:

## Option 1: Use a subdomain instead (easier, no changes needed)

Create a subdomain like:
- `parking.ammarateya.com`

**Steps:**
1. In Render, add custom domain: Settings → Custom Domains → Add `parking.ammarateya.com`
2. In your DNS settings for `ammarateya.com`, add a CNAME record:
   - Name: `parking`
   - Value: `ann-arbor-parking.onrender.com`
3. Done! Your app will be at `https://parking.ammarateya.com`

## Option 2: GitHub Pages can't proxy to external services

GitHub Pages is static-only and can't do reverse proxying. If you want `/a2-parking` as a subdirectory:

### Workaround: Use Cloudflare Workers (Free)

1. **Move your domain to Cloudflare:**
   - Go to Cloudflare.com and add `ammarateya.com`
   - Update your nameservers at your DNS provider
   - Cloudflare is free and keeps your existing DNS settings

2. **Create a Worker:**
   - In Cloudflare Dashboard → Workers & Pages
   - Create a new Worker with this code:

```javascript
addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  
  // Handle /a2-parking route
  if (url.pathname.startsWith("/a2-parking")) {
    const renderUrl = `https://ann-arbor-parking.onrender.com${url.pathname.replace(
      "/a2-parking",
      ""
    )}${url.search}`;
    
    return fetch(renderUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
  }
  
  // Pass through all other requests to GitHub Pages
  return fetch(request);
}
```

3. **Route your domain:**
   - Go to Cloudflare Dashboard → Workers & Pages → Your domain
   - Add a route: `ammarateya.com/a2-parking/*` → Your Worker

### Option 3: Keep It Simple - Use Render's URL

Just use `https://ann-arbor-parking.onrender.com` directly, or create a simple redirect page on your main site.

