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
  
  // Reset search navigation state
  lastSearchResults = null;
  lastSearchQuery = "";
  isViewingSearchResultDetail = false;
  isSearchActive = false;
  unfilteredSearchResults = null;
  
  // Restore hamburger menu if it was transformed to back arrow
  const searchMenuBtn = document.getElementById("searchMenuBtn");
  if (searchMenuBtn) {
    if (searchMenuBtn._searchBackHandler) {
      searchMenuBtn.removeEventListener("click", searchMenuBtn._searchBackHandler);
      searchMenuBtn._searchBackHandler = null;
    }
    if (searchMenuBtn._originalHTML) {
      searchMenuBtn.innerHTML = searchMenuBtn._originalHTML;
      searchMenuBtn.title = "Menu";
    }
  }
  
  // Hide the X button when closing the panel
  const searchClearBtn = document.getElementById("searchClearBtn");
  if (searchClearBtn) {
    searchClearBtn.style.display = "none";
  }
  
  // Clear URL deep link if present


  // Restore Default Map View (Current Time Filter)
  // This ensures that when we close a search result or detail view, 
  // we see all citations for the current period again.
  if (typeof filterByTime === "function" && typeof currentTimeFilter !== "undefined") {
    filterByTime(currentTimeFilter);
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

// Search navigation stack - for back button in search results
let lastSearchResults = null;      // Store the search results list (after time filter)
let lastSearchQuery = "";          // Store the original query
let isViewingSearchResultDetail = false; // Track if we drilled into a result
let unfilteredSearchResults = null; // Store raw search results before time filter

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

// Show search results in side panel list
function showSearchResults(list, originalQuery = "") {
    const resultsPanel = document.getElementById("sidePanelResults");
    const resultsList = document.getElementById("resultsList");
    const resultsCount = document.getElementById("resultsCount");
    const sidePanel = document.getElementById("sidePanel");
    const sidePanelContent = document.getElementById("sidePanelContent");
    const photosHero = document.getElementById("photosHero");
    const citationTitle = document.getElementById("citationTitle");
    const searchSpinner = document.getElementById("searchSpinner");
    
    if (!resultsPanel || !resultsList) return;

    // Store results for back navigation (only if we have results)
    if (list && list.length > 0) {
        lastSearchResults = list;
        lastSearchQuery = originalQuery;
    }

    // Reset view
    resultsList.innerHTML = '';
    
    // Logic for "No results"
    if (!list || list.length === 0) {
        if (searchSpinner) searchSpinner.style.display = "none";
        
        // Show "No Results" message in the side panel
        if (sidePanel) sidePanel.classList.add('active');
        if (sidePanelContent) sidePanelContent.style.display = 'none';
        
        // Hide persistent headers
        if (photosHero) photosHero.style.display = 'none';
        if (citationTitle) citationTitle.style.display = 'none';
        
        resultsPanel.style.display = 'flex';
        
        if (resultsCount) resultsCount.textContent = "";

        // Delay showing the no-results message to allow any pending UI updates
        setTimeout(() => {
            const noResultsDiv = document.createElement('div');
            noResultsDiv.className = 'no-results-google-style';
            noResultsDiv.innerHTML = `
                <div class="no-results-header">
                    Google Maps can't find ${originalQuery || 'your search'}
                </div>
                <div class="no-results-body">
                    Make sure your search is spelled correctly. Try adding a city, state, or zip code.
                </div>
                <div class="no-results-suggestions">
                    Note: Searches are limited to Ann Arbor, MI (within 6 miles).
                </div>
            `;
            resultsList.appendChild(noResultsDiv);
            // Ensure panel is open to show this message
            document.body.classList.add('panel-open');
        }, 500);
        return;
    }

    // Update count header
    if (resultsCount) {
        resultsCount.textContent = "Results";
        resultsCount.className = "results-header-text"; // Add class for bold styling
    }

    // Populate list
    // Limit to 50 items for performance in the DOM
    const displayList = list.slice(0, 50);
    
    displayList.forEach(citation => {
        const item = document.createElement('div');
        item.className = 'result-item-google';
        
        const amount = (parseFloat(citation.amount_due) || 0).toFixed(0);
        // const dateStr = citation.issue_date ? new Date(citation.issue_date).toLocaleDateString() : 'Unknown';
        
        // Get first image URL if available
        let imageUrl = "https://maps.gstatic.com/tactile/pane/default_geocode-2x.png"; // Default placeholder
        if (citation.image_urls && citation.image_urls.length > 0) {
            // Handle both string URLs and object structure
            imageUrl = citation.image_urls[0].url || citation.image_urls[0];
        }
        
        // Determine color for meta text like "Open" in google, here maybe "Unpaid" or amount color
        const amountColor = parseFloat(citation.amount_due) >= 50 ? '#d93025' : '#188038'; // Red for high, green for low? Or just dark gray.

        item.innerHTML = `
            <div class="result-info-google">
                <div class="result-title-google">Citation #${citation.citation_number}</div>
                <div class="result-rating-row">
                    <span class="result-amount" style="color: ${amountColor}">$${amount}</span>
                    <span class="result-dot">·</span>
                    <span class="result-date">${citation.issue_date ? new Date(citation.issue_date).toLocaleDateString() : ''}</span>
                </div>
                 <div class="result-subtitle-google">${citation.location || 'Ann Arbor, MI'}</div>
                <div class="result-meta-google">
                    <span class="result-meta-icon">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style="color: #1a73e8; margin-right: 4px; vertical-align: middle;">
                             <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                        </svg>
                    </span>
                    Parking Violation
                </div>
            </div>
            <div class="result-image-container">
                <img src="${imageUrl}" class="result-thumbnail-google" alt="Citation Image" loading="lazy">
            </div>
        `;
        
        item.onclick = () => {
             // Highlight in list (optional)
             document.querySelectorAll('.result-item-google').forEach(el => el.style.backgroundColor = '');
             item.style.backgroundColor = '#e8f0fe';

            // Track that we're viewing from search results
            isViewingSearchResultDetail = true;
            
            // HIDE the results panel before showing details
            const resultsPanel = document.getElementById("sidePanelResults");
            if (resultsPanel) resultsPanel.style.display = 'none';
            
            // Show the content panel (hidden when showing results)
            const contentPanel = document.getElementById("sidePanelContent");
            if (contentPanel) contentPanel.style.display = 'block';
            
            // Show full citation details in side panel (not floating)
            showCitationDetails(citation);
            
            // Transform hamburger to back arrow for navigation
            transformSearchBtnToBack();
        };
        
        resultsList.appendChild(item);
    });
    
    if (list.length > 50) {
        const moreDiv = document.createElement('div');
        moreDiv.style.padding = '12px';
        moreDiv.style.textAlign = 'center';
        moreDiv.style.color = '#5f6368';
        moreDiv.style.fontSize = '12px';
        moreDiv.textContent = `+ ${list.length - 50} more results...`;
        resultsList.appendChild(moreDiv);
    }

    // Show results panel
    if (sidePanel) sidePanel.classList.add('active');
    if (sidePanelContent) sidePanelContent.style.display = 'none';
    
    // Hide persistent headers
    if (photosHero) photosHero.style.display = 'none';
    if (citationTitle) citationTitle.style.display = 'none';
    
    resultsPanel.style.display = 'flex';
    
    // Switch to list view mode if needed
    document.body.classList.add('panel-open');
}

// Haversine distance helper (in miles)
function getDistanceFromLatLonInMiles(lat1, lon1, lat2, lon2) {
  var R = 3959; // Radius of the earth in miles
  var dLat = deg2rad(lat2-lat1);  
  var dLon = deg2rad(lon2-lon1); 
  var a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
    Math.sin(dLon/2) * Math.sin(dLon/2)
    ; 
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
  var d = R * c; // Distance in miles
  return d;
}

function deg2rad(deg) {
  return deg * (Math.PI/180)
}

// Function to show floating citation details
function showFloatingCitationDetails(citation) {
    const floatingPanel = document.getElementById('floatingPanel');
    if (!floatingPanel) return;

    // Populate data
    const floatingTitle = document.getElementById('floatingCitationNumber');
    const floatingSub = document.getElementById('floatingCitationSub');
    const floatingDetails = document.getElementById('floatingCitationDetails');
    const floatingHero = document.getElementById('floatingHeroImage');
    const floatingPhotosHero = document.getElementById('floatingPhotosHero');
    const floatingTitleContainer = document.getElementById('floatingCitationTitle');
    
    if (floatingTitle) floatingTitle.textContent = `Citation #${citation.citation_number}`;
    if (floatingTitleContainer) floatingTitleContainer.style.display = 'block';
    
    // Determine image
    let imageUrl = null;
    let images = [];
    if (citation.image_urls) {
        // Can be string JSON or object
        if (typeof citation.image_urls === "string") {
            try { images = JSON.parse(citation.image_urls); } catch(e) {}
        } else if (Array.isArray(citation.image_urls)) {
            images = citation.image_urls;
        }
    }
    
    if (images.length > 0) {
        imageUrl = images[0].url || images[0];
    }
    
    if (imageUrl && floatingHero) {
        floatingHero.src = imageUrl;
        if (floatingPhotosHero) floatingPhotosHero.style.display = 'block';
    } else if (floatingPhotosHero) {
        // Hide hero if no image or show default?
        // Google shows street view often.
        // For now hide or show default
         floatingPhotosHero.style.display = 'none';
    }

    // Populate details content
    if (floatingDetails) {
        const amount = (parseFloat(citation.amount_due) || 0).toFixed(2);
        const dateStr = citation.issue_date ? new Date(citation.issue_date).toLocaleString() : 'Unknown';
        
        floatingDetails.innerHTML = `
            <div class="info-row">
                <div class="info-label">Location</div>
                <div class="info-value">${citation.location || 'Unknown'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Amount Due</div>
                <div class="info-value">$${amount}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Issue Date</div>
                <div class="info-value">${dateStr}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Vehicle</div>
                <div class="info-value">${citation.plate_state || ''} ${citation.plate_number || ''}</div>
            </div>
             <div class="info-row">
                <div class="info-label">Violation</div>
                <div class="info-value">${citation.violations || 'Parking Violation'}</div>
            </div>
        `;
    }
    
    // Show Floating Panel
    floatingPanel.style.display = 'flex';
    
    // Close button handler
    const closeBtn = document.getElementById('floatingCloseBtn');
    if (closeBtn) {
        closeBtn.onclick = () => {
            floatingPanel.style.display = 'none';
             // Deselect list item highlight?
             document.querySelectorAll('.result-item-google').forEach(el => el.style.backgroundColor = '');
        };
    }
}

// Transform hamburger menu to back arrow for search result navigation
function transformSearchBtnToBack() {
    const searchMenuBtn = document.getElementById("searchMenuBtn");
    if (!searchMenuBtn) return;
    
    // Store original if not already stored
    if (!searchMenuBtn._originalHTML) {
        searchMenuBtn._originalHTML = searchMenuBtn.innerHTML;
    }
    
    // Remove any existing handlers
    if (searchMenuBtn._searchBackHandler) {
        searchMenuBtn.removeEventListener("click", searchMenuBtn._searchBackHandler);
    }
    if (searchMenuBtn._galleryBackHandler) {
        searchMenuBtn.removeEventListener("click", searchMenuBtn._galleryBackHandler);
    }
    
    // Transform to back arrow
    searchMenuBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>`;
    searchMenuBtn.title = "Back to results";
    
    // Store and bind handler
    searchMenuBtn._searchBackHandler = () => goBackToSearchResults();
    searchMenuBtn.addEventListener("click", searchMenuBtn._searchBackHandler);
}

// Go back to search results list from citation detail view
function goBackToSearchResults() {
    if (!lastSearchResults || !isViewingSearchResultDetail) return;
    
    // Reset navigation state
    isViewingSearchResultDetail = false;
    
    // Restore hamburger menu
    const searchMenuBtn = document.getElementById("searchMenuBtn");
    if (searchMenuBtn) {
        if (searchMenuBtn._searchBackHandler) {
            searchMenuBtn.removeEventListener("click", searchMenuBtn._searchBackHandler);
            searchMenuBtn._searchBackHandler = null;
        }
        if (searchMenuBtn._originalHTML) {
            searchMenuBtn.innerHTML = searchMenuBtn._originalHTML;
            searchMenuBtn.title = "Menu";
        }
    }
    
    // Hide citation details, show search results list
    const sidePanelContent = document.getElementById("sidePanelContent");
    const photosHero = document.getElementById("photosHero");
    const citationTitle = document.getElementById("citationTitle");
    
    if (sidePanelContent) sidePanelContent.style.display = 'none';
    if (photosHero) photosHero.style.display = 'none';
    if (citationTitle) citationTitle.style.display = 'none';
    
    // Re-show search results list
    showSearchResults(lastSearchResults, lastSearchQuery);
}

// Handle search input
async function handleSearch(query) {
    if (!query) return;
    query = query.trim();
    
    const loadingEl = document.getElementById("searchSpinner");
    if (loadingEl) loadingEl.style.display = "block";
    
    try {
        let apiUrl = '';
        let exactMatchResults = [];
        
        // Helper function to search citations for plate matches
        function findPlateMatches(plateNumber, plateState = null) {
            const upperQuery = plateNumber.toUpperCase();
            const matches = allCitations.filter(c => {
                const citationPlate = (c.plate_number || '').toUpperCase();
                const citationState = (c.plate_state || '').toUpperCase();
                
                // Match plate number
                if (citationPlate !== upperQuery) return false;
                
                // If state specified, must match
                if (plateState && citationState !== plateState.toUpperCase()) return false;
                
                return true;
            });
            return matches;
        }
        
        // 1. Try exact plate match against loaded citations first
        // Try formats: "ABC1234", "MI ABC1234", "MIABC1234"
        
        // Format: "MI ABC1234" (state + space + plate)
        let plateMatch = query.match(/^([A-Za-z]{2})\s+([A-Za-z0-9]+)$/);
        if (plateMatch) {
            console.log("Trying exact plate match: State + Space + Plate");
            exactMatchResults = findPlateMatches(plateMatch[2], plateMatch[1]);
        }
        
        // Format: "MIABC1234" (state + plate, no space)
        if (exactMatchResults.length === 0) {
            plateMatch = query.match(/^([A-Za-z]{2})([A-Za-z0-9]+)$/);
            if (plateMatch && plateMatch[2].length >= 3) { // Ensure plate part is at least 3 chars
                console.log("Trying exact plate match: State + Plate (no space)");
                exactMatchResults = findPlateMatches(plateMatch[2], plateMatch[1]);
            }
        }
        
        // Format: Just plate number (e.g., "ABC1234")
        if (exactMatchResults.length === 0 && /^[A-Za-z0-9]{3,}$/.test(query)) {
            console.log("Trying exact plate match: Plate only");
            exactMatchResults = findPlateMatches(query);
        }
        
        // If we found exact matches, use them
        if (exactMatchResults.length > 0) {
            console.log(`Found ${exactMatchResults.length} exact plate match(es)`);
            unfilteredSearchResults = exactMatchResults;
            isSearchActive = true;
            
            // Apply current time filter to search results
            const filteredResults = filterCitationsByTime(exactMatchResults, currentTimeFilter);
            
            // Update markers and UI with filtered results
            await showOnlyMarkers(filteredResults);
            
            // If exactly one result in filtered set, show details immediately
            if (filteredResults.length === 1) {
                lastSearchResults = filteredResults;
                lastSearchQuery = query;
                showCitationDetails(filteredResults[0]);
            } else {
                showSearchResults(filteredResults, query);
            }
            
            if (loadingEl) loadingEl.style.display = "none";
            return;
        }
        
        // 2. Check for citation number (all digits)
        if (/^\d+$/.test(query)) {
            console.log("Searching by citation number");
            apiUrl = `/api/search?mode=citation&citation_number=${encodeURIComponent(query)}`;
        }
        // 3. Fallback: Try as address/location
        else {
             console.log("Attempting to geocode...");
             
             // First check our geocode endpoint
             const geoResp = await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
             if (geoResp.ok) {
                 const geoData = await geoResp.json();
                 if (geoData.status === 'success') {
                     // CHECK DISTANCE FROM ANN ARBOR CENTER
                     const AA_LAT = 42.2808;
                     const AA_LON = -83.7430;
                     const MAX_DIST_MILES = 6.0;
                     
                     const dist = getDistanceFromLatLonInMiles(AA_LAT, AA_LON, geoData.lat, geoData.lon);
                     
                     if (dist > MAX_DIST_MILES) {
                         // Too far! Show specific "No results" message for out-of-bounds
                         console.warn(`Location is ${dist.toFixed(1)} miles away. Rejecting.`);
                         showSearchResults([], query + " (outside Ann Arbor)"); // Hack to show message
                         // Actually, let's just use the no results flow, maybe trigger it manually
                         // Or better, just return empty list to trigger the "No results" UI with a custom message?
                         // Let's modify showSearchResults to handle this if we want a custom message, 
                         // but "Google Maps can't find" is also appropriate here if we consider it "not found in our valid area".
                         // For now, let's show the standard "No results" panel which now includes a hint about 6 miles.
                         showSearchResults([], query);
                         return;
                     }

                     console.log("Geocoded to:", geoData);
                     // Search by location radius
                     const radius = 100; // meters
                     apiUrl = `/api/search?mode=location&lat=${geoData.lat}&lon=${geoData.lon}&radius_m=${radius}`;
                     
                     // Move map to location
                     map.setView([geoData.lat, geoData.lon], 16);
                     
                     // REMOVED: Blue circle (searchCircle logic deleted per feedback)
                     if (searchCircle) {
                         map.removeLayer(searchCircle);
                         searchCircle = null;
                     }
                 }
             } else {
                 // Geocoding failed
                 console.log("Geocoding failed, trying address search");
                 apiUrl = `/api/search?mode=address&address=${encodeURIComponent(query)}`;
             }
        }

        if (apiUrl) {
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Store raw (unfiltered) search results for time filtering
                const rawResults = data.citations || [];
                unfilteredSearchResults = rawResults;
                isSearchActive = true;
                
                // Apply current time filter to search results
                const filteredResults = filterCitationsByTime(rawResults, currentTimeFilter);
                
                // Update markers and UI with filtered results
                await showOnlyMarkers(filteredResults);

                
                // If exactly one result in filtered set, show details immediately
                if (filteredResults.length === 1) {
                    // Manually update search state since we are skipping showSearchResults
                    lastSearchResults = filteredResults;
                    lastSearchQuery = query;
                    
                    showCitationDetails(filteredResults[0]);
                } else {
                    showSearchResults(filteredResults, query);
                }
            } else {
                // Error from API
                unfilteredSearchResults = null;
                showSearchResults([], query);
            }
        } else {
            // No API URL (e.g. Geocoding failed and didn't fall back, or distance check failed above)
            // If distance check failed, we already called showSearchResults.
            // If we got here with no API URL and no previous return, it means geocode failed hard.
            unfilteredSearchResults = null;
            showSearchResults([], query);
        }
        
    } catch (e) {
        console.error("Search error:", e);
        showSearchResults([], query);
    } finally {
        if (loadingEl) loadingEl.style.display = "none";
    }
}

// Initialize Search Listeners
(function initSearchListeners() {
    const input = document.getElementById("mainSearchInput");
    const btn = document.getElementById("searchSubmitBtn");
    const closeBtn = document.getElementById("resultsCloseBtn");
    
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                handleSearch(input.value);
            }
        });
    }
    
    if (btn) {
        btn.addEventListener("click", () => {
            if (input) handleSearch(input.value);
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
             const resultsPanel = document.getElementById("sidePanelResults");
             const content = document.getElementById("sidePanelContent");
             if (resultsPanel) resultsPanel.style.display = 'none';
             if (content) content.style.display = 'block';
             // Optionally close panel or return to default state
             closeSidePanel();
             
             // Restore all markers?
             // Maybe reload/reset filter?
             // For now just close the drawer.
        });
    }
})();

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
      

    }
  } catch (error) {
    console.error("Error loading citations:", error);
    document.getElementById("loading").textContent = "Error loading citations";
  }
}



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
    const popup = activeCitationPopup;
    // Clear the global reference immediately to avoid any race conditions
    // (though the remove event listener would also do this)
    activeCitationPopup = null;
    
    // map.closePopup() already calls removeLayer(), so we just need to close it.
    // Using the local variable ensures we don't pass null if the event fires synchronously.
    map.closePopup(popup);
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

    
    // Show citation details immediately instead of waiting for moveend
    // This fixes the "two-click" issue when switching between nearby markers
    showCitationDetails(citation);
    
    // Animate the map to the marker location (happens in parallel)
    map.flyTo([lat, lon], currentZoom, {
      animate: true,
      duration: 0.6,
      easeLinearity: 0.25,
      noMoveStart: false,
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
  const resultsPanel = document.getElementById("sidePanelResults");
  
  if (!panel || !content) return;

  // Enforce Details View State
  content.style.display = "block";
  if (resultsPanel) resultsPanel.style.display = "none";

  // Check if mobile
  const isMobile =
    window.matchMedia && window.matchMedia("(max-width: 768px)").matches;

  // ===== PRELOAD IMAGE BEFORE OPENING PANEL =====
  // Fetch images first so we can preload before showing panel
  let images = [];
  let preloadedImageUrl = null;

  // OPTIMIZATION: Check if we already have the first image URL from the list view
  if (citation.image_urls && citation.image_urls.length > 0) {
      // Use the image URL we already have!
      console.log("[image] Using pre-fetched image URL:", citation.image_urls[0].url || citation.image_urls[0]);
      // Normalize format (might be string or object depending on source)
      const url = citation.image_urls[0].url || citation.image_urls[0];
      images = [{ url: url }];
      preloadedImageUrl = url;
  }

  // Always fetch full details in background to get complete image list/comments/etc
  const fetchPromise = (async () => {
    try {
        const response = await fetch(`/api/citation/${citation.citation_number}`);
        const data = await response.json();
        
        // Support both response shapes
        let fetchedImages = [];
        if (data && Array.isArray(data.images) && data.images.length > 0) {
            fetchedImages = data.images;
        } else if (data?.citation?.images?.length > 0) {
            fetchedImages = data.citation.images;
        }
        
        return { images: fetchedImages, fullData: data };
    } catch (err) {
        console.error("Error fetching citation details:", err);
        return { images: [], fullData: null };
    }
  })();

  // Always await the fetch promise to ensure we have the complete images array
  // before setting up click handlers (fixes gallery closure issue)
  try {
      const result = await fetchPromise;
      const fetchedImages = result.images;
      
      // Update citation with full details (stats, officer info, etc)
      if (result.fullData && result.fullData.citation) {
          Object.assign(citation, result.fullData.citation);
          console.log("Updated citation with full details:", citation);
      }
      
      if (fetchedImages.length > 0) {
          images = fetchedImages;
          // Update preloadedImageUrl if we didn't have one already
          if (!preloadedImageUrl) {
              preloadedImageUrl = images[0].url;
          }
      }
  } catch (e) {
      console.error("Error awaiting fetch for images:", e);
  }

  // Now, if we have a URL, we MUST wait for it to load
  let preloadedSrc = null;
  if (preloadedImageUrl) {
      preloadedSrc = await new Promise((resolve) => {
        const preloader = new Image();
        let resolved = false;

        preloader.onload = () => {
          if (!resolved) {
            resolved = true;
            console.log("[image] Successfully preloaded:", preloadedImageUrl);
            resolve(preloader.src);
          }
        };

        preloader.onerror = (error) => {
          if (!resolved) {
            resolved = true;
            console.error("[image] Failed to preload:", preloadedImageUrl, error);
            resolve(null); 
          }
        };

        preloader.src = preloadedImageUrl;

        // Timeout for slow connections (3s)
        setTimeout(() => {
          if (!resolved) {
            resolved = true;
            console.warn("[image] Preload timeout, proceeding anyway:", preloadedImageUrl);
            resolve(preloadedImageUrl); // Try anyway on timeout
          }
        }, 3000); 
      });
  }

  // Toggle classes for layout (hero vs no hero)
  if (panel) {
      if (preloadedSrc) {
          panel.classList.remove('no-hero');
          panel.classList.add('has-hero');
      } else {
          panel.classList.add('no-hero');
          panel.classList.remove('has-hero');
      }
  }

  // ===== NOW OPEN THE PANEL (image is ready or failed) =====
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

  // Show the X button so users can close the citation and return to main view
  const searchClearBtn = document.getElementById("searchClearBtn");
  if (searchClearBtn) {
    searchClearBtn.style.display = "flex";
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
              <div class="info-value"><a href="${citation.more_info_url}" target="_blank" style="color: #00d4ff; display: flex; align-items: center; gap: 6px;">VIEW MORE INFO <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 -960 960 960" width="18px" fill="currentColor"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h560v-280h80v280q0 33-23.5 56.5T760-120H200Zm188-212-56-56 372-372H560v-80h280v280h-80v-144L388-332Z"/></svg></a></div>
            </div>
            `
                : ""
            }
           `;

  // ===== INJECT REVIEWS SECTION =====
  // Only show if we have officer info (even just a badge number is enough for "Local Guide")
  // or if we have officer_stats
  if (citation.officer_name || citation.officer_badge || citation.officer_stats) {
      const stats = citation.officer_stats || { total_citations: 1, total_photos: 1 };
      
      // Determine Avatar
      // If beat contains "UM" -> Michigan Logo
      // Else -> Ann Arbor Logo (default)
      const isUM = citation.officer_beat && citation.officer_beat.toUpperCase().includes("UM");
      // Use existing logos in static folder? We saw parking-icon.png.
      // Let's use generic placeholder URLs if we don't have specific assets yet, 
      // or try to find a public URL for Ann Arbor / UM seals.
      // For now, let's use a colored circle with initials or the parking icon as fallback.
      // Better: User mentioned "City of Ann Arbor or University of Michigan".
      const umLogo = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Michigan_Wolverines_logo.svg/1200px-Michigan_Wolverines_logo.svg.png";
      const a2Logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQYpRUBYQEElkVQY9-i_36XEVqIYQRRyhWbEA&s";
      const avatarUrl = isUM ? umLogo : a2Logo;
      
      // Determine Name
      const officerName = citation.officer_name || `Officer ${citation.officer_badge}` || "Parking Enforcement";

      // Comments Generation
      // "funny fake review from the officer"
      const commentsPool = [
          "Just doing my job, ma'am.",
          "Nothing personal, just business.",
          "Please park more carefully next time.",
          "I've seen worse parking, but not by much.",
          "This spot is for loading only.",
          "The fire hydrant is not a decoration.",
          "Sidewalks are for people, not cars.",
          "Yellow lines mean no parking.",
          "Maybe take the bus next time?",
          "I wish I didn't have to do this.",
          "Reviewing parking compliance is my passion.",
          "Another day, another citation.",
          "Excellent parking... for a monster truck rally.",
          "So close, yet so far from the curb.",
          "I waited 5 minutes before writing this.",
          "Nice car. Shame about the parking job."
      ];
      
      // Pick a random comment or based on violation type? Random is fine for "funny".
      // Let's us a simple hash of citation number to keep it consistent for the same citation
      const seed = citation.citation_number || 12345;
      const commentIndex = seed % commentsPool.length;
      const comment = commentsPool[commentIndex];
      
      // Also if we have actual violations, maybe mention them
      // "Parked in Handicapped Zone? Really?"
      
      const reviewsHtml = `
        <div class="reviews-section" style="margin-top: 24px; padding-top: 16px;">
            <div class="reviews-header" style="font-size: 16px; font-weight: 500; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
                <span>Reviews</span>
                <span style="color: #1a73e8; font-size: 14px; cursor: pointer;">Write a review</span>
            </div>
            
            <div class="review-item" style="display: flex; gap: 16px;">
                <div class="review-avatar">
                    <img src="${avatarUrl}" alt="Officer Avatar" style="width: 32px; height: 32px; border-radius: 50%; object-fit: contain; background: #fff; border: 1px solid #e0e0e0;">
                </div>
                <div class="review-content" style="flex: 1;">
                    <div class="review-author" style="font-size: 14px; font-weight: 500; color: #202124;">
                        ${officerName}
                    </div>
                    <div class="review-meta" style="font-size: 12px; color: #70757a; margin-bottom: 4px;">
                        Local Guide · ${stats.total_citations.toLocaleString()} citations · ${stats.total_photos.toLocaleString()} photos
                    </div>
                    <div class="review-stars" style="color: #fbbc04; font-size: 12px; margin-bottom: 4px;">
                        ★★★★★ <span style="color: #70757a; margin-left: 6px;">${citation.issue_date ? new Date(citation.issue_date).toLocaleDateString() : 'Recently'}</span>
                    </div>
                    <div class="review-text" style="font-size: 14px; color: #202124; line-height: 20px;">
                        ${comment}
                    </div>
                     <!-- Action buttons like Google Maps reviews -->
                     <div class="review-actions" style="display: flex; gap: 16px; margin-top: 12px;">
                        <button style="background: none; border: 1px solid #dadce0; border-radius: 16px; padding: 0 12px; height: 32px; font-size: 13px; color: #3c4043; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
                            Helpful
                        </button>
                        <button style="background: none; border: 1px solid #dadce0; border-radius: 16px; padding: 0 12px; height: 32px; font-size: 13px; color: #3c4043; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
                            Share
                        </button>
                     </div>
                </div>
            </div>
        </div>
      `;
      
      content.innerHTML += reviewsHtml;
  }

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

  if (photosHero) {
    photosHero.style.display = "block";
    
    // Check if we have a valid image URL
    if (preloadedImageUrl) {
        heroImage.src = preloadedImageUrl;
        heroImage.style.display = "block";
        heroImage.alt = images[0]?.caption || `Citation ${citation.citation_number}`;
        
        // Show "See photos" button
        if (seePhotosPopup) {
            seePhotosPopup.style.display = "flex";
        }
        
        // Enable gallery click interactions
        heroImage.style.cursor = "pointer";
        heroImage.onclick = () => {
           // wait for full images list if it's still loading in background
           if (images.length === 0 && citation.image_urls && citation.image_urls.length > 0) {
               // Fallback if full fetch hasn't finished but we have local partial
               openSidePanelGallery([{url: preloadedImageUrl}], 0, citation);
           } else {
               openSidePanelGallery(images, 0, citation);
           }
        };
        if (seePhotosPopup) {
            seePhotosPopup.onclick = (e) => {
                e.stopPropagation();
                if (images.length === 0 && citation.image_urls && citation.image_urls.length > 0) {
                     openSidePanelGallery([{url: preloadedImageUrl}], 0, citation);
                } else {
                     openSidePanelGallery(images, 0, citation);
                }
            };
        }
    } else {
        // NO IMAGES - SHOW PLACEHOLDER
        heroImage.src = "https://maps.gstatic.com/tactile/pane/default_geocode-2x.png";
        heroImage.style.display = "block";
        heroImage.alt = "No photo available";
        
        // Hide "See photos" button
        if (seePhotosPopup) {
            seePhotosPopup.style.display = "none";
        }
        
        // Disable gallery interactions
        heroImage.style.cursor = "default";
        heroImage.onclick = null;
    }
    
    if (heroLoading) heroLoading.style.display = "none";
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

// Helper: get cutoff timestamp for a time filter period
function getCutoffTimestamp(period) {
  const now = new Date();
  let cutoffTime = null;

  if (period === "hour") {
    cutoffTime = new Date(now.getTime() - 60 * 60 * 1000);
  } else if (period === "day") {
    cutoffTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  } else if (period === "week") {
    cutoffTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  }
  // else null (show all)
  return cutoffTime ? cutoffTime.getTime() : null;
}

// Helper: filter a list of citations by time period
function filterCitationsByTime(citationList, period) {
  const cutoffTimestamp = getCutoffTimestamp(period);
  if (cutoffTimestamp === null) {
    return citationList; // "all" - no filtering
  }
  return citationList.filter((c) => {
    if (!c.issue_date) return false;
    const issueTimestamp = new Date(c.issue_date).getTime();
    return issueTimestamp >= cutoffTimestamp;
  });
}

// Filter citations by time period
async function filterByTime(period) {
  currentTimeFilter = period;

  // Update dropdown value
  const filterDropdown = document.getElementById("filterDropdown");
  if (filterDropdown && filterDropdown.value !== period) {
    filterDropdown.value = period;
  }

  // Hide no results message initially
  const noResultsMsg = document.getElementById("noResultsMessage");
  noResultsMsg.classList.remove("visible");

  // If search is active, re-filter search results
  if (isSearchActive && unfilteredSearchResults) {
    const filteredSearchResults = filterCitationsByTime(unfilteredSearchResults, period);
    
    // Update markers and UI
    await showOnlyMarkers(filteredSearchResults);
    showSearchResults(filteredSearchResults, lastSearchQuery);
    
    // Show no results if empty
    if (filteredSearchResults.length === 0 && period !== "all") {
      let intervalText = getNoResultsIntervalText(period);
      document.getElementById("noResultsInterval").textContent = intervalText;
      noResultsMsg.classList.add("visible");
    }
    return;
  }

  // Normal (non-search) mode: filter all citations
  const cutoffTimestamp = getCutoffTimestamp(period);

  // Filter citations based on time period
  const filteredCitations = filterCitationsByTime(allCitations, period);

  // Update citations array to reflect filtered set
  citations = filteredCitations;

  // Clear existing markers and add filtered ones to layer group
  markersLayerGroup.clearLayers();
  await placeMarkers();

  const visibleCount = filteredCitations.length;

  // Show no results message if no citations found
  if (visibleCount === 0 && period !== "all") {
    let intervalText = getNoResultsIntervalText(period);
    document.getElementById("noResultsInterval").textContent = intervalText;
    noResultsMsg.classList.add("visible");
  } else {
    noResultsMsg.classList.remove("visible");
  }

  // Update stats based on visible citations
  updateStatsForFilter(period, cutoffTimestamp);
}

// Helper: get "no results" interval text for a period
function getNoResultsIntervalText(period) {
  if (period === "hour") {
    return "NONE FOUND IN THE LAST HOUR";
  } else if (period === "day") {
    return "NONE FOUND IN THE LAST 24 HOURS";
  } else if (period === "week") {
    return "NONE FOUND IN THE LAST WEEK";
  }
  return "";
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

  // Search on Enter key
  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const query = this.value.trim();
      performSearch(query);
      lastSearchQuery = query;
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
