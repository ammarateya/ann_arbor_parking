function closeSidePanel() {
  const panel = document.getElementById("sidePanel");
  panel.classList.remove("active");

  // Hide citation title
  const citationTitle = document.getElementById("citationTitle");
  if (citationTitle) citationTitle.style.display = "none";

  // Check if mobile
  const isMobile =
    window.matchMedia && window.matchMedia("(max-width: 768px)").matches;
  if (isMobile) {
    document.body.classList.remove("mobile-panel-open");
  } else {
    document.body.classList.remove("panel-open");
  }
  closeCitationPopup();
  closeSidePanelGallery();
  
  // Clear URL deep link if present
  if (window.location.pathname.includes('/citation/')) {
    window.history.pushState({}, '', '/');
  }
}

// #region agent log (debug)
(function agentLogLayoutOnLoad() {
  try {
    const isMobileMq =
      window.matchMedia && window.matchMedia("(max-width: 768px)").matches;
    const searchBar = document.querySelector(".search-bar");
    const sidePanel = document.getElementById("sidePanel");
    const searchBarRect = searchBar ? searchBar.getBoundingClientRect() : null;
    const sidePanelRect = sidePanel ? sidePanel.getBoundingClientRect() : null;
    const searchBarStyle = searchBar
      ? window.getComputedStyle(searchBar)
      : null;
    const sidePanelStyle = sidePanel
      ? window.getComputedStyle(sidePanel)
      : null;

    fetch("http://127.0.0.1:7242/ingest/e36ef556-bd8a-4e44-88f5-708e512b1239", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: "debug-session",
        runId: "pre-fix",
        hypothesisId: "H1",
        location: "static/js/map.js:agentLogLayoutOnLoad",
        message: "layout snapshot on load",
        data: {
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          isMobileMq,
          searchBarRect: searchBarRect
            ? {
                w: searchBarRect.width,
                h: searchBarRect.height,
                x: searchBarRect.x,
                y: searchBarRect.y,
              }
            : null,
          searchBarCss: searchBarStyle
            ? {
                width: searchBarStyle.width,
                maxWidth: searchBarStyle.maxWidth,
                flex: searchBarStyle.flex,
              }
            : null,
          sidePanelRect: sidePanelRect
            ? {
                w: sidePanelRect.width,
                h: sidePanelRect.height,
                x: sidePanelRect.x,
                y: sidePanelRect.y,
              }
            : null,
          sidePanelCss: sidePanelStyle
            ? {
                width: sidePanelStyle.width,
                height: sidePanelStyle.height,
                top: sidePanelStyle.top,
                bottom: sidePanelStyle.bottom,
                position: sidePanelStyle.position,
              }
            : null,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  } catch (e) {}
})();
// #endregion agent log (debug)

// ... existing code ...

// Close side panel gallery
let sidePanelGalleryKeyHandler = null;
function closeSidePanelGallery() {
  const sidePanel = document.getElementById("sidePanel");
  const sidePanelContent = document.getElementById("sidePanelContent");
  const sidePanelGallery = document.getElementById("sidePanelGallery");
  const rightViewer = document.getElementById("rightImageViewer");

  if (sidePanelContent) sidePanelContent.style.display = "block";
  if (sidePanelGallery) {
    sidePanelGallery.style.display = "none";
    // Remove keyboard handler if it exists
    if (sidePanelGalleryKeyHandler) {
      document.removeEventListener("keydown", sidePanelGalleryKeyHandler);
      sidePanelGalleryKeyHandler = null;
    }
  }

  // Hide right-side viewer and show map
  if (rightViewer) {
    rightViewer.style.display = "none";
    document.body.classList.remove("right-viewer-active");
  }

  // Remove gallery-mode class
  if (sidePanel) {
    sidePanel.classList.remove("gallery-mode");
    // Ensure panel is expanded when returning from gallery
    if (sidePanel.classList.contains("collapsed")) {
        toggleSidePanelCollapse();
    }
  }

  // Restore hamburger menu icon
  const searchMenuBtn = document.getElementById("searchMenuBtn");
  if (searchMenuBtn) {
    // Remove the gallery back handler
    if (searchMenuBtn._galleryBackHandler) {
      searchMenuBtn.removeEventListener("click", searchMenuBtn._galleryBackHandler);
      searchMenuBtn._galleryBackHandler = null;
    }
    // Restore original hamburger icon
    if (searchMenuBtn._originalHTML) {
      searchMenuBtn.innerHTML = searchMenuBtn._originalHTML;
      searchMenuBtn.title = "Menu";
    }
  }

  sidePanelGalleryImages = [];
  sidePanelGalleryCitation = null;
  sidePanelGalleryIndex = 0;
}
// Initialize map centered on Ann Arbor with performance optimizations
console.log("[map.js] script loaded");

// Helper function to format dollar amount with SVG icon
function formatDollarAmount(amount) {
  const formatted = amount.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  const dollarIcon = '<svg xmlns="http://www.w3.org/2000/svg" height="14px" viewBox="0 -960 960 960" width="14px" fill="currentColor"><path d="M441-120v-86q-53-12-91.5-46T293-348l74-30q15 48 44.5 73t77.5 25q41 0 69.5-18.5T587-356q0-35-22-55.5T463-458q-86-27-118-64.5T313-614q0-65 42-101t86-41v-84h80v84q50 8 82.5 36.5T651-650l-74 32q-12-32-34-48t-60-16q-44 0-67 19.5T393-614q0 33 30 52t104 40q69 20 104.5 63.5T667-358q0 71-42 108t-104 46v84h-80Z"/></svg>';
  return dollarIcon + formatted;
}

// Define Ann Arbor bounds (roughly 15-20 miles radius)
const annArborBounds = L.latLngBounds(
  [42.15, -83.9], // Southwest corner
  [42.4, -83.6] // Northeast corner
);

const map = L.map("map", {
  zoomControl: true,
  zoom: 13,
  center: [42.2808, -83.743],
  minZoom: 11, // Don't zoom out too far
  maxZoom: 19, // Don't zoom in too close
  maxBounds: annArborBounds, // Restrict panning to Ann Arbor area
  maxBoundsViscosity: 1.0, // Hard boundary - can't pan outside
  preferCanvas: true, // Use canvas rendering for better performance
  fadeAnimation: true, // Enable smooth fade animations
  zoomAnimation: true, // Enable smooth zoom animation
  zoomAnimationThreshold: 4, // Smooth zoom for up to 4 levels
  markerZoomAnimation: true, // Enable marker zoom animation for smoothness
  // Performance optimizations
  updateWhenZooming: true, // Update during zoom for smoother experience
  updateWhenIdle: true, // Update markers when zoom/pan complete
  keepInView: false, // Don't keep markers in view during pan
  // Smooth zoom settings
  wheelPxPerZoomLevel: 60, // Smoother mouse wheel zoom
  doubleClickZoom: true,
  scrollWheelZoom: true,
});

let isDarkMode = true;
let currentTileLayer;

// Side panel closed by default

// Initialize with CARTO Voyager (Google Maps-style)
currentTileLayer = L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
  {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 20,
  }
).addTo(map);

// Icon helpers
function getSunIcon() {
  return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">\
          <circle cx="12" cy="12" r="4" fill="#00d4ff"/>\
          <g stroke="#00d4ff" stroke-width="2">\
            <line x1="12" y1="1" x2="12" y2="4"/>\
            <line x1="12" y1="20" x2="12" y2="23"/>\
            <line x1="1" y1="12" x2="4" y2="12"/>\
            <line x1="20" y1="12" x2="23" y2="12"/>\
            <line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/>\
            <line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/>\
            <line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/>\
            <line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/>\
          </g>\
        </svg>';
}

function getMoonIcon() {
  return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">\
          <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" fill="#00d4ff"/>\
        </svg>';
}

function getSearchIcon() {
  return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">\
          <circle cx="11" cy="11" r="7" stroke="#00d4ff" stroke-width="2" fill="none"/>\
          <line x1="16.5" y1="16.5" x2="22" y2="22" stroke="#00d4ff" stroke-width="2"/>\
        </svg>';
}

function getBellIcon() {
  return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">\
          <path d="M12 22a2 2 0 002-2H10a2 2 0 002 2z" fill="#00d4ff"/>\
          <path d="M18 16v-5a6 6 0 10-12 0v5l-2 2h16l-2-2z" stroke="#00d4ff" stroke-width="2" fill="none"/>\
        </svg>';
}

// Set initial theme toggle icon (action: switch to light → sun)
(function initIcons() {
  const themeBtn = document.getElementById("themeBtn");
  if (themeBtn) themeBtn.innerHTML = getSunIcon();
  const searchBtn = document.getElementById("searchToggleBtn");
  if (searchBtn) searchBtn.innerHTML = getSearchIcon();
  const notifyBtn = document.getElementById("notifyToggleBtn");
  if (notifyBtn) notifyBtn.innerHTML = getBellIcon();
})();

// Store citations data
let allCitations = []; // Store all citations from API (unfiltered)
let citations = []; // Currently visible citations (filtered)
let markers = [];
const citationToMarker = new Map();
let usedCoordinates = new Map(); // Track coordinates to avoid overlap
let currentTimeFilter = "week"; // Track current time filter - default to week view
let activeCitationPopup = null;

let isSearchActive = false;
let searchCenter = null; // {lat, lon}
let searchCircle = null;
let pendingPick = false;
let mostRecentCitationTime = null; // Store the most recent citation timestamp
let mostRecentCitationNumber = null; // Store the most recent citation number
const rootElement = document.documentElement;

function updateTopOffsets() {
  const headerEl = document.querySelector(".header");
  const timeFilterEl = document.getElementById("timeFilterBar");

  if (headerEl) {
    rootElement.style.setProperty(
      "--header-height",
      `${headerEl.offsetHeight}px`
    );
  }

  if (timeFilterEl) {
    rootElement.style.setProperty(
      "--time-filter-height",
      `${timeFilterEl.offsetHeight}px`
    );
  }
}

const scheduleTopOffsetUpdate = () =>
  window.requestAnimationFrame(updateTopOffsets);

scheduleTopOffsetUpdate();
window.addEventListener("resize", scheduleTopOffsetUpdate);
window.addEventListener("orientationchange", scheduleTopOffsetUpdate);
window.addEventListener("load", scheduleTopOffsetUpdate);

// Pre-render pin icons as data URLs for performance (one per color tier)
const pinIcons = {
  green: createPinDataURL("#34A853"),
  yellow: createPinDataURL("#FBBC04"),
  orange: createPinDataURL("#FA7B17"),
  red: createPinDataURL("#EA4335"),
};

// Create canvas icon from SVG pin
function createPinDataURL(color) {
  const svg = `<svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
          <path d="M16 0C7.16 0 0 7.16 0 16c0 8.84 16 24 16 24s16-15.16 16-24C32 7.16 24.84 0 16 0z" fill="${color}" stroke="#fff" stroke-width="2"/>
          <circle cx="16" cy="14" r="8" fill="#fff"/>
        </svg>`;
  return "data:image/svg+xml;base64," + btoa(svg);
}

// Initialize markers layer group for efficient rendering
let markersLayerGroup = L.layerGroup().addTo(map);
let allMarkersArray = [];

function clearAllMarkers() {
  markersLayerGroup.clearLayers();
  allMarkersArray = [];
  markers = [];
  citationToMarker.clear();
  usedCoordinates = new Map();
}

// Leaflet handles large numbers of markers efficiently with canvas rendering
// when preferCanvas: true is set on the map (which we have done)

// Debounce map move events to improve pan performance
let updateTimeout;
map.on("moveend", function () {
  clearTimeout(updateTimeout);
  updateTimeout = setTimeout(function () {
    // Canvas layer handles viewport efficiently, no additional action needed
  }, 150);
});

// Canvas markers work at all zoom levels, no threshold handling needed

// Disable unnecessary animations during pan/zoom for better performance
let isPanning = false;
map.on("movestart", function () {
  isPanning = true;
});
map.on("moveend", function () {
  isPanning = false;
});

// Search UI logic

function clearAllMarkers() {
  markersLayerGroup.clearLayers();
  markers = [];
  citationToMarker.clear();
  usedCoordinates = new Map();
}

async function showOnlyMarkers(list) {
  clearAllMarkers();

  // Batch marker creation for search results
  const BATCH_SIZE = 100;
  const batchMarkersToAdd = [];

  for (let i = 0; i < list.length; i++) {
    const c = list[i];
    const m = createMarkerForCitation(c);
    if (m) {
      markers.push(m);
      allMarkersArray.push(m);
      batchMarkersToAdd.push(m);

      if (c.citation_number) {
        citationToMarker.set(String(c.citation_number), m);
      }

      if (batchMarkersToAdd.length >= BATCH_SIZE || i === list.length - 1) {
        batchMarkersToAdd.forEach((marker) => {
          markersLayerGroup.addLayer(marker);
        });
        batchMarkersToAdd.length = 0;

        // Yield to browser
        await new Promise((resolve) => requestAnimationFrame(resolve));
      }
    }
  }

  focusMap();

  // Update stats and legend based on the provided list (search results)
  try {
    // Total citations and total amount
    const totalCount = list.length;
    const totalCountFormatted = totalCount.toLocaleString();
    document.getElementById("totalCitations").textContent = totalCountFormatted;
    const totalAmount = list.reduce(
      (sum, c) => sum + (parseFloat(c.amount_due) || 0),
      0
    );
    const totalAmountFormatted = formatDollarAmount(totalAmount);
    document.getElementById("totalAmount").innerHTML = totalAmountFormatted;

    // Update stats pills
    const statsPillCitations = document.getElementById(
      "statsPillCitationsValue"
    );
    const statsPillTotal = document.getElementById("statsPillTotalValue");
    if (statsPillCitations)
      statsPillCitations.textContent = totalCountFormatted;
    if (statsPillTotal) statsPillTotal.innerHTML = totalAmountFormatted;

    // Legend buckets
    let redCount = 0; // >= $76
    let orangeCount = 0; // $46-75
    let yellowCount = 0; // $26-45
    let greenCount = 0; // $0-25
    list.forEach((citation) => {
      const amount = parseFloat(citation.amount_due) || 0;
      if (amount >= 76) redCount++;
      else if (amount >= 46) orangeCount++;
      else if (amount >= 26) yellowCount++;
      else greenCount++;
    });
    document.getElementById("legendRed").textContent =
      redCount.toLocaleString();
    document.getElementById("legendOrange").textContent =
      orangeCount.toLocaleString();
    document.getElementById("legendYellow").textContent =
      yellowCount.toLocaleString();
    document.getElementById("legendGreen").textContent =
      greenCount.toLocaleString();
  } catch (_) {
    // no-op if elements not found
  }
}

// Header recent time: fixed-length scramble during load, gentle decode reveal
let recentScrambleTimer = null;
let recentScrambleTargetLength = null;
function startRecentScramble(targetLength) {
  const el = document.getElementById("recentCitationTime");
  if (!el) return;
  if (recentScrambleTimer) clearInterval(recentScrambleTimer);
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:, ";
  recentScrambleTargetLength = targetLength || 22; // fallback length
  recentScrambleTimer = setInterval(() => {
    let s = "";
    for (let i = 0; i < recentScrambleTargetLength; i++) {
      s += chars[Math.floor(Math.random() * chars.length)];
    }
    el.textContent = s;
  }, 70); // smooth, not jarring
}

function revealRecentTime(finalText) {
  const el = document.getElementById("recentCitationTime");
  if (!el) return;
  if (recentScrambleTimer) {
    clearInterval(recentScrambleTimer);
    recentScrambleTimer = null;
  }
  const target = finalText;
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:, ";
  const currentScrambled = el.textContent; // keep the current scramble
  const length = target.length;
  // Ensure we have the right length array
  let result =
    currentScrambled.length === length
      ? Array.from(currentScrambled)
      : Array.from(
          { length: length },
          () => chars[Math.floor(Math.random() * chars.length)]
        );
  let index = 0;
  const interval = setInterval(() => {
    // Replace characters in place from left to right
    if (index < length) {
      result[index] = target[index];
      index++;
    }
    // Keep scrambling the remaining characters
    for (let i = index; i < length; i++) {
      result[i] = chars[Math.floor(Math.random() * chars.length)];
    }
    el.textContent = result.join("");
    if (index >= length) {
      clearInterval(interval);
      el.textContent = target;
    }
  }, 50);
}

// Load citations from API
async function loadCitations() {
  // Estimate final length - account for "Today, " prefix if it's today
  const estimateFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Detroit",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
  const estimated = `LATEST: ${estimateFormatter.format(new Date())}`;
  // Use slightly longer estimate to account for "Today, " format
  startRecentScramble(Math.max(estimated.length, 25));
  try {
    const response = await fetch("/api/citations");
    const data = await response.json();

    if (data.citations) {
      allCitations = data.citations || [];

      // Filter citations based on default time filter (week) before processing
      // This avoids showing "no results" error and applies filter during load
      const now = new Date();
      const cutoffTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 7 days ago
      const cutoffTimestamp = cutoffTime.getTime();

      citations = allCitations.filter((c) => {
        if (!c.issue_date) return false;
        const issueTimestamp = new Date(c.issue_date).getTime();
        return issueTimestamp >= cutoffTimestamp;
      });

      // Show error message if there's an auth issue
      if (
        data.error &&
        (data.error.includes("authentication") ||
          data.error.includes("SUPABASE_SERVICE_ROLE_KEY"))
      ) {
        document.getElementById("loading").innerHTML = `
                 <div style="background: rgba(255, 59, 48, 0.9); padding: 20px 30px; border-radius: 0; color: #fff; max-width: 500px; text-align: center;">
                   <div style="font-size: 24px; margin-bottom: 10px;">🔒</div>
                   <strong>Authentication Required</strong><br>
                   <div style="margin-top: 10px; font-size: 13px;">
                     Please add SUPABASE_SERVICE_ROLE_KEY to your environment variables.<br>
                     See <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 0;">FIX_AUTH_ISSUE.md</code> for instructions.
                   </div>
                 </div>
               `;
        return;
      }

      // Show message if no citations with coordinates in filtered set
      // Check original data.total to see if there are any citations at all
      if (citations.length === 0) {
        if (allCitations.length === 0 && (data.total || 0) > 0) {
          // There are citations in DB but none have coordinates
          document.getElementById("loading").innerHTML = `
                   <div style="background: rgba(255, 149, 0, 0.9); padding: 20px 30px; border-radius: 0; color: #fff; max-width: 500px; text-align: center;">
                     <div style="font-size: 24px; margin-bottom: 10px;">📍</div>
                     <strong>No Geocoded Citations</strong><br>
                     <div style="margin-top: 10px; font-size: 13px;">
                       Found ${data.total} citations but none have coordinates.<br>
                       Run: <code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 0;">python geocode_citations.py</code>
                     </div>
                   </div>
                 `;
          document.getElementById("totalCitations").textContent = "0";
          document.getElementById("totalAmount").innerHTML = formatDollarAmount(0);
          return;
        }
        // If just no citations in past week, that's fine - show empty state
      }

      // Update stats
      const totalCountFormatted = citations.length.toLocaleString();
      document.getElementById("totalCitations").textContent = totalCountFormatted;
      const totalAmount = citations.reduce(
        (sum, c) => sum + (parseFloat(c.amount_due) || 0),
        0
      );
      const totalAmountFormatted = formatDollarAmount(totalAmount);
      document.getElementById("totalAmount").innerHTML = totalAmountFormatted;

      // Update stats pills for total citations and total amount
      const statsPillCitations = document.getElementById("statsPillCitationsValue");
      const statsPillTotal = document.getElementById("statsPillTotalValue");
      if (statsPillCitations) statsPillCitations.textContent = totalCountFormatted;
      if (statsPillTotal) statsPillTotal.innerHTML = totalAmountFormatted;

      // Compute today's stats in America/Detroit
      const detroitTZ = "America/Detroit";
      const nowDetroit = new Date(
        new Intl.DateTimeFormat("en-US", { timeZone: detroitTZ }).format(
          new Date()
        )
      );
      const todayDetroitStr = new Intl.DateTimeFormat("en-CA", {
        timeZone: detroitTZ,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(new Date());

      let countToday = 0;
      let amountToday = 0;
      citations.forEach((c) => {
        if (!c.issue_date) return;
        const d = new Date(c.issue_date);
        const dStr = new Intl.DateTimeFormat("en-CA", {
          timeZone: detroitTZ,
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(d);
        if (dStr === todayDetroitStr) {
          countToday += 1;
          amountToday += parseFloat(c.amount_due) || 0;
        }
      });
      const countTodayFormatted = countToday.toLocaleString();
      const amountTodayFormatted = formatDollarAmount(amountToday);
      document.getElementById("totalCitationsToday").textContent =
        countTodayFormatted;
      document.getElementById("totalAmountToday").innerHTML =
        amountTodayFormatted;

      // Update stats pills
      const statsPillToday = document.getElementById("statsPillTodayValue");
      const statsPillTodayTotal = document.getElementById(
        "statsPillTodayTotalValue"
      );
      if (statsPillToday) statsPillToday.textContent = countTodayFormatted;
      if (statsPillTodayTotal)
        statsPillTodayTotal.innerHTML = amountTodayFormatted;

      // Update most recent citation time (America/Detroit)
      if (data.most_recent_citation_time) {
        const recent = new Date(data.most_recent_citation_time);
        mostRecentCitationTime = data.most_recent_citation_time; // Store for Latest link
        mostRecentCitationNumber = data.most_recent_citation_number || null; // Store citation number

        if (!isNaN(recent.getTime())) {
          const detroitTZ = "America/Detroit";
          // Check if the citation is from today
          const todayDetroitStr = new Intl.DateTimeFormat("en-CA", {
            timeZone: detroitTZ,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          }).format(new Date());

          const recentDateStr = new Intl.DateTimeFormat("en-CA", {
            timeZone: detroitTZ,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          }).format(recent);

          let formattedTime;
          if (recentDateStr === todayDetroitStr) {
            // Format as "Today, X:YZ PM/AM"
            const timeFormatter = new Intl.DateTimeFormat("en-US", {
              timeZone: detroitTZ,
              hour: "numeric",
              minute: "2-digit",
              hour12: true,
            });
            formattedTime = `Today, ${timeFormatter.format(recent)}`;
          } else {
            // Format as "Month Day, Year X:YZ PM/AM"
            const formatter = new Intl.DateTimeFormat("en-US", {
              timeZone: detroitTZ,
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "numeric",
              minute: "2-digit",
              hour12: true,
            });
            formattedTime = formatter.format(recent);
          }
          revealRecentTime(`LATEST: ${formattedTime}`);
          const el = document.getElementById("recentCitationTime");
          if (el) {
            el.style.cursor = "pointer";
            el.title = "Jump to latest citation";
            el.onclick = () => focusLatestCitation();
          }
        }
      }

      // Calculate legend counts - new color scheme
      let redCount = 0; // >= $76
      let orangeCount = 0; // $46-75
      let yellowCount = 0; // $26-45
      let greenCount = 0; // $0-25

      citations.forEach((citation) => {
        const amount = parseFloat(citation.amount_due) || 0;
        if (amount >= 76) {
          redCount++;
        } else if (amount >= 46) {
          orangeCount++;
        } else if (amount >= 26) {
          yellowCount++;
        } else {
          greenCount++;
        }
      });

      // Update legend counts
      document.getElementById("legendRed").textContent =
        redCount.toLocaleString();
      document.getElementById("legendOrange").textContent =
        orangeCount.toLocaleString();
      document.getElementById("legendYellow").textContent =
        yellowCount.toLocaleString();
      document.getElementById("legendGreen").textContent =
        greenCount.toLocaleString();

      // Geocode and place markers
      await placeMarkers();

      // Hide loading
      document.getElementById("loading").style.display = "none";
      
      // Check for deep link
      await handleDeepLink();
    }
  } catch (error) {
    console.error("Error loading citations:", error);
    document.getElementById("loading").textContent = "Error loading citations";
  }
}

// Handle deep linking for citations
async function handleDeepLink() {
  const path = window.location.pathname;
  const match = path.match(/\/citation\/(\d+)/);
  if (match && match[1]) {
    const citationNumber = match[1];
    
    // First try to find it in the loaded markers
    if (citationToMarker.has(citationNumber)) {
      const marker = citationToMarker.get(citationNumber);
      showCitationDetails(marker._citation);
      map.setView(marker.getLatLng(), 18);
    } else {
      // If not in current view (e.g. filtered out or paginated), fetch it directly
      try {
        const response = await fetch(`/api/citation/${citationNumber}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.citation) {
          showCitationDetails(data.citation);
          
          if (data.citation.latitude && data.citation.longitude) {
            const lat = parseFloat(data.citation.latitude);
            const lon = parseFloat(data.citation.longitude);
            map.setView([lat, lon], 18);
            
            // Create a temporary marker if one doesn't exist
            const tempMarker = L.marker([lat, lon], {
                icon: L.icon({
                  iconUrl: pinIcons.red, // default to red for deep link
                  iconSize: [32, 40],
                  iconAnchor: [16, 40],
                })
            }).addTo(map);
            tempMarker.bindPopup("Filtered citation").openPopup();
          }
        }
      } catch (e) {
        console.error("Failed to load deep linked citation", e);
      }
    }
  } else if (path === '/') {
    // If returning to root, ensure side panel is closed
    closeSidePanel();
  }
}

window.addEventListener('popstate', () => {
  handleDeepLink();
});

// Get offset for duplicate coordinates
function getOffsetCoordinates(lat, lon) {
  const coordKey = `${lat.toFixed(6)},${lon.toFixed(6)}`;

  if (!usedCoordinates.has(coordKey)) {
    usedCoordinates.set(coordKey, 1);
    return { lat, lon };
  }

  // If this coordinate is already used, add a small random offset
  const count = usedCoordinates.get(coordKey);
  usedCoordinates.set(coordKey, count + 1);

  // Create a spiral offset: each duplicate gets a slightly larger radius
  // Use tighter distribution (2 meters per duplicate) and cap max distance
  const angle = count * 137.5; // Golden angle for even distribution
  const baseDistance = 0.00002; // ~2 meters per duplicate (tighter)
  const maxDistance = 0.00008; // Cap at ~8 meters max (prevents straying too far)
  const distance = Math.min(baseDistance * count, maxDistance);
  const offsetLat = lat + Math.cos((angle * Math.PI) / 180) * distance;
  const offsetLon = lon + Math.sin((angle * Math.PI) / 180) * distance;

  return { lat: offsetLat, lon: offsetLon };
}

function closeCitationPopup() {
  if (activeCitationPopup) {
    map.closePopup(activeCitationPopup);
    map.removeLayer(activeCitationPopup);
    activeCitationPopup = null;
  }
}

function buildCitationPopupContent(citation) {
  const amount = (parseFloat(citation.amount_due) || 0).toFixed(2);
  const issueDate = citation.issue_date
    ? new Intl.DateTimeFormat("en-US", {
        timeZone: "America/Detroit",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }).format(new Date(citation.issue_date))
    : "UNKNOWN";

  return `
          <div class="popup-receipt">
            <div class="receipt-title">
              CITATION #${citation.citation_number || "UNKNOWN"}
            </div>
            <div class="receipt-row">
              <span>Location</span>
              <span>${citation.location || "UNKNOWN"}</span>
            </div>
            <div class="receipt-row">
              <span>Issued</span>
              <span>${issueDate}</span>
            </div>
            <div class="receipt-row">
              <span>Amount</span>
              <span>$${amount}</span>
            </div>
            <div class="receipt-row">
              <span>Plate</span>
              <span>${citation.plate_state || ""} ${
    citation.plate_number || ""
  }</span>
            </div>
          </div>
        `;
}

function showCitationPopup(citation, markerLatLng = null) {
  if (!citation) return;

  let lat = markerLatLng ? markerLatLng.lat : null;
  let lon = markerLatLng ? markerLatLng.lng : null;

  if (lat === null || lon === null) {
    if (!citation.latitude || !citation.longitude) {
      return;
    }
    lat = parseFloat(citation.latitude);
    lon = parseFloat(citation.longitude);
  }

  if (Number.isNaN(lat) || Number.isNaN(lon)) return;

  closeCitationPopup();

  activeCitationPopup = L.popup({
    className: "citation-popup",
    closeButton: true,
    autoClose: false,
    closeOnClick: false,
    maxWidth: 280,
  })
    .setLatLng([lat, lon])
    .setContent(buildCitationPopupContent(citation))
    .addTo(map);

  activeCitationPopup.on("remove", () => {
    activeCitationPopup = null;
  });
}

// Create marker for citation with coordinates
function createMarkerForCitation(citation) {
  // Check if citation has coordinates
  if (!citation.latitude || !citation.longitude) {
    console.warn("Citation missing coordinates:", citation.citation_number);
    return null;
  }

  const originalLat = parseFloat(citation.latitude);
  const originalLon = parseFloat(citation.longitude);

  // Get offset coordinates if duplicates exist
  const { lat, lon } = getOffsetCoordinates(originalLat, originalLon);

  // Create icon based on amount
  const amount = parseFloat(citation.amount_due) || 0;
  let iconUrl;
  if (amount >= 76) {
    iconUrl = pinIcons.red;
  } else if (amount >= 46) {
    iconUrl = pinIcons.orange;
  } else if (amount >= 26) {
    iconUrl = pinIcons.yellow;
  } else {
    iconUrl = pinIcons.green;
  }

  // Create marker with icon
  const marker = L.marker([lat, lon], {
    icon: L.icon({
      iconUrl: iconUrl,
      iconSize: [32, 40],
      iconAnchor: [16, 40],
    }),
    riseOnHover: true,
    keyboard: false,
  });

  // Store citation data on marker for click handler
  marker._citation = citation;
  marker._originalLat = originalLat;
  marker._originalLon = originalLon;

  // Add click handler to marker
  marker.on("click", function () {
    const currentZoom = map.getZoom();
    closeCitationPopup();
    
    // Update URL
    if (citation.citation_number) {
        window.history.pushState({}, '', '/citation/' + citation.citation_number);
    }
    
    map.flyTo([lat, lon], currentZoom, {
      animate: true,
      duration: 0.6,
      easeLinearity: 0.25,
      noMoveStart: false,
    });
    map.once("moveend", function handleMarkerPan() {
      showCitationDetails(citation);
    });
  });

  // Keep reference to the marker by citation number
  if (citation.citation_number) {
    citationToMarker.set(String(citation.citation_number), marker);
  }

  return marker;
}

// Focus and open the latest citation
async function focusLatestCitation() {
  console.log("focusLatestCitation called", {
    mostRecentCitationNumber,
    mostRecentCitationTime,
    citationsCount: citations.length,
  });

  if (!citations.length && !mostRecentCitationNumber) {
    console.warn("No citations loaded and no citation number");
    return;
  }

  let latest = null;

  // First try to find by citation number (most reliable)
  if (mostRecentCitationNumber) {
    const targetNum = String(mostRecentCitationNumber);
    console.log("Looking for citation number:", targetNum);

    latest = citations.find((c) => {
      const cNum = String(c.citation_number || "");
      const match = cNum === targetNum;
      if (match) console.log("Found citation by number:", c.citation_number);
      return match;
    });

    if (!latest) {
      console.log("Citation not found in loaded array, attempting to fetch...");
      // If not found in loaded citations, fetch it directly
      try {
        const resp = await fetch(
          `/api/search?mode=citation&citation_number=${encodeURIComponent(
            mostRecentCitationNumber
          )}`
        );
        const data = await resp.json();
        if (
          data.status === "success" &&
          data.citations &&
          data.citations.length > 0
        ) {
          latest = data.citations[0];
          console.log("Fetched citation from API:", latest.citation_number);
          // Add it to the citations array and create a marker for it
          if (
            !citations.find(
              (c) =>
                String(c.citation_number) === String(latest.citation_number)
            )
          ) {
            citations.push(latest);
            const marker = createMarkerForCitation(latest);
            if (marker) {
              markers.push(marker);
              if (latest.citation_number) {
                citationToMarker.set(String(latest.citation_number), marker);
              }
              markersLayerGroup.addLayer(marker);
            }
          }
        } else {
          console.warn(
            "API search returned no results for citation",
            mostRecentCitationNumber
          );
        }
      } catch (err) {
        console.error("Error fetching latest citation:", err);
      }
    }
  }

  // Only fall back to timestamp/date matching if we still don't have a match
  if (!latest) {
    // If not found by citation number, try to find by timestamp (with tolerance)
    if (mostRecentCitationTime) {
      const targetTime = new Date(mostRecentCitationTime).getTime();
      // Use tolerance of 5 seconds to handle precision differences
      const tolerance = 5000; // 5 seconds in milliseconds
      for (const c of citations) {
        if (c.issue_date) {
          const issueTime = new Date(c.issue_date).getTime();
          if (Math.abs(issueTime - targetTime) <= tolerance) {
            latest = c;
            console.log("Found citation by timestamp:", c.citation_number);
            break;
          }
        }
      }
    }

    // If still not found, find the most recent by date from loaded citations
    if (!latest && citations.length > 0) {
      latest = citations[0];
      for (const c of citations) {
        if (!c.issue_date) continue;
        if (new Date(c.issue_date) > new Date(latest.issue_date || 0)) {
          latest = c;
        }
      }
      console.log(
        "Falling back to most recent citation by date:",
        latest.citation_number
      );
    }
  }

  if (!latest || !latest.citation_number) {
    console.warn("Could not find latest citation", {
      latest,
      mostRecentCitationNumber,
    });
    return;
  }

  console.log("Focusing on citation:", latest.citation_number);

  const marker = citationToMarker.get(String(latest.citation_number));
  if (marker) {
    const lat = parseFloat(latest.latitude);
    const lon = parseFloat(latest.longitude);
    map.flyTo([lat, lon], 16, {
      duration: 1.2,
      easeLinearity: 0.25,
    });
    showCitationDetails(latest, marker.getLatLng());
  } else if (latest.latitude && latest.longitude) {
    // Marker not found but we have coordinates - create a temporary marker or just focus
    const lat = parseFloat(latest.latitude);
    const lon = parseFloat(latest.longitude);
    map.flyTo([lat, lon], 16, {
      duration: 1.2,
      easeLinearity: 0.25,
    });
    showCitationDetails(latest, { lat, lng: lon });
    // Try to create marker now if it doesn't exist
    const newMarker = createMarkerForCitation(latest);
    if (newMarker) {
      markers.push(newMarker);
      if (latest.citation_number) {
        citationToMarker.set(String(latest.citation_number), newMarker);
      }
      markersLayerGroup.addLayer(newMarker);
      showCitationDetails(latest, newMarker.getLatLng());
    }
  } else {
    console.warn("Citation found but no coordinates:", latest.citation_number);
  }
}

// Get color based on amount - Minimal opacity
function getColorForAmount(amount) {
  const amt = parseFloat(amount) || 0;
  if (amt >= 76) return "#EA4335"; // Red
  if (amt >= 46) return "#FA7B17"; // Orange
  if (amt >= 26) return "#FBBC04"; // Yellow
  return "#34A853"; // Green
}

// Place all markers - creates markers for all citations and adds them to layer group
async function placeMarkers() {
  // Clear existing markers
  markersLayerGroup.clearLayers();
  allMarkersArray = [];
  markers = [];
  citationToMarker.clear();
  usedCoordinates.clear();

  // Create markers for ALL citations (so they're ready when switching filters)
  const BATCH_SIZE = 100; // Process 100 markers at a time
  const batchMarkersToAdd = [];

  // Performance optimization: Create Set of filtered citation numbers for O(1) lookup
  const filteredCitationNumbers = new Set(
    citations.map((c) => String(c.citation_number))
  );

  // First, create markers for all citations
  for (let i = 0; i < allCitations.length; i++) {
    const citation = allCitations[i];
    const marker = createMarkerForCitation(citation);
    if (marker) {
      markers.push(marker);
      allMarkersArray.push(marker);

      // Store in map for filtering/search
      if (citation.citation_number) {
        citationToMarker.set(String(citation.citation_number), marker);
      }

      // If this citation is in the filtered set, mark it for adding
      if (filteredCitationNumbers.has(String(citation.citation_number))) {
        batchMarkersToAdd.push(marker);
      }

      // Batch add filtered markers to layer group
      if (
        batchMarkersToAdd.length >= BATCH_SIZE ||
        i === allCitations.length - 1
      ) {
        batchMarkersToAdd.forEach((m) => markersLayerGroup.addLayer(m));
        batchMarkersToAdd.length = 0;

        // Yield to browser to prevent blocking
        await new Promise((resolve) => requestAnimationFrame(resolve));
      }
    }
  }
}

// Focus map on markers
function focusMap() {
  if (markers.length > 0) {
    const group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
}

// Reset view to Ann Arbor
function resetView() {
  map.flyTo([42.2808, -83.743], 13, {
    duration: 1.2,
    easeLinearity: 0.25,
  });
}

// Show citation details in side panel
async function showCitationDetails(citation, markerLatLng = null) {
  if (!citation) return;
  const panel = document.getElementById("sidePanel");
  const content = document.getElementById("sidePanelContent");
  if (!panel || !content) return;

  // Check if mobile
  const isMobile =
    window.matchMedia && window.matchMedia("(max-width: 768px)").matches;

  // ===== PRELOAD IMAGE BEFORE OPENING PANEL =====
  // Fetch images first so we can preload before showing panel
  let images = [];
  let preloadedImageUrl = null;

  try {
    const response = await fetch(`/api/citation/${citation.citation_number}`);
    const data = await response.json();

    // Support both response shapes
    if (data && Array.isArray(data.images) && data.images.length > 0) {
      images = data.images;
    } else if (data?.citation?.images?.length > 0) {
      images = data.citation.images;
    }

    // Preload the hero image BEFORE opening panel
    if (images.length > 0) {
      preloadedImageUrl = await new Promise((resolve) => {
        const preloader = new Image();
        let resolved = false;

        preloader.onload = () => {
          if (!resolved) {
            resolved = true;
            console.log("[image] Successfully preloaded:", images[0].url);
            resolve(preloader.src);
          }
        };

        preloader.onerror = (error) => {
          if (!resolved) {
            resolved = true;
            console.error("[image] Failed to preload:", images[0].url, error);
            resolve(null); // Signal failure
          }
        };

        preloader.src = images[0].url;

        // Longer timeout for slow connections
        setTimeout(() => {
          if (!resolved) {
            resolved = true;
            console.warn(
              "[image] Preload timeout, proceeding anyway:",
              images[0].url
            );
            resolve(images[0].url); // Try anyway on timeout
          }
        }, 5000); // Increased from 3s to 5s
      });
    }
  } catch (err) {
    console.error("Error preloading citation images:", err);
  }

  // ===== NOW OPEN THE PANEL (image is ready) =====
  if (isMobile) {
    panel.classList.add("active");
    document.body.classList.add("mobile-panel-open");
  } else {
    panel.classList.add("active");
    document.body.classList.add("panel-open");
  }

  // Populate search bar with citation number
  const searchInput = document.getElementById("mainSearchInput");
  if (searchInput && citation.citation_number) {
    searchInput.value = citation.citation_number.toString();
  }

  // #region agent log (debug)
  try {
    const rect2 = panel.getBoundingClientRect();
    const style2 = window.getComputedStyle(panel);
    const sb = document.querySelector(".search-bar");
    const sbRect = sb ? sb.getBoundingClientRect() : null;
    const sbStyle = sb ? window.getComputedStyle(sb) : null;
    fetch("http://127.0.0.1:7242/ingest/e36ef556-bd8a-4e44-88f5-708e512b1239", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: "debug-session",
        runId: "pre-fix",
        hypothesisId: "H3",
        location: "static/js/map.js:showCitationDetails:afterBranch",
        message: "after mobile/desktop branch",
        data: {
          innerWidth: window.innerWidth,
          bodyClass: document.body.className,
          panelActive: panel.classList.contains("active"),
          panelRect: {
            w: rect2.width,
            h: rect2.height,
            x: rect2.x,
            y: rect2.y,
          },
          panelCss: {
            width: style2.width,
            height: style2.height,
            top: style2.top,
            bottom: style2.bottom,
            position: style2.position,
          },
          searchBarRect: sbRect
            ? { w: sbRect.width, h: sbRect.height, x: sbRect.x, y: sbRect.y }
            : null,
          searchBarCss: sbStyle
            ? {
                width: sbStyle.width,
                maxWidth: sbStyle.maxWidth,
                flex: sbStyle.flex,
              }
            : null,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  } catch (e) {}
  // #endregion agent log (debug)

  let formattedIssueDate = "UNKNOWN";
  if (citation.issue_date) {
    try {
      formattedIssueDate = new Intl.DateTimeFormat("en-US", {
        timeZone: "America/Detroit",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }).format(new Date(citation.issue_date));
    } catch (_) {
      formattedIssueDate = "UNKNOWN";
    }
  }

  content.innerHTML = `
            <div class="info-item">
              <div class="info-label">LOCATION</div>
              <div class="info-value">${citation.location || "Unknown"}</div>
            </div>
            <div class="info-item">
              <div class="info-label">ISSUE DATE</div>
              <div class="info-value">${formattedIssueDate}</div>
            </div>
            <div class="info-item">
              <div class="info-label">AMOUNT DUE</div>
              <div class="info-value">$${(
                parseFloat(citation.amount_due) || 0
              ).toFixed(2)}</div>
            </div>
            <div class="info-item">
              <div class="info-label">PLATE</div>
              <div class="info-value">${citation.plate_state || ""} ${
    citation.plate_number || ""
  }</div>
            </div>
            ${
              citation.violations && citation.violations.length > 0
                ? `
            <div class="info-item">
              <div class="info-label">VIOLATIONS</div>
              <div class="info-value">${
                Array.isArray(citation.violations)
                  ? citation.violations.join(", ")
                  : citation.violations
              }</div>
            </div>
            `
                : ""
            }
            ${
              citation.comments
                ? `
            <div class="info-item">
              <div class="info-label">COMMENTS</div>
              <div class="info-value">${citation.comments}</div>
            </div>
            `
                : ""
            }
            ${
              citation.more_info_url
                ? `
            <div class="info-item">
              <div class="info-label"></div>
              <div class="info-value"><a href="${citation.more_info_url}" target="_blank" style="color: #00d4ff;">VIEW MORE INFO →</a></div>
            </div>
            `
                : ""
            }
           `;

  // ===== DISPLAY PRELOADED IMAGE (already fetched above) =====
  const photosHero = document.getElementById("photosHero");
  const heroImage = document.getElementById("heroImage");
  const heroLoading = document.getElementById("heroLoadingSpinner");
  const seePhotosPopup = document.getElementById("seePhotosPopup");

  // ===== UPDATE CITATION TITLE =====
  const citationTitle = document.getElementById("citationTitle");
  const citationNumber = document.getElementById("citationNumber");
  if (citationTitle && citationNumber) {
    citationNumber.textContent = citation.citation_number || "Unknown";
    citationTitle.style.display = "block";
  }

  if (images.length > 0) {
    photosHero.style.display = "block";

    if (preloadedImageUrl) {
      // Image successfully preloaded - show immediately
      heroLoading.style.display = "none";
      heroImage.src = preloadedImageUrl;
      heroImage.alt =
        images[0].caption || `Citation ${citation.citation_number}`;
      heroImage.style.display = "block";
    } else {
      // Preload failed - try loading with spinner as fallback
      console.warn("[image] Preload failed, trying direct load with spinner");
      heroLoading.style.display = "flex";
      heroImage.style.display = "none";

      heroImage.onload = () => {
        heroLoading.style.display = "none";
        heroImage.style.display = "block";
      };

      heroImage.onerror = () => {
        console.error("[image] Direct load also failed:", images[0].url);
        heroLoading.style.display = "none";
        // Show placeholder or hide hero entirely
        photosHero.style.display = "none";
        return;
      };

      heroImage.src = images[0].url;
      heroImage.alt =
        images[0].caption || `Citation ${citation.citation_number}`;
    }

    // Click on hero image opens side panel gallery
    heroImage.onclick = () => openSidePanelGallery(images, 0, citation);

    // Update "See photos" popup
    if (seePhotosPopup) {
      const seePhotosText = seePhotosPopup.querySelector(".see-photos-text");
      if (seePhotosText) seePhotosText.textContent = `See photos`;
      seePhotosPopup.onclick = (e) => {
        e.stopPropagation();
        openSidePanelGallery(images, 0, citation);
      };
    }
  } else {
    // No images - hide hero
    if (photosHero) photosHero.style.display = "none";
  }

  showCitationPopup(citation, markerLatLng);
}

// Side panel gallery state
let sidePanelGalleryImages = [];
let sidePanelGalleryCitation = null;
let sidePanelGalleryIndex = 0;

// Open side panel gallery (Google Maps style)
function openSidePanelGallery(images, startIndex, citation) {
  if (!images || images.length === 0) return;

  sidePanelGalleryImages = images;
  sidePanelGalleryCitation = citation || null;
  sidePanelGalleryIndex = startIndex || 0;

  const sidePanel = document.getElementById("sidePanel");
  const sidePanelContent = document.getElementById("sidePanelContent");
  const sidePanelGallery = document.getElementById("sidePanelGallery");
  const galleryThumbnails = document.getElementById(
    "galleryThumbnailsVertical"
  );
  const galleryMainPhoto = document.getElementById("galleryMainPhoto");
  const galleryBackBtn = document.getElementById("galleryBackBtn");
  const galleryNavPrev = document.getElementById("galleryNavPrev");
  const galleryNavNext = document.getElementById("galleryNavNext");

  // Right-side viewer elements
  const rightViewer = document.getElementById("rightImageViewer");
  const rightViewerImage = document.getElementById("rightViewerImage");
  const rightViewerLoading = document.getElementById("rightViewerLoading");
  const rightViewerTitle = document.getElementById("rightViewerCitationTitle");
  const rightViewerPhotoInfo = document.getElementById("rightViewerPhotoInfo");
  const rightViewerCloseBtn = document.getElementById("rightViewerCloseBtn");
  const rightViewerNavPrev = document.getElementById("rightViewerNavPrev");
  const rightViewerNavNext = document.getElementById("rightViewerNavNext");

  // Ensure side panel is visible
  if (sidePanel) {
    sidePanel.classList.add("active");
    sidePanel.classList.add("gallery-mode");
  }

  // Hide citation details, show gallery
  if (sidePanelContent) sidePanelContent.style.display = "none";
  if (sidePanelGallery) sidePanelGallery.style.display = "flex";

  // Show right-side viewer and hide map
  if (rightViewer) {
    rightViewer.style.display = "flex";
    document.body.classList.add("right-viewer-active");
  }

  // Replace hamburger menu with back arrow
  const searchMenuBtn = document.getElementById("searchMenuBtn");
  if (searchMenuBtn) {
    // Store original hamburger icon HTML if not already stored
    if (!searchMenuBtn._originalHTML) {
      searchMenuBtn._originalHTML = searchMenuBtn.innerHTML;
    }
    // Replace with back arrow
    searchMenuBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M19 12H5M12 19l-7-7 7-7"/>
    </svg>`;
    searchMenuBtn.title = "Back to details";
    // Add click handler to go back to citation details
    searchMenuBtn._galleryBackHandler = () => closeSidePanelGallery();
    searchMenuBtn.addEventListener("click", searchMenuBtn._galleryBackHandler);
  }

  // Update right viewer header
  if (rightViewerTitle && citation) {
    rightViewerTitle.textContent = `Citation #${citation.citation_number || "Unknown"}`;
  }
  if (rightViewerPhotoInfo && images[startIndex]) {
    const img = images[startIndex];
    const dateStr = img.date || img.caption || "";
    rightViewerPhotoInfo.textContent = dateStr ? `Photo - ${dateStr}` : "Photo";
  }

  // Populate thumbnails
  if (galleryThumbnails) {
    galleryThumbnails.innerHTML = "";
    images.forEach((img, idx) => {
      const thumbContainer = document.createElement("div");
      thumbContainer.className = "gallery-thumbnail-item";
      if (idx === sidePanelGalleryIndex) thumbContainer.classList.add("active");

      const thumb = document.createElement("img");
      thumb.src = img.url;
      thumb.alt = img.caption || `Thumbnail ${idx + 1}`;
      thumb.loading = "lazy";
      thumb.decoding = "async";

      thumbContainer.appendChild(thumb);
      thumbContainer.onclick = () => loadSidePanelGalleryPhoto(idx);
      galleryThumbnails.appendChild(thumbContainer);
    });
  }

  // Load initial photo in both views
  loadSidePanelGalleryPhoto(sidePanelGalleryIndex);

  // Attach handlers
  if (galleryBackBtn) {
    galleryBackBtn.onclick = closeSidePanelGallery;
  }
  if (galleryNavPrev) {
    galleryNavPrev.onclick = () => navigateSidePanelGallery(-1);
  }
  if (galleryNavNext) {
    galleryNavNext.onclick = () => navigateSidePanelGallery(1);
  }

  // Right viewer handlers
  if (rightViewerCloseBtn) {
    rightViewerCloseBtn.onclick = closeSidePanelGallery;
  }
  if (rightViewerNavPrev) {
    rightViewerNavPrev.onclick = () => navigateSidePanelGallery(-1);
  }
  if (rightViewerNavNext) {
    rightViewerNavNext.onclick = () => navigateSidePanelGallery(1);
  }
  const rightViewerShareBtn = document.getElementById("rightViewerShareBtn");
  if (rightViewerShareBtn) {
    rightViewerShareBtn.onclick = () => {
      // Placeholder for share functionality
      if (navigator.share && rightViewerImage && rightViewerImage.src) {
        navigator.share({
          title: rightViewerTitle ? rightViewerTitle.textContent : "Citation Photo",
          url: rightViewerImage.src,
        }).catch(() => {
          // Fallback: copy to clipboard
          navigator.clipboard.writeText(rightViewerImage.src);
        });
      } else if (rightViewerImage && rightViewerImage.src) {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(rightViewerImage.src).then(() => {
          alert("Image URL copied to clipboard");
        });
      }
    };
  }

  // Keyboard navigation
  sidePanelGalleryKeyHandler = (e) => {
    if (e.key === "ArrowLeft") navigateSidePanelGallery(-1);
    else if (e.key === "ArrowRight") navigateSidePanelGallery(1);
    else if (e.key === "Escape") closeSidePanelGallery();
  };
  document.addEventListener("keydown", sidePanelGalleryKeyHandler);
}



// Toggle side panel collapse/expand (Google Maps style)
function toggleSidePanelCollapse() {
  const sidePanel = document.getElementById("sidePanel");
  const rightViewer = document.getElementById("rightImageViewer");
  const collapseText = document.getElementById("collapseText");
  const collapseIcon = document.getElementById("collapseIcon");
  const searchBarPanel = document.getElementById("searchBarPanel");
  
  if (!sidePanel) return;
  
  const isCollapsed = sidePanel.classList.contains("collapsed");
  
  if (isCollapsed) {
    // Expand
    sidePanel.classList.remove("collapsed");
    document.body.classList.remove("side-panel-collapsed");
    if (rightViewer && rightViewer.style.display !== "none") {
      rightViewer.style.left = "429px";
    }
    // Show search bar when expanded
    if (searchBarPanel) searchBarPanel.style.display = "";
    
    if (collapseText) collapseText.textContent = "Collapse";
    if (collapseIcon) {
      collapseIcon.setAttribute("d", "M15 18l-6-6 6-6");
    }
  } else {
    // Collapse
    sidePanel.classList.add("collapsed");
    document.body.classList.add("side-panel-collapsed");
    if (rightViewer && rightViewer.style.display !== "none") {
      rightViewer.style.left = "48px";
    }
    // Hide search bar when collapsed
    if (searchBarPanel) searchBarPanel.style.display = "none";
    
    if (collapseText) collapseText.textContent = "Expand";
    if (collapseIcon) {
      collapseIcon.setAttribute("d", "M9 18l6-6-6-6");
    }
  }
}

// Initialize collapse button handler
(function initSidePanelCollapse() {
  const collapseTab = document.getElementById("sidePanelCollapseTab");
  if (collapseTab) {
    collapseTab.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSidePanelCollapse();
    });
  }
})();

// Load a specific photo in side panel gallery
function loadSidePanelGalleryPhoto(index) {
  if (
    !sidePanelGalleryImages ||
    index < 0 ||
    index >= sidePanelGalleryImages.length
  )
    return;

  sidePanelGalleryIndex = index;
  const imgObj = sidePanelGalleryImages[index];
  const galleryMainPhoto = document.getElementById("galleryMainPhoto");
  const galleryLoading = document.getElementById("galleryLoadingSpinner");
  const thumbnails = document.querySelectorAll(".gallery-thumbnail-item");

  // Right-side viewer elements
  const rightViewerImage = document.getElementById("rightViewerImage");
  const rightViewerLoading = document.getElementById("rightViewerLoading");
  const rightViewerPhotoInfo = document.getElementById("rightViewerPhotoInfo");

  if (!galleryMainPhoto) return;

  // Show loading in both views
  if (galleryLoading) galleryLoading.style.display = "flex";
  galleryMainPhoto.style.display = "none";
  if (rightViewerLoading) rightViewerLoading.style.display = "flex";
  if (rightViewerImage) rightViewerImage.style.display = "none";

  // Preload image for faster display
  const preloader = new Image();
  preloader.onload = () => {
    // Update side panel image
    galleryMainPhoto.src = preloader.src;
    galleryMainPhoto.alt =
      imgObj.caption ||
      `Citation ${
        sidePanelGalleryCitation ? sidePanelGalleryCitation.citation_number : ""
      }`;
    if (galleryLoading) galleryLoading.style.display = "none";
    galleryMainPhoto.style.display = "block";

    // Update right viewer image
    if (rightViewerImage) {
      rightViewerImage.src = preloader.src;
      rightViewerImage.alt = galleryMainPhoto.alt;
      if (rightViewerLoading) rightViewerLoading.style.display = "none";
      rightViewerImage.style.display = "block";
    }

    // Update photo info in right viewer header
    if (rightViewerPhotoInfo) {
      const dateStr = imgObj.date || imgObj.caption || "";
      rightViewerPhotoInfo.textContent = dateStr ? `Photo - ${dateStr}` : "Photo";
    }
  };

  preloader.onerror = () => {
    console.error("[gallery] Failed to load image:", imgObj.url);
    if (galleryLoading) galleryLoading.style.display = "none";
    if (rightViewerLoading) rightViewerLoading.style.display = "none";
    // Try direct load as fallback
    galleryMainPhoto.src = imgObj.url;
    galleryMainPhoto.style.display = "block";
    if (rightViewerImage) {
      rightViewerImage.src = imgObj.url;
      rightViewerImage.style.display = "block";
    }
  };

  preloader.src = imgObj.url;
  galleryMainPhoto.decoding = "async";
  if (rightViewerImage) rightViewerImage.decoding = "async";

  // Update active thumbnail
  thumbnails.forEach((thumb, idx) => {
    if (idx === index) {
      thumb.classList.add("active");
      thumb.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
      thumb.classList.remove("active");
    }
  });
}

// Navigate side panel gallery
function navigateSidePanelGallery(delta) {
  if (!sidePanelGalleryImages || sidePanelGalleryImages.length === 0) return;

  let newIndex = sidePanelGalleryIndex + delta;
  if (newIndex < 0) newIndex = sidePanelGalleryImages.length - 1;
  if (newIndex >= sidePanelGalleryImages.length) newIndex = 0;

  loadSidePanelGalleryPhoto(newIndex);
}

// Viewer state
let viewerImages = [];
let viewerCitation = null;
let viewerIndex = 0;
let viewerMiniMap = null;
let viewerKeyHandler = null;
let viewerTouch = { startX: 0, endX: 0 };

// Open full-screen photo viewer
function openPhotoViewer(images, startIndex, citation) {
  if (!images || images.length === 0) return;
  viewerImages = images;
  viewerCitation = citation || null;
  viewerIndex = startIndex || 0;

  const pv = document.getElementById("photoViewer");
  const thumbsEl = document.getElementById("photoThumbnailsVertical");
  const closeBtn = document.getElementById("photoViewerClose");
  const prevBtn = document.getElementById("photoNavPrev");
  const nextBtn = document.getElementById("photoNavNext");
  const sidebar = document.getElementById("photoViewerSidebar");
  const toggleBtn = document.getElementById("sidebarToggle");

  // Populate thumbnails
  thumbsEl.innerHTML = "";
  images.forEach((img, idx) => {
    const t = document.createElement("img");
    t.src = img.url;
    t.alt = img.caption || `Image ${idx + 1}`;
    t.className = "photo-thumbnail-vertical";
    t.dataset.index = idx;
    t.loading = "lazy";
    t.decoding = "async";
    if (idx === viewerIndex) t.classList.add("active");
    t.addEventListener("click", () => loadViewerPhoto(idx));
    thumbsEl.appendChild(t);
  });

  // Show viewer
  pv.style.display = "block";
  document.body.style.overflow = "hidden";

  // Attach handlers
  closeBtn.onclick = closePhotoViewer;
  prevBtn.onclick = () => navigateViewerPhoto(-1);
  nextBtn.onclick = () => navigateViewerPhoto(1);
  toggleBtn.onclick = toggleSidebar;

  // Keyboard navigation
  viewerKeyHandler = function (e) {
    if (e.key === "Escape") closePhotoViewer();
    if (e.key === "ArrowLeft") navigateViewerPhoto(-1);
    if (e.key === "ArrowRight") navigateViewerPhoto(1);
  };
  document.addEventListener("keydown", viewerKeyHandler);

  // Touch gestures for mobile
  const mainImg = document.getElementById("viewerMainPhoto");
  mainImg.addEventListener("touchstart", (ev) => {
    viewerTouch.startX = ev.touches[0].clientX;
  });
  mainImg.addEventListener("touchend", (ev) => {
    viewerTouch.endX = ev.changedTouches[0].clientX;
    const dx = viewerTouch.endX - viewerTouch.startX;
    if (dx > 50) navigateViewerPhoto(-1);
    else if (dx < -50) navigateViewerPhoto(1);
  });

  // Init mini map for citation coords if available
  initMiniMap(viewerCitation);

  // Load starting photo
  loadViewerPhoto(viewerIndex);
}

function closePhotoViewer() {
  const pv = document.getElementById("photoViewer");
  pv.style.display = "none";
  document.body.style.overflow = "";

  // Remove keyboard handler
  if (viewerKeyHandler)
    document.removeEventListener("keydown", viewerKeyHandler);
  viewerKeyHandler = null;

  // Destroy mini map
  if (viewerMiniMap) {
    try {
      viewerMiniMap.remove();
    } catch (e) {}
    viewerMiniMap = null;
  }

  // Clear thumbnails and main photo
  const thumbsEl = document.getElementById("photoThumbnailsVertical");
  thumbsEl.innerHTML = "";
  const mainImg = document.getElementById("viewerMainPhoto");
  mainImg.src = "";
}

function navigateViewerPhoto(delta) {
  const newIndex = viewerIndex + delta;
  if (newIndex < 0 || newIndex >= viewerImages.length) return;
  loadViewerPhoto(newIndex);
}

function loadViewerPhoto(index) {
  if (!viewerImages || viewerImages.length === 0) return;
  viewerIndex = index;
  const imgObj = viewerImages[index];
  const mainImg = document.getElementById("viewerMainPhoto");
  const spinner = document.getElementById("viewerLoadingSpinner");
  const captionEl = document.getElementById("photoCaption");
  const dateEl = document.getElementById("photoDate");

  // Show spinner
  spinner.style.display = "block";
  mainImg.style.display = "none";

  // Update image
  mainImg.src = imgObj.url;
  mainImg.alt =
    imgObj.caption ||
    `Citation ${viewerCitation ? viewerCitation.citation_number : ""}`;
  mainImg.onload = () => {
    spinner.style.display = "none";
    mainImg.style.display = "block";
  };

  // Update metadata
  captionEl.textContent =
    imgObj.caption ||
    `Citation #${viewerCitation ? viewerCitation.citation_number : ""}`;
  if (viewerCitation && viewerCitation.issue_date) {
    try {
      const d = new Date(viewerCitation.issue_date);
      const month = d.toLocaleString("en-US", { month: "long" });
      const year = d.getFullYear();
      dateEl.textContent = `Photo - ${month} ${year}`;
    } catch (_) {
      dateEl.textContent = "";
    }
  } else {
    dateEl.textContent = "";
  }

  // Update active thumbnail
  document
    .querySelectorAll(".photo-thumbnail-vertical")
    .forEach((t) => t.classList.remove("active"));
  const sel = document.querySelector(
    '.photo-thumbnail-vertical[data-index="' + index + '"]'
  );
  if (sel) sel.classList.add("active");

  // Ensure thumbnail into view
  const activeThumb = document.querySelector(
    ".photo-thumbnail-vertical.active"
  );
  if (activeThumb)
    activeThumb.scrollIntoView({ block: "center", behavior: "smooth" });
}

function toggleSidebar() {
  const sidebar = document.getElementById("photoViewerSidebar");
  sidebar.classList.toggle("collapsed");
  // Adjust toggle icon rotation handled by CSS
}

function initMiniMap(citation) {
  const mmEl = document.getElementById("photoMinimap");
  if (!mmEl) return;

  // Clear existing map if present
  if (viewerMiniMap) {
    try {
      viewerMiniMap.remove();
    } catch (e) {}
    viewerMiniMap = null;
  }

  // If citation has coords, init map
  const lat =
    citation && citation.latitude ? parseFloat(citation.latitude) : null;
  const lon =
    citation && citation.longitude ? parseFloat(citation.longitude) : null;
  if (lat === null || lon === null || Number.isNaN(lat) || Number.isNaN(lon)) {
    mmEl.innerHTML = "";
    return;
  }

  // Create Leaflet map
  viewerMiniMap = L.map(mmEl, {
    attributionControl: false,
    zoomControl: false,
    interactive: true,
    dragging: true,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    touchZoom: false,
  }).setView([lat, lon], 16);

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    {
      subdomains: "abcd",
      maxZoom: 19,
    }
  ).addTo(viewerMiniMap);

  // Add marker
  L.marker([lat, lon]).addTo(viewerMiniMap);

  // Click mini map to jump to main map and close viewer
  mmEl.onclick = () => {
    closePhotoViewer();
    // Fly main map to this location
    map.flyTo([lat, lon], 17, { duration: 1.0 });
    // Open side panel details for this citation
    showCitationDetails(citation, { lat: lat, lng: lon });
  };
}

// Toggle between light and dark mode
function toggleTheme() {
  isDarkMode = !isDarkMode;

  // Remove current tile layer
  map.removeLayer(currentTileLayer);

  if (isDarkMode) {
    // Dark theme
    currentTileLayer = L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }
    );
    document.getElementById("themeBtn").innerHTML = getSunIcon();
  } else {
    // Light theme
    currentTileLayer = L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }
    );
    document.getElementById("themeBtn").innerHTML = getMoonIcon();
  }

  currentTileLayer.addTo(map);
}

// Filter citations by time period
async function filterByTime(period) {
  if (isSearchActive) {
    // Ignore time filter while search is active
    return;
  }
  currentTimeFilter = period;

  // Update dropdown value
  const filterDropdown = document.getElementById("filterDropdown");
  if (filterDropdown && filterDropdown.value !== period) {
    filterDropdown.value = period;
  }

  // Hide no results message initially
  const noResultsMsg = document.getElementById("noResultsMessage");
  noResultsMsg.classList.remove("visible");

  // Calculate cutoff time - use UTC for consistent comparison with database dates
  // Database dates are in UTC, so we need to compare in UTC
  const now = new Date();
  let cutoffTime = null;

  if (period === "hour") {
    cutoffTime = new Date(now.getTime() - 60 * 60 * 1000);
  } else if (period === "day") {
    cutoffTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  } else if (period === "week") {
    cutoffTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  }
  // else cutoffTime remains null (show all)

  // Convert cutoff to UTC timestamp for comparison
  // JavaScript Date objects are internally UTC, but we ensure proper comparison
  const cutoffTimestamp = cutoffTime ? cutoffTime.getTime() : null;

  // Filter citations based on time period
  // Use allCitations (full dataset) when showing "all", otherwise filter from allCitations
  const filteredCitations =
    cutoffTimestamp === null
      ? allCitations
      : allCitations.filter((c) => {
          if (!c.issue_date) return false;
          const issueTimestamp = new Date(c.issue_date).getTime();
          return issueTimestamp >= cutoffTimestamp;
        });

  // Update citations array to reflect filtered set
  citations = filteredCitations;

  // Clear existing markers and add filtered ones to layer group
  markersLayerGroup.clearLayers();
  await placeMarkers();

  const visibleCount = filteredCitations.length;

  // Show no results message if no citations found
  if (visibleCount === 0 && period !== "all") {
    let intervalText = "";
    if (period === "hour") {
      intervalText = "NONE FOUND IN THE LAST HOUR";
    } else if (period === "day") {
      intervalText = "NONE FOUND IN THE LAST 24 HOURS";
    } else if (period === "week") {
      intervalText = "NONE FOUND IN THE LAST WEEK";
    }
    document.getElementById("noResultsInterval").textContent = intervalText;
    noResultsMsg.classList.add("visible");
  } else {
    noResultsMsg.classList.remove("visible");
  }

  // Update stats based on visible citations
  updateStatsForFilter(period, cutoffTimestamp);
}

// Update statistics for filtered citations
function updateStatsForFilter(period, cutoffTimestamp) {
  let filteredCitations = citations;

  if (cutoffTimestamp !== null) {
    filteredCitations = citations.filter((c) => {
      if (!c.issue_date) return false;
      const issueDate = new Date(c.issue_date);
      // Compare timestamps (UTC) to avoid timezone issues
      return issueDate.getTime() >= cutoffTimestamp;
    });
  }

  // Update total citations and amount
  const filteredCountFormatted = filteredCitations.length.toLocaleString();
  document.getElementById("totalCitations").textContent =
    filteredCountFormatted;
  const totalAmount = filteredCitations.reduce(
    (sum, c) => sum + (parseFloat(c.amount_due) || 0),
    0
  );
  const filteredAmountFormatted = formatDollarAmount(totalAmount);
  document.getElementById("totalAmount").innerHTML = filteredAmountFormatted;

  // Update stats pills
  const statsPillCitations = document.getElementById("statsPillCitationsValue");
  const statsPillTotal = document.getElementById("statsPillTotalValue");
  if (statsPillCitations)
    statsPillCitations.textContent = filteredCountFormatted;
  if (statsPillTotal) statsPillTotal.innerHTML = filteredAmountFormatted;

  // Update legend counts for filtered citations
  let redCount = 0;
  let orangeCount = 0;
  let greenCount = 0;

  filteredCitations.forEach((citation) => {
    const amount = parseFloat(citation.amount_due) || 0;
    if (amount >= 50) {
      redCount++;
    } else if (amount >= 30) {
      orangeCount++;
    } else {
      greenCount++;
    }
  });

  document.getElementById("legendRed").textContent = redCount.toLocaleString();
  document.getElementById("legendOrange").textContent =
    orangeCount.toLocaleString();
  document.getElementById("legendGreen").textContent =
    greenCount.toLocaleString();
}

// Initialize filter dropdown - set "week" as default
(function initFilterDropdown() {
  const filterDropdown = document.getElementById("filterDropdown");
  if (filterDropdown) {
    filterDropdown.value = "week";
  }
})();

// Load citations on page load
loadCitations();

// Notifications UI (bell)
(function initNotifyUI() {
  const toggleBtn = document.getElementById("notifyToggleBtn");
  const panel = document.getElementById("notifyPanel");
  const modeEl = document.getElementById("notifyMode");
  const plateRow = document.getElementById("notifyPlate");
  const locRow = document.getElementById("notifyLocation");
  const pickBtn = document.getElementById("notifyPickCenterBtn");
  const useMyLocationBtn = document.getElementById("notifyUseMyLocationBtn");
  const radiusEl = document.getElementById("notifyRadiusMeters");
  const pickedText = document.getElementById("notifyPickedText");
  const submitBtn = document.getElementById("notifySubmitBtn");
  const msg = document.getElementById("notifyMsg");
  const searchPanel = document.getElementById("searchPanel");
  const searchHint = document.getElementById("searchHint");
  let pendingPickNotify = false;
  let notifyCircle = null;

  // Add a subtle subscribe tip if not present
  if (panel && !document.getElementById("notifyTip")) {
    const tip = document.createElement("div");
    tip.id = "notifyTip";
    tip.style.cssText =
      "margin-top:6px; padding:8px; border:1px dashed #00d4ff; color:#00d4ff; font-size:10px; background:rgba(0,255,0,0.05)";
    tip.textContent =
      "Tip: Subscribe by plate, or pick a center & radius to get alerts for that area.";
    panel.appendChild(tip);
  }

  function updateNotifyInputs() {
    const mode = modeEl.value;
    plateRow.style.display = mode === "plate" ? "flex" : "none";
    locRow.style.display = mode === "location" ? "flex" : "none";
    msg.textContent = "";

    // Visual cue for location notifications
    if (mode === "location") {
      if (searchHint) searchHint.style.bottom = "180px"; // move up to avoid overlap
      const r = parseFloat(radiusEl.value || "0");
      if (searchCenter && !isNaN(r) && r > 0) {
        if (notifyCircle) map.removeLayer(notifyCircle);
        notifyCircle = L.circle([searchCenter.lat, searchCenter.lon], {
          radius: r,
          color: "#00ffff",
          dashArray: "6 6",
        }).addTo(map);
      }
    } else {
      if (searchHint) searchHint.style.bottom = "100px";
      if (notifyCircle) {
        map.removeLayer(notifyCircle);
        notifyCircle = null;
      }
    }
  }
  modeEl.addEventListener("change", updateNotifyInputs);
  updateNotifyInputs();

  if (toggleBtn && panel) {
    toggleBtn.addEventListener("click", () => {
      const opening = panel.style.display === "none";
      panel.style.display = opening ? "flex" : "none";
      if (opening) {
        // Close search panel for clean UX
        if (searchPanel) searchPanel.style.display = "none";
        // Reset any active search state
        isSearchActive = false;
        if (searchCircle) {
          map.removeLayer(searchCircle);
          searchCircle = null;
        }
        showOnlyMarkers(citations);
        updateNotifyInputs();
      } else {
        msg.textContent = "";
        if (searchHint) searchHint.style.bottom = "100px";
        if (notifyCircle) {
          map.removeLayer(notifyCircle);
          notifyCircle = null;
        }
      }
    });
  }

  pickBtn.addEventListener("click", () => {
    pendingPickNotify = true;
    pickedText.textContent = "tap map to set center";
    if (searchHint) searchHint.style.bottom = "180px";
    if (map && map._container) map._container.style.cursor = "crosshair";
  });

  map.on("click", (e) => {
    if (!pendingPickNotify) return;
    pendingPickNotify = false;
    searchCenter = { lat: e.latlng.lat, lon: e.latlng.lng };
    pickedText.textContent = `center: ${searchCenter.lat.toFixed(
      5
    )}, ${searchCenter.lon.toFixed(5)}`;
    // Draw/update cyan preview circle
    const r = parseFloat(radiusEl.value || "0");
    if (notifyCircle) map.removeLayer(notifyCircle);
    if (!isNaN(r) && r > 0) {
      notifyCircle = L.circle([searchCenter.lat, searchCenter.lon], {
        radius: r,
        color: "#00ffff",
        dashArray: "6 6",
      }).addTo(map);
    }
    if (map && map._container) map._container.style.cursor = "";
  });

  if (useMyLocationBtn) {
    useMyLocationBtn.addEventListener("click", async () => {
      try {
        const pos = await (async () =>
          new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
              return reject(new Error("geolocation not supported"));
            }
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              enableHighAccuracy: true,
              timeout: 8000,
              maximumAge: 0,
            });
          }))();
        searchCenter = {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        };
        pickedText.textContent = `center: ${searchCenter.lat.toFixed(
          5
        )}, ${searchCenter.lon.toFixed(5)}`;
        const r = parseFloat(radiusEl.value || "0");
        if (notifyCircle) map.removeLayer(notifyCircle);
        if (!isNaN(r) && r > 0) {
          notifyCircle = L.circle([searchCenter.lat, searchCenter.lon], {
            radius: r,
            color: "#00ffff",
            dashArray: "6 6",
          }).addTo(map);
        }
        map.flyTo([searchCenter.lat, searchCenter.lon], 15, {
          duration: 1.2,
          easeLinearity: 0.25,
        });
      } catch (_) {
        // ignore geolocation errors silently
      }
    });
  }

  // Live update preview when radius changes in notify panel
  radiusEl.addEventListener("input", () => {
    const r = parseFloat(radiusEl.value || "0");
    if (notifyCircle && !isNaN(r)) notifyCircle.setRadius(r);
  });

  // Inline +/- for notify radius
  const notifyMinus = document.getElementById("notifyRadiusMinus");
  const notifyPlus = document.getElementById("notifyRadiusPlus");
  function adjustNotifyRadius(delta) {
    const current = parseFloat(radiusEl.value || "0") || 0;
    const next = Math.max(10, Math.min(100000, current + delta));
    radiusEl.value = String(Math.round(next));
    radiusEl.dispatchEvent(new Event("input"));
  }
  if (notifyMinus)
    notifyMinus.addEventListener("click", () => adjustNotifyRadius(-50));
  if (notifyPlus)
    notifyPlus.addEventListener("click", () => adjustNotifyRadius(50));

  submitBtn.addEventListener("click", async () => {
    msg.style.color = "#888";
    msg.textContent = "";
    const email = (document.getElementById("notifyEmail").value || "").trim();
    if (!email) {
      msg.style.color = "#ff8080";
      msg.textContent = "Email is required";
      return;
    }
    // persist contact locally for convenience
    try {
      localStorage.setItem("notify_email", email || "");
    } catch (_) {}
    const mode = modeEl.value;
    let payload = {
      email: email,
    };
    if (mode === "plate") {
      const st = (document.getElementById("notifyPlateState").value || "")
        .trim()
        .toUpperCase();
      const pn = (
        document.getElementById("notifyPlateNumber").value || ""
      ).trim();
      if (!st || !pn) {
        msg.style.color = "#ff8080";
        msg.textContent = "Enter plate state and number";
        return;
      }
      payload.plate_state = st;
      payload.plate_number = pn;
    } else {
      const r = parseFloat(radiusEl.value || "0");
      if (!searchCenter || isNaN(r) || r <= 0) {
        msg.style.color = "#ff8080";
        msg.textContent = "Pick a center and set a positive radius";
        return;
      }
      payload.center_lat = searchCenter.lat;
      payload.center_lon = searchCenter.lon;
      payload.radius_m = r;
    }
    try {
      const resp = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok) {
        msg.style.color = "#80ff80";
        msg.textContent =
          mode === "plate"
            ? "Subscribed: you'll get alerts when this plate is ticketed."
            : "Subscribed: you'll get alerts for tickets in this area.";
      } else {
        msg.style.color = "#ff8080";
        msg.textContent = data.error || "Failed to subscribe";
      }
    } catch (err) {
      msg.style.color = "#ff8080";
      msg.textContent = "Network error";
    }
  });

  // Pre-fill contact from localStorage
  try {
    const savedEmail = localStorage.getItem("notify_email") || "";
    if (savedEmail) document.getElementById("notifyEmail").value = savedEmail;
  } catch (_) {}
})();

