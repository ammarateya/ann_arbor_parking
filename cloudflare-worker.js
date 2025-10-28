// Cloudflare Worker for ammarateya.com/a2-parking
// This proxies requests to the Render service

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // Handle API routes first - proxy directly to Render
  if (url.pathname.startsWith("/api/")) {
    const renderUrl = `https://ann-arbor-parking.onrender.com${url.pathname}${url.search}`;
    console.log(`Proxying API: ${url.pathname} to ${renderUrl}`);

    // Clone headers and add CORS if needed
    const headers = new Headers(request.headers);

    const response = await fetch(renderUrl, {
      method: request.method,
      headers: headers,
      body: request.body,
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("Access-Control-Allow-Origin", "*");
    responseHeaders.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    responseHeaders.set("Access-Control-Allow-Headers", "Content-Type");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  }

  // Redirect /a2-parking to /a2-parking/ if no trailing slash
  if (url.pathname === "/a2-parking") {
    return Response.redirect(url + "/", 301);
  }

  // This Worker only handles /a2-parking routes (configured in Cloudflare Dashboard)
  // Rewrite the path to remove /a2-parking prefix
  let renderPath = url.pathname.replace("/a2-parking", "");

  // Handle trailing slashes properly
  if (renderPath === "") {
    renderPath = "/";
  }

  const renderUrl = `https://ann-arbor-parking.onrender.com${renderPath}${url.search}`;

  console.log(`Proxying ${url.pathname} to ${renderUrl}`);

  // Forward the request to Render
  const response = await fetch(renderUrl, {
    method: request.method,
    headers: request.headers,
    body: request.body,
  });

  // Get response body to modify if needed
  let body = await response.arrayBuffer();

  // If HTML response, we might need to rewrite URLs (but for now just proxy as-is)
  const headers = new Headers(response.headers);

  // Return the response with proper headers
  return new Response(body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers,
  });
}
