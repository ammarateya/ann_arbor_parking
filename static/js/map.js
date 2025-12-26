      function closeSidePanel() {
        const panel = document.getElementById("sidePanel");
        panel.classList.remove("active");
        // Check if mobile
        const isMobile =
          window.matchMedia && window.matchMedia("(max-width: 768px)").matches;
        if (isMobile) {
          document.body.classList.remove("mobile-panel-open");
        } else {
          document.body.classList.remove("panel-open");
        }
        closeCitationPopup();
      }
      // Initialize map centered on Ann Arbor with performance optimizations
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

      // Initialize with dark theme
      currentTileLayer = L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
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
      let heatmapLayer = null; // Heatmap layer for performance
      let showHeatmap = true; // Default to heatmap, markers show at high zoom
      const MARKER_ZOOM_THRESHOLD = 17; // Show individual markers at zoom 15+

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

      const zoomRadiusBreakpoints = [
        { maxZoom: 9, radius: 100 },
        { maxZoom: 10, radius: 90 },
        { maxZoom: 11, radius: 80 },
        { maxZoom: 12, radius: 75 },
        { maxZoom: 13, radius: 60 },
        { maxZoom: 14, radius: 50 },
        { maxZoom: 15, radius: 40 },
        { maxZoom: 16, radius: 30 },
        { maxZoom: 17, radius: 20 },
        { maxZoom: 18, radius: 15 },
        { maxZoom: 19, radius: 10 },
      ];

      function getClusterRadiusForZoom(zoom) {
        for (const bp of zoomRadiusBreakpoints) {
          if (zoom < bp.maxZoom) {
            return bp.radius;
          }
        }
        return 18;
      }

      // Create marker cluster group - clustering disabled, using as a layer group for viewport optimization
      const markerClusterGroup = L.markerClusterGroup({
        maxClusterRadius: 0, // Disable clustering - show all markers individually
        spiderfyOnMaxZoom: false,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: false,
        disableClusteringAtZoom: 0, // Disable clustering at all zoom levels
        chunkedLoading: true, // Load markers in chunks for better performance
        chunkInterval: 200, // Process markers every 200ms
        chunkDelay: 50, // Delay between chunks
        iconCreateFunction: function (cluster) {
          const count = cluster.getChildCount();
          const size = count < 10 ? "small" : count < 100 ? "medium" : "large";
          const className = "marker-cluster marker-cluster-" + size;

          let totalAmount = 0;
          let hasAmounts = false;
          cluster.getAllChildMarkers().forEach(function (marker) {
            if (marker._amount !== undefined) {
              totalAmount += marker._amount;
              hasAmounts = true;
            }
          });

          let receiptWidth = 32;
          let receiptHeight = 40;
          if (count >= 50) {
            receiptWidth = 44;
            receiptHeight = 56;
          } else if (count >= 25) {
            receiptWidth = 38;
            receiptHeight = 48;
          }

          let colorClass = "";
          if (hasAmounts && count >= 10) {
            const avgAmount = totalAmount / count;
            if (avgAmount >= 40) {
              colorClass = " cluster-high-amount";
            } else if (avgAmount >= 25) {
              colorClass = " cluster-medium-amount";
            }
          }

          const totalAmountRounded = hasAmounts ? Math.round(totalAmount) : 0;
          const displayHTML =
            hasAmounts && count >= 10
              ? '<span class="cluster-count">' +
                count +
                '</span><span class="cluster-amount">$' +
                totalAmountRounded.toLocaleString() +
                "</span>"
              : '<span class="cluster-count">' + count + "</span>";

          return L.divIcon({
            html: "<div>" + displayHTML + "</div>",
            className: className + colorClass,
            iconSize: L.point(receiptWidth, receiptHeight),
            iconAnchor: L.point(receiptWidth / 2, 4),
          });
        },
      });

      // Handle cluster clicks - just zoom in instead of spiderfying
      markerClusterGroup.on("clusterclick", function (a) {
        const cluster = a.layer;
        const bounds = cluster.getBounds();
        const center = bounds.getCenter();
        // Zoom in smoothly to the cluster center
        map.flyTo(center, map.getZoom() + 2, {
          duration: 1.2,
          easeLinearity: 0.25,
        });
      });

      // Event delegation for marker clicks - single listener instead of 10,000+ individual listeners
      // This dramatically improves performance when many markers are loaded
      markerClusterGroup.on("click", function (e) {
        const marker = e.layer;
        // Check if this is a marker (not a cluster) and has citation data
        if (
          marker &&
          marker._citation &&
          marker._originalLat &&
          marker._originalLon
        ) {
          const citation = marker._citation;
          const currentZoom = map.getZoom();
          const targetLatLng = [marker._originalLat, marker._originalLon];
          const markerLatLng = marker.getLatLng();

          // Close any existing popup immediately so the next one can render
          closeCitationPopup();

          // Fly the map (without changing zoom) and show popup when movement completes
          map.flyTo(targetLatLng, currentZoom, {
            animate: true,
            duration: 0.6,
            easeLinearity: 0.25,
            noMoveStart: false,
          });

          map.once("moveend", function handleMarkerPan() {
            showCitationDetails(citation, markerLatLng);
          });
        }
      });

      markerClusterGroup.addTo(map);

      // Initialize heatmap layer
      function updateHeatmap() {
        const currentZoom = map.getZoom();

        // Remove existing heatmap if it exists
        if (heatmapLayer) {
          map.removeLayer(heatmapLayer);
          heatmapLayer = null;
        }

        // Show heatmap only when zoomed out (below threshold) and enabled
        if (
          !showHeatmap ||
          citations.length === 0 ||
          currentZoom >= MARKER_ZOOM_THRESHOLD
        ) {
          return;
        }

        // Convert citations to heatmap points [lat, lng, intensity]
        // Intensity can be based on amount_due or just count (1.0 for each citation)
        const heatmapPoints = citations
          .filter((c) => c.latitude && c.longitude)
          .map((c) => {
            const lat = parseFloat(c.latitude);
            const lon = parseFloat(c.longitude);
            // Use amount_due as intensity (normalized) or just 1.0 for count
            const amount = parseFloat(c.amount_due) || 0;
            // Normalize amount to 0.5-2.0 range for visual variety
            const intensity =
              amount > 0 ? Math.min(2.0, 0.5 + amount / 100) : 1.0;
            return [lat, lon, intensity];
          });

        if (heatmapPoints.length > 0) {
          heatmapLayer = L.heatLayer(heatmapPoints, {
            radius: 25, // Radius of each "point" in pixels
            blur: 15, // Blur factor
            maxZoom: MARKER_ZOOM_THRESHOLD, // Hide heatmap at high zoom
            max: 2.0, // Maximum intensity
            gradient: {
              0.0: "blue", // Low intensity
              0.5: "cyan", // Medium-low
              0.7: "lime", // Medium
              0.9: "yellow", // Medium-high
              1.0: "red", // High intensity
            },
          });
          heatmapLayer.addTo(map);
        }
      }

      // Update marker visibility based on zoom level
      function updateMarkerVisibility() {
        const currentZoom = map.getZoom();
        const shouldShowMarkers = currentZoom >= MARKER_ZOOM_THRESHOLD;

        if (shouldShowMarkers) {
          // Hide heatmap, show markers
          if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
            heatmapLayer = null;
          }

          // Add filtered markers if not already added
          if (markerClusterGroup.getLayers().length === 0) {
            const filteredMarkers = [];
            citations.forEach((citation) => {
              if (!citation.citation_number) return;
              const marker = citationToMarker.get(
                String(citation.citation_number)
              );
              if (marker) {
                filteredMarkers.push(marker);
              }
            });

            // Add markers in batches
            const BATCH_SIZE = 100;
            for (let i = 0; i < filteredMarkers.length; i += BATCH_SIZE) {
              const batch = filteredMarkers.slice(i, i + BATCH_SIZE);
              markerClusterGroup.addLayers(batch);
            }
          }
        } else {
          // Hide markers, show heatmap (when zoomed out)
          // Force remove all markers - use multiple methods to ensure they're gone
          const allLayers = markerClusterGroup.getLayers();
          if (allLayers.length > 0) {
            markerClusterGroup.removeLayers(allLayers);
          }
          markerClusterGroup.clearLayers();

          // Also remove from map directly if needed
          markerClusterGroup.eachLayer(function (layer) {
            map.removeLayer(layer);
          });

          // Force heatmap update to ensure it shows
          if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
            heatmapLayer = null;
          }
          updateHeatmap();
        }
      }

      // Debounce map move events to improve pan performance
      let updateTimeout;
      map.on("moveend", function () {
        clearTimeout(updateTimeout);
        updateTimeout = setTimeout(function () {
          // Update visible markers based on new viewport
          updateVisibleMarkers();
        }, 150);
      });

      // Optimize zoom performance - update heatmap/markers based on zoom level
      let zoomEndTimeout;
      let isZooming = false;
      let lastZoomLevel = map.getZoom();

      map.on("zoomstart", function () {
        isZooming = true;
        lastZoomLevel = map.getZoom();
        clearTimeout(zoomEndTimeout);
      });

      // Update during zoom when crossing threshold for immediate feedback
      map.on("zoom", function () {
        const currentZoom = map.getZoom();
        // Check if we crossed the threshold
        const wasAboveThreshold = lastZoomLevel >= MARKER_ZOOM_THRESHOLD;
        const isAboveThreshold = currentZoom >= MARKER_ZOOM_THRESHOLD;

        // If we crossed the threshold, update immediately
        if (wasAboveThreshold !== isAboveThreshold) {
          updateMarkerVisibility();
        }
        // Also update if we're zooming out below threshold (for safety)
        else if (
          !isAboveThreshold &&
          markerClusterGroup.getLayers().length > 0
        ) {
          updateMarkerVisibility();
        }

        lastZoomLevel = currentZoom;
      });

      map.on("zoomend", function () {
        isZooming = false;
        // Always update at zoom end to ensure correct state
        clearTimeout(zoomEndTimeout);
        // Call immediately, no debounce needed for zoom end
        updateMarkerVisibility();
      });

      // Disable unnecessary animations during pan/zoom for better performance
      let isPanning = false;
      map.on("movestart", function () {
        isPanning = true;
      });
      map.on("moveend", function () {
        isPanning = false;
      });

      // Search UI logic
      (function initSearchUI() {
        const toggleBtn = document.getElementById("searchToggleBtn");
        const panel = document.getElementById("searchPanel");
        const hint = document.getElementById("searchHint");
        const modeEl = document.getElementById("searchMode");
        const plateInputs = document.getElementById("plateInputs");
        const citationInputs = document.getElementById("citationInputs");
        const locationInputs = document.getElementById("locationInputs");
        const pickBtn = document.getElementById("pickLocationBtn");
        const useMyLocationBtn = document.getElementById("useMyLocationBtn");
        const searchBtn = document.getElementById("searchBtn");
        const clearBtn = document.getElementById("clearSearchBtn");
        const radiusEl = document.getElementById("searchRadiusMeters");
        let previousFilter = currentTimeFilter;

        if (toggleBtn && panel) {
          toggleBtn.addEventListener("click", () => {
            const opening = panel.style.display === "none";
            panel.style.display = opening ? "flex" : "none";
            if (!opening) {
              // Collapsing: restore previous view
              isSearchActive = false;
              if (searchCircle) {
                map.removeLayer(searchCircle);
                searchCircle = null;
              }
              showOnlyMarkers(citations);
              filterByTime(previousFilter);
              if (hint) hint.style.display = "none";
            } else {
              previousFilter = currentTimeFilter;
            }
          });
        }
        function getSinceIsoFromFilter() {
          // Map currentTimeFilter to a cutoff ISO string; return null for "all"
          try {
            if (
              currentTimeFilter === "hour" ||
              currentTimeFilter === "day" ||
              currentTimeFilter === "week"
            ) {
              const now = new Date();
              let ms = 0;
              if (currentTimeFilter === "hour") ms = 60 * 60 * 1000;
              else if (currentTimeFilter === "day") ms = 24 * 60 * 60 * 1000;
              else if (currentTimeFilter === "week")
                ms = 7 * 24 * 60 * 60 * 1000;
              const cutoff = new Date(now.getTime() - ms);
              return cutoff.toISOString();
            }
          } catch (_) {}
          return null;
        }

        function flashSearchHint() {
          const el = document.getElementById("searchHint");
          if (!el) return;
          el.style.display = "block";
          el.classList.remove("flash");
          // restart animation
          void el.offsetWidth;
          el.classList.add("flash");
          setTimeout(() => {
            el.classList.remove("flash");
            el.style.display = "none";
          }, 1800);
        }

        function updateInputs() {
          const mode = modeEl.value;
          plateInputs.style.display = mode === "plate" ? "inline-flex" : "none";
          citationInputs.style.display =
            mode === "citation" ? "inline" : "none";
          locationInputs.style.display =
            mode === "location" ? "inline-flex" : "none";
          if (mode === "location") {
            if (radiusEl) radiusEl.classList.add("highlight");
            flashSearchHint();
          } else if (hint) {
            hint.style.display = "none";
            if (radiusEl) radiusEl.classList.remove("highlight");
          }
        }

        modeEl.addEventListener("change", updateInputs);
        updateInputs();

        pickBtn.addEventListener("click", () => {
          pendingPick = true;
          document.getElementById("searchPickedLocationText").textContent =
            "tap map to set center";
          flashSearchHint();
          if (map && map._container) map._container.style.cursor = "crosshair";
        });

        // Geolocation helper
        async function getCurrentPosition() {
          return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
              return reject(new Error("geolocation not supported"));
            }
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              enableHighAccuracy: true,
              timeout: 8000,
              maximumAge: 0,
            });
          });
        }

        if (useMyLocationBtn) {
          useMyLocationBtn.addEventListener("click", async () => {
            try {
              const pos = await getCurrentPosition();
              searchCenter = {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
              };
              document.getElementById(
                "searchPickedLocationText"
              ).textContent = `center: ${searchCenter.lat.toFixed(
                5
              )}, ${searchCenter.lon.toFixed(5)}`;
              const radiusM = parseFloat(radiusEl.value || "0");
              if (searchCircle) map.removeLayer(searchCircle);
              if (radiusM > 0) {
                searchCircle = L.circle([searchCenter.lat, searchCenter.lon], {
                  radius: radiusM,
                  color: "#00d4ff",
                }).addTo(map);
              }
              map.flyTo([searchCenter.lat, searchCenter.lon], 15, {
                duration: 1.2,
                easeLinearity: 0.25,
              });
              // Auto-run search
              let url = "/api/search?mode=location";
              url += `&lat=${encodeURIComponent(
                searchCenter.lat
              )}&lon=${encodeURIComponent(
                searchCenter.lon
              )}&radius_m=${encodeURIComponent(radiusM)}`;
              const sinceIso1 = getSinceIsoFromFilter();
              if (sinceIso1) {
                url += `&since=${encodeURIComponent(sinceIso1)}`;
              }
              const resp = await fetch(url);
              const data = await resp.json();
              if (data.status !== "success") return;
              isSearchActive = true;
              const results = data.citations || [];
              showOnlyMarkers(results);
              const noResultsMsg = document.getElementById("noResultsMessage");
              const intervalEl = document.getElementById("noResultsInterval");
              if (!results.length) {
                if (intervalEl) intervalEl.textContent = "NO MATCHES FOUND";
                if (noResultsMsg) noResultsMsg.classList.add("visible");
              } else if (noResultsMsg) {
                noResultsMsg.classList.remove("visible");
              }
            } catch (_) {
              // ignore geolocation errors silently
            }
          });
        }

        map.on("click", (e) => {
          // When in location mode on mobile, allow tap-to-pick without pressing PICK
          const isLocationMode = modeEl && modeEl.value === "location";
          if (!pendingPick && !isLocationMode) return;
          pendingPick = false;
          searchCenter = { lat: e.latlng.lat, lon: e.latlng.lng };
          document.getElementById(
            "searchPickedLocationText"
          ).textContent = `center: ${searchCenter.lat.toFixed(
            5
          )}, ${searchCenter.lon.toFixed(5)}`;
          const radiusM = parseFloat(
            document.getElementById("searchRadiusMeters").value || "0"
          );
          if (searchCircle) {
            map.removeLayer(searchCircle);
          }
          if (radiusM > 0) {
            searchCircle = L.circle([searchCenter.lat, searchCenter.lon], {
              radius: radiusM,
              color: "#00d4ff",
            }).addTo(map);
          }
          if (hint) hint.style.display = "none";
          if (map && map._container) map._container.style.cursor = "";
          // Auto-run location search after picking center
          (async () => {
            try {
              const mode = "location";
              let url = "/api/search?mode=" + mode;
              const radiusM = parseFloat(radiusEl.value || "0");
              url += `&lat=${encodeURIComponent(
                searchCenter.lat
              )}&lon=${encodeURIComponent(
                searchCenter.lon
              )}&radius_m=${encodeURIComponent(radiusM)}`;
              const sinceIso2 = getSinceIsoFromFilter();
              if (sinceIso2) {
                url += `&since=${encodeURIComponent(sinceIso2)}`;
              }
              const resp = await fetch(url);
              const data = await resp.json();
              if (data.status !== "success") return;
              isSearchActive = true;
              const results = data.citations || [];
              showOnlyMarkers(results);
              if (!results.length) {
                const noResultsMsg =
                  document.getElementById("noResultsMessage");
                const intervalEl = document.getElementById("noResultsInterval");
                if (intervalEl) intervalEl.textContent = "NO MATCHES FOUND";
                if (noResultsMsg) noResultsMsg.classList.add("visible");
                return;
              }
              if (results.length === 1) {
                const only = results[0];
                const marker = citationToMarker.get(
                  String(only.citation_number)
                );
                if (marker && only.latitude && only.longitude) {
                  const lat = parseFloat(only.latitude);
                  const lon = parseFloat(only.longitude);
                  map.flyTo([lat, lon], 16, {
                    duration: 1.2,
                    easeLinearity: 0.25,
                  });
                  showCitationDetails(only, marker.getLatLng());
                }
              } else {
                const noResultsMsg =
                  document.getElementById("noResultsMessage");
                if (noResultsMsg) noResultsMsg.classList.remove("visible");
              }
            } catch (err) {
              console.error("search error", err);
            }
          })();
        });

        // Live update circle when radius changes
        radiusEl.addEventListener("input", () => {
          const val = parseFloat(radiusEl.value || "0");
          if (searchCircle && !isNaN(val)) {
            searchCircle.setRadius(val);
          }
        });

        // Inline +/- buttons for search radius
        const searchMinus = document.getElementById("searchRadiusMinus");
        const searchPlus = document.getElementById("searchRadiusPlus");
        let searchDebounce = null;
        function adjustSearchRadius(delta) {
          const current = parseFloat(radiusEl.value || "0") || 0;
          const next = Math.max(10, Math.min(100000, current + delta));
          radiusEl.value = String(Math.round(next));
          radiusEl.dispatchEvent(new Event("input"));
          if (isNaN(next) || !searchCenter) return;
          if (searchDebounce) clearTimeout(searchDebounce);
          searchDebounce = setTimeout(async () => {
            try {
              let url = "/api/search?mode=location";
              url += `&lat=${encodeURIComponent(
                searchCenter.lat
              )}&lon=${encodeURIComponent(
                searchCenter.lon
              )}&radius_m=${encodeURIComponent(next)}`;
              const sinceIso3 = getSinceIsoFromFilter();
              if (sinceIso3) {
                url += `&since=${encodeURIComponent(sinceIso3)}`;
              }
              const resp = await fetch(url);
              const data = await resp.json();
              if (data.status !== "success") return;
              isSearchActive = true;
              const results = data.citations || [];
              showOnlyMarkers(results);
              const noResultsMsg = document.getElementById("noResultsMessage");
              if (results.length === 0) {
                const intervalEl = document.getElementById("noResultsInterval");
                if (intervalEl) intervalEl.textContent = "NO MATCHES FOUND";
                if (noResultsMsg) noResultsMsg.classList.add("visible");
              } else {
                if (noResultsMsg) noResultsMsg.classList.remove("visible");
              }
            } catch (_) {}
          }, 300);
        }
        if (searchMinus)
          searchMinus.addEventListener("click", () => adjustSearchRadius(-50));
        if (searchPlus)
          searchPlus.addEventListener("click", () => adjustSearchRadius(50));

        searchBtn.addEventListener("click", async () => {
          // Reuse the same logic as auto-search
          const mode = modeEl.value;
          try {
            let url = "/api/search?mode=" + encodeURIComponent(mode);
            if (mode === "plate") {
              const state = (
                document.getElementById("searchPlateState").value || ""
              ).trim();
              const number = (
                document.getElementById("searchPlateNumber").value || ""
              ).trim();
              if (!state || !number) return;
              url += `&plate_state=${encodeURIComponent(
                state
              )}&plate_number=${encodeURIComponent(number)}`;
            } else if (mode === "citation") {
              const cnum = (
                document.getElementById("searchCitationNumber").value || ""
              ).trim();
              if (!cnum) return;
              url += `&citation_number=${encodeURIComponent(cnum)}`;
            } else if (mode === "location") {
              const radiusM = parseFloat(radiusEl.value || "0");
              if (!searchCenter) return;
              url += `&lat=${encodeURIComponent(
                searchCenter.lat
              )}&lon=${encodeURIComponent(
                searchCenter.lon
              )}&radius_m=${encodeURIComponent(radiusM)}`;
            }

            const sinceIso4 = getSinceIsoFromFilter();
            if (sinceIso4) {
              url += `&since=${encodeURIComponent(sinceIso4)}`;
            }

            const resp = await fetch(url);
            const data = await resp.json();
            if (data.status !== "success") return;

            isSearchActive = true;
            const results = data.citations || [];
            showOnlyMarkers(results);
            updateRadiusDisplay(
              mode === "location" ? radiusEl.value || "0" : null
            );

            if (!results.length) {
              const noResultsMsg = document.getElementById("noResultsMessage");
              const intervalEl = document.getElementById("noResultsInterval");
              if (intervalEl) intervalEl.textContent = "NO MATCHES FOUND";
              if (noResultsMsg) noResultsMsg.classList.add("visible");
              return;
            }

            if (results.length === 1) {
              const only = results[0];
              const marker = citationToMarker.get(String(only.citation_number));
              if (marker && only.latitude && only.longitude) {
                const lat = parseFloat(only.latitude);
                const lon = parseFloat(only.longitude);
                map.flyTo([lat, lon], 16, {
                  duration: 1.2,
                  easeLinearity: 0.25,
                });
                showCitationDetails(only, marker.getLatLng());
              }
            } else {
              const noResultsMsg = document.getElementById("noResultsMessage");
              if (noResultsMsg) noResultsMsg.classList.remove("visible");
            }
          } catch (err) {
            console.error("search error", err);
          }
        });

        clearBtn.addEventListener("click", () => {
          isSearchActive = false;
          if (searchCircle) {
            map.removeLayer(searchCircle);
            searchCircle = null;
          }
          // Reset to full dataset
          showOnlyMarkers(citations);
          filterByTime(previousFilter);
          if (panel) panel.style.display = "none";
          if (hint) hint.style.display = "none";
          const noResultsMsg = document.getElementById("noResultsMessage");
          if (noResultsMsg) noResultsMsg.classList.remove("visible");
        });
      })();

      function clearAllMarkers() {
        markerClusterGroup.clearLayers();
        markers = [];
        citationToMarker.clear();
        usedCoordinates = new Map();
      }

      async function showOnlyMarkers(list) {
        clearAllMarkers();

        // Batch marker creation for search results
        const BATCH_SIZE = 100;
        const batchMarkers = [];

        for (let i = 0; i < list.length; i++) {
          const c = list[i];
          const m = createMarkerForCitation(c);
          if (m) {
            markers.push(m);
            batchMarkers.push(m);

            if (c.citation_number) {
              citationToMarker.set(String(c.citation_number), m);
            }

            if (batchMarkers.length >= BATCH_SIZE || i === list.length - 1) {
              markerClusterGroup.addLayers(batchMarkers);
              batchMarkers.length = 0;

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
          document.getElementById("totalCitations").textContent =
            totalCount.toLocaleString();
          const totalAmount = list.reduce(
            (sum, c) => sum + (parseFloat(c.amount_due) || 0),
            0
          );
          document.getElementById("totalAmount").textContent =
            "$" +
            totalAmount.toLocaleString(undefined, {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            });

          // Legend buckets
          let redCount = 0; // >= $50
          let orangeCount = 0; // >= $30
          let greenCount = 0; // < $30
          list.forEach((citation) => {
            const amount = parseFloat(citation.amount_due) || 0;
            if (amount >= 50) redCount++;
            else if (amount >= 30) orangeCount++;
            else greenCount++;
          });
          document.getElementById("legendRed").textContent =
            redCount.toLocaleString();
          document.getElementById("legendOrange").textContent =
            orangeCount.toLocaleString();
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

          if (data.status === "success") {
            allCitations = data.citations || [];

            // Filter citations based on default time filter (week) before processing
            // This avoids showing "no results" error and applies filter during load
            const now = new Date();
            const cutoffTime = new Date(
              now.getTime() - 7 * 24 * 60 * 60 * 1000
            ); // 7 days ago
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
                document.getElementById("totalAmount").textContent = "$0";
                return;
              }
              // If just no citations in past week, that's fine - show empty state
            }

            // Update stats
            document.getElementById("totalCitations").textContent =
              citations.length.toLocaleString();
            const totalAmount = citations.reduce(
              (sum, c) => sum + (parseFloat(c.amount_due) || 0),
              0
            );
            document.getElementById("totalAmount").textContent =
              "$" +
              totalAmount.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              });

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
            document.getElementById("totalCitationsToday").textContent =
              countToday.toLocaleString();
            document.getElementById("totalAmountToday").textContent =
              "$" +
              amountToday.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              });

            // Update most recent citation time (America/Detroit)
            if (data.most_recent_citation_time) {
              const recent = new Date(data.most_recent_citation_time);
              mostRecentCitationTime = data.most_recent_citation_time; // Store for Latest link
              mostRecentCitationNumber =
                data.most_recent_citation_number || null; // Store citation number

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

            // Calculate legend counts
            let redCount = 0; // >= $50
            let orangeCount = 0; // >= $30
            let greenCount = 0; // < $30

            citations.forEach((citation) => {
              const amount = parseFloat(citation.amount_due) || 0;
              if (amount >= 50) {
                redCount++;
              } else if (amount >= 30) {
                orangeCount++;
              } else {
                greenCount++;
              }
            });

            // Update legend counts
            document.getElementById("legendRed").textContent =
              redCount.toLocaleString();
            document.getElementById("legendOrange").textContent =
              orangeCount.toLocaleString();
            document.getElementById("legendGreen").textContent =
              greenCount.toLocaleString();

            // Geocode and place markers
            await placeMarkers();

            // Hide loading
            document.getElementById("loading").style.display = "none";
          }
        } catch (error) {
          console.error("Error loading citations:", error);
          document.getElementById("loading").textContent =
            "Error loading citations";
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
          console.warn(
            "Citation missing coordinates:",
            citation.citation_number
          );
          return null;
        }

        const originalLat = parseFloat(citation.latitude);
        const originalLon = parseFloat(citation.longitude);

        // Get offset coordinates if duplicates exist
        const { lat, lon } = getOffsetCoordinates(originalLat, originalLon);

        // Create custom icon - Minimal style with performance optimizations
        const amount = parseFloat(citation.amount_due) || 0;
        const color = getColorForAmount(citation.amount_due);
        const currentZoom = map.getZoom();
        // Use smaller markers at lower zoom levels for better performance
        let size;
        if (currentZoom < 13) {
          size = amount >= 50 ? 6 : amount >= 30 ? 5 : 4;
        } else if (currentZoom < 15) {
          size = amount >= 50 ? 8 : amount >= 30 ? 7 : 6;
        } else {
          size = amount >= 50 ? 12 : amount >= 30 ? 10 : 8;
        }
        const borderColor =
          amount >= 50 ? "#ff0040" : amount >= 30 ? "#ff8000" : "#00d4ff";

        // Use simpler icon HTML for better performance
        const customIcon = L.divIcon({
          className: "custom-marker",
          html: `<div style="width:${size}px;height:${size}px;background:${color};border:1px solid ${borderColor};"></div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
          // Optimize rendering
          popupAnchor: [0, -size / 2],
        });

        // Create marker - don't bind popup until clicked (lazy loading for performance)
        const marker = L.marker([lat, lon], {
          icon: customIcon,
          // Performance options
          riseOnHover: false, // Don't raise markers on hover (expensive)
          keyboard: false, // Disable keyboard navigation for markers (minor perf gain)
        });

        // Calculate font size based on citation number length
        const citationNumStr = String(citation.citation_number || "");
        const digitCount = citationNumStr.replace(/\D/g, "").length;
        let fontSize = "12px";
        if (digitCount >= 7) {
          fontSize = "9px";
        } else if (digitCount === 6) {
          fontSize = "10px";
        } else if (digitCount === 5) {
          fontSize = "11px";
        }

        const popupContent = `
                    <strong style="font-size: ${fontSize};">▶ CITATION #${
          citation.citation_number
        }</strong><br>
                    ──────────────────────<br>
                    LOC: ${citation.location || "UNKNOWN"}<br>
                    AMT: $${(parseFloat(citation.amount_due) || 0).toFixed(
                      2
                    )}<br>
                    PLT: ${citation.plate_state || ""} ${
          citation.plate_number || ""
        }<br>
                    ──────────────────────
                `;

        // Store popup content but don't bind until needed
        marker._popupContent = popupContent;
        // Store amount for cluster calculations
        marker._amount = amount;
        // Store citation data on marker for event delegation (performance optimization)
        marker._citation = citation;
        marker._originalLat = originalLat;
        marker._originalLon = originalLon;

        // Keep reference to the marker by citation number
        if (citation.citation_number) {
          citationToMarker.set(String(citation.citation_number), marker);
        }

        // REMOVED: Individual click listener - now using event delegation on markerClusterGroup
        // This reduces from 10,000+ listeners to just 1 listener for better performance

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
            if (match)
              console.log("Found citation by number:", c.citation_number);
            return match;
          });

          if (!latest) {
            console.log(
              "Citation not found in loaded array, attempting to fetch..."
            );
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
                console.log(
                  "Fetched citation from API:",
                  latest.citation_number
                );
                // Add it to the citations array and create a marker for it
                if (
                  !citations.find(
                    (c) =>
                      String(c.citation_number) ===
                      String(latest.citation_number)
                  )
                ) {
                  citations.push(latest);
                  const marker = createMarkerForCitation(latest);
                  if (marker) {
                    markers.push(marker);
                    if (latest.citation_number) {
                      citationToMarker.set(
                        String(latest.citation_number),
                        marker
                      );
                    }
                    markerClusterGroup.addLayer(marker);
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
                  console.log(
                    "Found citation by timestamp:",
                    c.citation_number
                  );
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
            markerClusterGroup.addLayer(newMarker);
            showCitationDetails(latest, newMarker.getLatLng());
          }
        } else {
          console.warn(
            "Citation found but no coordinates:",
            latest.citation_number
          );
        }
      }

      // Get color based on amount - Minimal opacity
      function getColorForAmount(amount) {
        const amt = parseFloat(amount) || 0;
        if (amt >= 50) return "rgba(255, 0, 64, 0.7)"; // Red with opacity
        if (amt >= 30) return "rgba(255, 128, 0, 0.7)"; // Orange with opacity
        return "rgba(0, 212, 255, 0.7)"; // Cyan with opacity
      }

      // Place all markers - creates markers for all citations but only adds filtered ones to map
      async function placeMarkers() {
        // Clear existing markers
        markerClusterGroup.clearLayers();
        markers = [];
        citationToMarker.clear();
        usedCoordinates.clear();

        // Create markers for ALL citations (so they're ready when switching filters)
        // But only add the filtered ones (citations array) to the cluster group
        const BATCH_SIZE = 100; // Process 100 markers at a time
        const batchMarkersToAdd = [];

        // Performance optimization: Create Set of filtered citation numbers for O(1) lookup
        // Instead of O(n) array.some() check for each marker (was O(n²) overall)
        const filteredCitationNumbers = new Set(
          citations.map((c) => String(c.citation_number))
        );

        // First, create markers for all citations
        // Initially show all filtered markers; viewport filtering will handle updates on pan/zoom
        for (let i = 0; i < allCitations.length; i++) {
          const citation = allCitations[i];
          const marker = createMarkerForCitation(citation);
          if (marker) {
            markers.push(marker);

            // Store in map for filtering/search
            if (citation.citation_number) {
              citationToMarker.set(String(citation.citation_number), marker);
            }

            // If this citation is in the filtered set, mark it for adding
            if (filteredCitationNumbers.has(String(citation.citation_number))) {
              batchMarkersToAdd.push(marker);
            }

            // Batch add filtered markers to cluster group (only if zoomed in enough)
            if (
              batchMarkersToAdd.length >= BATCH_SIZE ||
              i === allCitations.length - 1
            ) {
              // Don't add markers here - updateMarkerVisibility will handle it based on zoom
              batchMarkersToAdd.length = 0;

              // Yield to browser to prevent blocking
              await new Promise((resolve) => requestAnimationFrame(resolve));
            }
          }
        }

        // Update marker/heatmap visibility based on current zoom level
        updateMarkerVisibility();
      }

      // Update visible markers based on current viewport (performance optimization)
      async function updateVisibleMarkers() {
        if (markers.length === 0) return;

        // Don't update markers if we're below zoom threshold (should show heatmap instead)
        const currentZoom = map.getZoom();
        if (currentZoom < MARKER_ZOOM_THRESHOLD) {
          // If markers are visible but shouldn't be, clear them
          if (markerClusterGroup.getLayers().length > 0) {
            markerClusterGroup.clearLayers();
          }
          return;
        }

        const bounds = map.getBounds();
        const padding = 0.1; // 10% padding
        const extendedBounds = L.latLngBounds(
          [
            bounds.getSouth() -
              (bounds.getNorth() - bounds.getSouth()) * padding,
            bounds.getWest() - (bounds.getEast() - bounds.getWest()) * padding,
          ],
          [
            bounds.getNorth() +
              (bounds.getNorth() - bounds.getSouth()) * padding,
            bounds.getEast() + (bounds.getEast() - bounds.getWest()) * padding,
          ]
        );

        // Get currently visible markers
        const currentlyVisible = new Set();
        markerClusterGroup.eachLayer(function (marker) {
          if (marker.getLatLng) {
            currentlyVisible.add(marker);
          }
        });

        // Determine which markers should be visible
        const shouldBeVisible = new Set();
        const markersToAdd = [];
        const markersToRemove = [];

        // Check all markers
        for (const marker of markers) {
          if (!marker._citation) continue;

          const citation = marker._citation;
          const markerLat = parseFloat(citation.latitude);
          const markerLon = parseFloat(citation.longitude);

          // Check if marker should be visible (in viewport and in filtered set)
          const isInFilteredSet = citations.some(
            (c) =>
              String(c.citation_number) === String(citation.citation_number)
          );
          const isInViewport = extendedBounds.contains([markerLat, markerLon]);

          if (isInFilteredSet && isInViewport) {
            shouldBeVisible.add(marker);
            if (!currentlyVisible.has(marker)) {
              markersToAdd.push(marker);
            }
          } else if (currentlyVisible.has(marker)) {
            markersToRemove.push(marker);
          }
        }

        // Batch remove markers outside viewport
        if (markersToRemove.length > 0) {
          markerClusterGroup.removeLayers(markersToRemove);
        }

        // Batch add markers in viewport
        if (markersToAdd.length > 0) {
          const BATCH_SIZE = 100;
          for (let i = 0; i < markersToAdd.length; i += BATCH_SIZE) {
            const batch = markersToAdd.slice(i, i + BATCH_SIZE);
            markerClusterGroup.addLayers(batch);
            if (i + BATCH_SIZE < markersToAdd.length) {
              await new Promise((resolve) => requestAnimationFrame(resolve));
            }
          }
        }
      }

      // Focus map on markers
      function focusMap() {
        if (markers.length > 0) {
          // Use the cluster group to get bounds (more efficient)
          if (markerClusterGroup.getLayers().length > 0) {
            map.fitBounds(markerClusterGroup.getBounds().pad(0.1));
          } else {
            // Fallback to feature group if cluster is empty
            const group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
          }
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
      function showCitationDetails(citation, markerLatLng = null) {
        if (!citation) return;
        const panel = document.getElementById("sidePanel");
        const title = document.getElementById("sidePanelTitle");
        const content = document.getElementById("sidePanelContent");
        if (!panel || !title || !content) return;

        // Check if mobile
        const isMobile =
          window.matchMedia && window.matchMedia("(max-width: 768px)").matches;

        if (isMobile) {
          // On mobile: just slide up from bottom, no layout shift
          panel.classList.add("active");
          document.body.classList.add("mobile-panel-open"); // For map controls positioning
          // Don't add panel-open class on mobile to prevent layout shifts
        } else {
          // On desktop: shift layout as before
          panel.classList.add("active");
          document.body.classList.add("panel-open");
        }

        // Calculate font size for title based on citation number length
        const citationNumStr = String(citation.citation_number || "");
        const digitCount = citationNumStr.replace(/\D/g, "").length;
        let titleFontSize = "12px"; // Default
        if (digitCount >= 7) {
          titleFontSize = "9px";
        } else if (digitCount === 6) {
          titleFontSize = "10px";
        } else if (digitCount === 5) {
          titleFontSize = "11px";
        }
        title.textContent = `CITATION #${citation.citation_number}`;
        title.style.fontSize = titleFontSize;

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
        showCitationPopup(citation, markerLatLng);
      }

      // Toggle between heatmap and markers view
      function toggleHeatmap() {
        showHeatmap = !showHeatmap;
        const toggleBtn = document.getElementById("heatmapToggle");

        if (showHeatmap) {
          // Show heatmap, hide markers
          markerClusterGroup.clearLayers();
          toggleBtn.textContent = "MARKERS";
          toggleBtn.classList.add("active");
        } else {
          // Show markers, hide heatmap
          if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
            heatmapLayer = null;
          }
          toggleBtn.textContent = "HEATMAP";
          toggleBtn.classList.remove("active");

          // Re-add filtered markers
          const filteredMarkers = [];
          citations.forEach((citation) => {
            if (!citation.citation_number) return;
            const marker = citationToMarker.get(
              String(citation.citation_number)
            );
            if (marker) {
              filteredMarkers.push(marker);
            }
          });

          // Add markers in batches
          const BATCH_SIZE = 100;
          for (let i = 0; i < filteredMarkers.length; i += BATCH_SIZE) {
            const batch = filteredMarkers.slice(i, i + BATCH_SIZE);
            markerClusterGroup.addLayers(batch);
          }
        }

        // Update the display
        updateHeatmap();
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

        // Update button states
        document.querySelectorAll(".time-filter-btn").forEach((btn) => {
          btn.classList.remove("active");
          if (btn.dataset.time === period) {
            btn.classList.add("active");
          }
        });

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

        // Clear existing markers/heatmap - updateMarkerVisibility will handle showing the right one
        markerClusterGroup.clearLayers();
        if (heatmapLayer) {
          map.removeLayer(heatmapLayer);
          heatmapLayer = null;
        }

        // Update marker/heatmap visibility based on current zoom level
        updateMarkerVisibility();

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
          document.getElementById("noResultsInterval").textContent =
            intervalText;
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
        document.getElementById("totalCitations").textContent =
          filteredCitations.length.toLocaleString();
        const totalAmount = filteredCitations.reduce(
          (sum, c) => sum + (parseFloat(c.amount_due) || 0),
          0
        );
        document.getElementById("totalAmount").textContent =
          "$" +
          totalAmount.toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          });

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

        document.getElementById("legendRed").textContent =
          redCount.toLocaleString();
        document.getElementById("legendOrange").textContent =
          orangeCount.toLocaleString();
        document.getElementById("legendGreen").textContent =
          greenCount.toLocaleString();
      }

      // Initialize filter button - set "week" as active (default view)
      (function initFilterButtons() {
        const filterAllBtn = document.getElementById("filterAll");
        const filterWeekBtn = document.getElementById("filterWeek");
        if (filterAllBtn) {
          filterAllBtn.classList.remove("active");
        }
        if (filterWeekBtn) {
          filterWeekBtn.classList.add("active");
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
        const useMyLocationBtn = document.getElementById(
          "notifyUseMyLocationBtn"
        );
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
          const email = (
            document.getElementById("notifyEmail").value || ""
          ).trim();
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
          if (savedEmail)
            document.getElementById("notifyEmail").value = savedEmail;
        } catch (_) {}
      })();

      // Risk Score UI
      (function initRiskScoreUI() {
        const toggleBtn = document.getElementById("riskScoreToggleBtn");
        const panel = document.getElementById("riskScorePanel");
        const calculateBtn = document.getElementById("riskCalculateBtn");
        const useMyLocationBtn = document.getElementById(
          "riskUseMyLocationBtn"
        );
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
            riskMarker = L.marker(
              [data.coordinates.lat, data.coordinates.lon],
              {
                icon: L.divIcon({
                  className: "custom-marker",
                  html: `<div style="background: ${riskColor}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 10px ${riskColor};"></div>`,
                  iconSize: [14, 14],
                  iconAnchor: [7, 7],
                }),
              }
            ).addTo(map);

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

      (function updateMobileFilterLabels() {
        function setLabels(isMobile) {
          if (isMobile) {
            document.getElementById("filterAll").textContent = "ALL";
            document.getElementById("filterWeek").textContent = "WK";
            document.getElementById("filterDay").textContent = "24H";
            document.getElementById("filterHour").textContent = "1H";
          } else {
            document.getElementById("filterAll").textContent = "ALL";
            document.getElementById("filterWeek").textContent = "PAST WEEK";
            document.getElementById("filterDay").textContent = "PAST 24 HOURS";
            document.getElementById("filterHour").textContent = "PAST HOUR";
          }
          if (typeof scheduleTopOffsetUpdate === "function") {
            scheduleTopOffsetUpdate();
          }
        }
        function checkWidth() {
          setLabels(window.innerWidth <= 768);
        }
        window.addEventListener("resize", checkWidth);
        checkWidth();
      })();
