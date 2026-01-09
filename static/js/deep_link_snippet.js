
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