// Risk Score UI
(function initRiskScoreUI() {
  const toggleBtn = document.getElementById("riskScoreToggleBtn");
  const panel = document.getElementById("riskScorePanel");
  const calculateBtn = document.getElementById("riskCalculateBtn");
  const useMyLocationBtn = document.getElementById("riskUseMyLocationBtn");
  const addressInput = document.getElementById("riskAddress");
  const durationInput = document.getElementById("riskDuration");
  const durationUnit = document.getElementById("riskDurationUnit");
  const daySelect = document.getElementById("riskDay");
  const timeInput = document.getElementById("riskTime");
  const resultDiv = document.getElementById("riskResult");
  const resultText = document.getElementById("riskResultText");
  const resultDetails = document.getElementById("riskResultDetails");
  const msgDiv = document.getElementById("riskMsg");

  // Set current day and time as defaults
  const now = new Date();
  // Convert JavaScript day (0=Sunday, 6=Saturday) to our format (0=Monday, 6=Sunday)
  const jsDay = now.getDay();
  daySelect.value = jsDay === 0 ? 6 : jsDay - 1;
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  timeInput.value = `${hours}:${minutes}`;

  let riskMarker = null;
  let isUsingCurrentLocation = false;

  if (toggleBtn && panel) {
    toggleBtn.addEventListener("click", () => {
      const opening = panel.style.display === "none";
      panel.style.display = opening ? "flex" : "none";
      if (opening) {
        // Close other panels for clean UX
        const searchPanel = document.getElementById("searchPanel");
        const notifyPanel = document.getElementById("notifyPanel");
        if (searchPanel) searchPanel.style.display = "none";
        if (notifyPanel) notifyPanel.style.display = "none";
      } else {
        msgDiv.textContent = "";
        resultDiv.style.display = "none";
        if (riskMarker) {
          map.removeLayer(riskMarker);
          riskMarker = null;
        }
      }
    });
  }

  useMyLocationBtn.addEventListener("click", async () => {
    try {
      const pos = await new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          return reject(new Error("geolocation not supported"));
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 8000,
          maximumAge: 0,
        });
      });
      addressInput.value = "near me";
      isUsingCurrentLocation = true;
      msgDiv.style.color = "#80ff80";
      msgDiv.textContent = "Location acquired";

      // Show marker on map
      if (riskMarker) {
        map.removeLayer(riskMarker);
      }
      riskMarker = L.marker([pos.coords.latitude, pos.coords.longitude], {
        icon: L.divIcon({
          className: "custom-marker",
          html: '<div style="background: #ff0040; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 10px #ff0040;"></div>',
          iconSize: [12, 12],
          iconAnchor: [6, 6],
        }),
      }).addTo(map);

      map.flyTo([pos.coords.latitude, pos.coords.longitude], 16, {
        duration: 1.2,
        easeLinearity: 0.25,
      });
    } catch (err) {
      msgDiv.style.color = "#ff8080";
      msgDiv.textContent = "Could not get location";
    }
  });

  calculateBtn.addEventListener("click", async () => {
    msgDiv.style.color = "#888";
    msgDiv.textContent = "Calculating...";
    resultDiv.style.display = "none";

    const address = addressInput.value.trim();
    const durationValue = parseFloat(durationInput.value);
    const durationInHours =
      durationUnit.value === "days" ? durationValue * 24 : durationValue;
    const day = parseInt(daySelect.value);
    const time = timeInput.value;

    if (!address && !isUsingCurrentLocation) {
      msgDiv.style.color = "#ff8080";
      msgDiv.textContent = "Enter an address or use 'near me'";
      return;
    }

    if (!time) {
      msgDiv.style.color = "#ff8080";
      msgDiv.textContent = "Enter a time";
      return;
    }

    try {
      let url;

      if (isUsingCurrentLocation || address.toLowerCase() === "near me") {
        // Get current location and use coordinates
        const pos = await new Promise((resolve, reject) => {
          if (!navigator.geolocation) {
            return reject(new Error("geolocation not supported"));
          }
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 8000,
            maximumAge: 0,
          });
        });
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        url = `/api/risk-score?lat=${lat}&lon=${lon}&day=${day}&time=${time}&duration_hours=${durationInHours}`;
      } else {
        // Geocode address via API
        url = `/api/risk-score?address=${encodeURIComponent(
          address
        )}&day=${day}&time=${time}&duration_hours=${durationInHours}`;
      }

      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to calculate risk");
      }

      displayRiskResult(data);
    } catch (err) {
      msgDiv.style.color = "#ff8080";
      msgDiv.textContent = err.message || "Error calculating risk";
    }
  });

  function displayRiskResult(data) {
    const address = addressInput.value || "this location";
    const duration =
      durationInput.value +
      " " +
      (parseFloat(durationInput.value) === 1
        ? durationUnit.value.slice(0, -1)
        : durationUnit.value);
    const dayName = daySelect.options[daySelect.selectedIndex].text;
    const time = timeInput.value;

    // Format in mad libs style
    const riskScore = data.risk_score;
    const riskLevel = data.risk_level;
    const riskColor =
      riskLevel === "HIGH"
        ? "#ff0040"
        : riskLevel === "MEDIUM"
        ? "#ff8000"
        : "#00d4ff";

    resultText.innerHTML = `
            <div style="margin-bottom: 8px;">
              I am parking at <strong style="color: ${riskColor};">${address}</strong> for <strong style="color: ${riskColor};">${duration}</strong> on <strong style="color: ${riskColor};">${dayName}</strong> at <strong style="color: ${riskColor};">${time}</strong>.
            </div>
            <div style="font-size: 16px; font-weight: bold; color: ${riskColor}; margin-top: 8px;">
              Your risk is <span style="font-size: 24px;">${riskScore}</span>/100 (${riskLevel})
            </div>
          `;

    // Add details
    const details = [];
    if (data.citation_count.matching_day_time > 0) {
      details.push(
        `${data.citation_count.matching_day_time} citations on ${dayName} at similar times`
      );
    }
    if (data.citation_count.nearby_total > 0) {
      details.push(
        `${data.citation_count.nearby_total} total citations within ${data.radius_m}m`
      );
    }
    if (data.average_ticket_amount) {
      details.push(`Average ticket: $${data.average_ticket_amount}`);
    }

    resultDetails.innerHTML =
      details.length > 0
        ? details.join(" • ")
        : "No historical citations found in this area";

    resultDiv.style.display = "block";
    msgDiv.textContent = "";

    // Show marker if coordinates available
    if (data.coordinates && riskMarker) {
      map.removeLayer(riskMarker);
    }
    if (data.coordinates) {
      riskMarker = L.marker([data.coordinates.lat, data.coordinates.lon], {
        icon: L.divIcon({
          className: "custom-marker",
          html: `<div style="background: ${riskColor}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 10px ${riskColor};"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7],
        }),
      }).addTo(map);

      map.flyTo([data.coordinates.lat, data.coordinates.lon], 16, {
        duration: 1.2,
        easeLinearity: 0.25,
      });
    }
  }

  // Reset location flag when address changes
  addressInput.addEventListener("input", () => {
    const value = addressInput.value.toLowerCase().trim();
    if (value === "near me" || value === "") {
      // Keep flag as is if it's already set via button
    } else {
      isUsingCurrentLocation = false;
    }
  });
})();

// On mobile, keep panels collapsed by default for simpler experience

// (popup radius controls removed; radius +/- now inline in panels)

// Mobile filter labels no longer needed (dropdown handles this)

// Main search bar functionality
(function initMainSearch() {
  const searchInput = document.getElementById("mainSearchInput");
  const searchIcon = document.getElementById("searchIcon");
  const searchSpinner = document.getElementById("searchSpinner");
  const searchClearBtn = document.getElementById("searchClearBtn");
  const searchSubmitBtn = document.getElementById("searchSubmitBtn");
  const searchCloseBtn = document.getElementById("searchCloseBtn");
  let searchTimeout = null;
  let lastSearchQuery = "";

  if (!searchInput) return;

  // Show/hide clear button based on input
  searchInput.addEventListener("input", function () {
    if (searchClearBtn) {
      searchClearBtn.style.display = this.value ? "flex" : "none";
    }
  });

  // Clear button handler
  if (searchClearBtn) {
    searchClearBtn.addEventListener("click", function () {
      closeSidePanel(); // Close panel and reset view
      searchInput.value = "";
      searchClearBtn.style.display = "none";
      lastSearchQuery = "";
      searchInput.focus();
      // Reset to show all citations for current time filter
      filterCitationsByTime(window.currentTimeFilter || "week");
    });
  }

  // Search submit button handler
  if (searchSubmitBtn) {
    searchSubmitBtn.addEventListener("click", function () {
      const query = searchInput.value.trim();
      // If query unchanged, re-search the same thing; otherwise search new query
      if (query === lastSearchQuery && query) {
        performSearch(query);
      } else {
        performSearch(query);
        lastSearchQuery = query;
      }
    });
  }

  // Close button handler - closes side panel and returns to main view
  if (searchCloseBtn) {
    searchCloseBtn.addEventListener("click", function () {
      // If the right viewer (large image viewer) is active, close it first
      // This ensures we go directly to home without an intermediate white state
      if (document.body.classList.contains("right-viewer-active")) {
        closeSidePanelGallery();
      }
      // Close the side panel
      closeSidePanel();
      // Clear the search input
      searchInput.value = "";
      if (searchClearBtn) searchClearBtn.style.display = "none";
      lastSearchQuery = "";
      // Reset to show all citations for current time filter
      filterCitationsByTime(window.currentTimeFilter || "week");
    });
  }

  // Search on Enter key
  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const query = this.value.trim();
      performSearch(query);
      lastSearchQuery = query;
    }
  });

  // Debounced search as user types
  searchInput.addEventListener("input", function () {
    const query = this.value.trim();
    if (searchTimeout) clearTimeout(searchTimeout);

    if (query.length >= 3) {
      searchTimeout = setTimeout(() => performSearch(query), 500);
    }
  });

  function showSpinner() {
    if (searchIcon) searchIcon.style.display = "none";
    if (searchSpinner) searchSpinner.style.display = "block";
  }

  function hideSpinner() {
    if (searchIcon) searchIcon.style.display = "flex";
    if (searchSpinner) searchSpinner.style.display = "none";
  }

  async function performSearch(query) {
    if (!query) {
      lastSearchQuery = "";
      filterCitationsByTime(window.currentTimeFilter || "week");
      return;
    }

    lastSearchQuery = query;
    showSpinner();

    try {
      // Determine search type
      const isPlate = /^[A-Z]{0,2}\s*[A-Z0-9]+$/i.test(query);
      const isCitationNumber = /^\d+$/.test(query);

      let searchMode = "plate";
      let searchParams = {};

      if (isCitationNumber) {
        searchMode = "citation";
        searchParams = { citation_number: query };
      } else if (isPlate) {
        searchMode = "plate";
        // Parse plate - assume MI if no state prefix
        const parts = query.toUpperCase().split(/\s+/);
        if (parts.length >= 2 && parts[0].length <= 2) {
          searchParams = { state: parts[0], number: parts.slice(1).join("") };
        } else {
          searchParams = { state: "MI", number: query.toUpperCase() };
        }
      } else {
        // Address search - filter locally by location
        const lowerQuery = query.toLowerCase();
        const filtered = citations.filter((c) =>
          (c.location || "").toLowerCase().includes(lowerQuery)
        );
        updateMapWithResults(filtered);
        hideSpinner();
        return;
      }

      // API search
      const url = new URL("/api/search", window.location.origin);
      url.searchParams.set("mode", searchMode);
      Object.entries(searchParams).forEach(([k, v]) =>
        url.searchParams.set(k, v)
      );

      const resp = await fetch(url);
      const data = await resp.json();

      if (data.status === "success" && data.citations) {
        updateMapWithResults(data.citations);
      } else {
        updateMapWithResults([]);
      }
    } catch (err) {
      console.error("Search error:", err);
      updateMapWithResults([]);
    } finally {
      hideSpinner();
    }
  }

  function updateMapWithResults(results) {
    // Clear existing markers
    markersLayerGroup.clearLayers();
    markers.length = 0;

    // Add result markers
    results.forEach((citation) => {
      const marker = createMarkerForCitation(citation);
      if (marker) {
        markers.push(marker);
        markersLayerGroup.addLayer(marker);
      }
    });

    // Update stats pills for search results
    const searchCount = results.length.toLocaleString();
    const searchTotal = results.reduce(
      (sum, c) => sum + (parseFloat(c.amount_due) || 0),
      0
    );
    const searchTotalFormatted = formatDollarAmount(searchTotal);
    const statsPillCitations = document.getElementById(
      "statsPillCitationsValue"
    );
    const statsPillTotal = document.getElementById("statsPillTotalValue");
    if (statsPillCitations) statsPillCitations.textContent = searchCount;
    if (statsPillTotal) statsPillTotal.innerHTML = searchTotalFormatted;

    // If single result, show it
    if (results.length === 1) {
      showCitationDetails(results[0]);
      const marker = markers[0];
      if (marker) {
        map.flyTo(marker.getLatLng(), 17);
      }
    } else if (results.length > 0) {
      // Fit bounds to results
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.1));
    }
  }
})();
