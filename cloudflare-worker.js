// Cloudflare Worker for ammarateya.com/a2-parking
// This proxies requests to the Render service

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

    // Clone response to modify if needed
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  // For all other routes, pass through to your GitHub Pages site
  // or return 404 if you want
  return fetch(request);
}
