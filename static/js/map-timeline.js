/**
 * Map Timeline - Animated time slider showing accident clustering over time
 * Shows accidents appearing on the map as time progresses with play/pause controls
 */

class MapTimeline {
  constructor(options) {
    this.map = options.map;
    this.containerId = options.containerId || 'mapTimeline';
    this.apiEndpoint = options.apiEndpoint || '/api/v1/stats/accidents/timeline';
    
    this.data = [];
    this.markers = [];
    this.markerClusterGroup = null;
    this.currentIndex = 0;
    this.isPlaying = false;
    this.playInterval = null;
    this.playSpeed = 500; // ms between frames
    
    this.init();
  }
  
  async init() {
    this.createUI();
    await this.loadData();
    this.setupMarkerCluster();
    this.updateDisplay();
  }
  
  createUI() {
    const container = document.getElementById(this.containerId);
    if (!container) return;
    
    container.innerHTML = `
      <div class="map-timeline">
        <div class="timeline-header">
          <div class="timeline-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span data-i18n="stats.timelineTitle">Accident Timeline</span>
          </div>
          <div class="timeline-period" id="timelinePeriod">--</div>
        </div>
        
        <div class="timeline-controls">
          <button class="timeline-btn" id="timelinePlayBtn" title="Play/Pause">
            <svg class="play-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            <svg class="pause-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
              <rect x="6" y="4" width="4" height="16"></rect>
              <rect x="14" y="4" width="4" height="16"></rect>
            </svg>
          </button>
          
          <div class="timeline-slider-container">
            <input type="range" class="timeline-slider" id="timelineSlider" min="0" max="100" value="0">
            <div class="timeline-progress" id="timelineProgress"></div>
          </div>
          
          <div class="timeline-speed">
            <button class="speed-btn" id="speedDownBtn" title="Slower">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
            <span class="speed-label" id="speedLabel">1x</span>
            <button class="speed-btn" id="speedUpBtn" title="Faster">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="timeline-stats">
          <div class="timeline-stat">
            <span class="stat-value" id="timelineAccidentCount">0</span>
            <span class="stat-label" data-i18n="stats.accidentsShown">Accidents Shown</span>
          </div>
          <div class="timeline-stat">
            <span class="stat-value" id="timelineTotalCount">0</span>
            <span class="stat-label" data-i18n="stats.totalInPeriod">Total in Period</span>
          </div>
        </div>
      </div>
    `;
    
    this.bindEvents();
  }
  
  bindEvents() {
    const playBtn = document.getElementById('timelinePlayBtn');
    const slider = document.getElementById('timelineSlider');
    const speedUpBtn = document.getElementById('speedUpBtn');
    const speedDownBtn = document.getElementById('speedDownBtn');
    
    if (playBtn) {
      playBtn.addEventListener('click', () => this.togglePlay());
    }
    
    if (slider) {
      slider.addEventListener('input', (e) => {
        this.currentIndex = parseInt(e.target.value);
        this.updateDisplay();
      });
    }
    
    if (speedUpBtn) {
      speedUpBtn.addEventListener('click', () => this.changeSpeed(1));
    }
    
    if (speedDownBtn) {
      speedDownBtn.addEventListener('click', () => this.changeSpeed(-1));
    }
  }
  
  async loadData() {
    try {
      // Fetch accidents with coordinates grouped by month for timeline animation
      const response = await fetch('/api/v1/stats/timeline');
      if (!response.ok) throw new Error('Failed to load timeline data');
      
      const result = await response.json();
      console.log('MapTimeline: Loaded data', result);

      // Normalize different server formats into result.timeline = [{date,count,accidents}...]
      let timeline = [];
      if (result.timeline && Array.isArray(result.timeline)) {
        timeline = result.timeline;
      } else if (Array.isArray(result)) {
        // result is an array: could be [[date,count], ...] or [{date,count,accidents}, ...]
        if (result.length && Array.isArray(result[0]) && result[0].length >= 2) {
          timeline = result.map(r => ({ date: r[0], count: r[1], accidents: [] }));
        } else if (result.length && typeof result[0] === 'object') {
          timeline = result.map(r => ({ date: r.date || r.label || r.period, count: r.count || r.value || 0, accidents: r.accidents || [] }));
        }
      } else if (result.data && Array.isArray(result.data)) {
        timeline = result.data;
      }

      // Use the timeline data which has accidents with lat/lng
      if (timeline && Array.isArray(timeline)) {
        this.data = timeline.map(item => ({
          period: item.date || item.period,
          count: item.count || 0,
          accidents: item.accidents || [] // Each accident has lat, lng, severity
        }));
      } else {
        this.data = [];
      }
      
      // Update slider max
      const slider = document.getElementById('timelineSlider');
      if (slider && this.data.length > 0) {
        slider.max = this.data.length - 1;
        slider.value = 0;
        console.log('MapTimeline: Slider max set to', this.data.length - 1);
      }
      
    } catch (error) {
      console.error('MapTimeline: Error loading data', error);
      this.data = [];
    }
  }
  
  setupMarkerCluster() {
    if (!this.map || !window.L) return;
    
    // Create marker cluster group if Leaflet.markercluster is available
    if (window.L.markerClusterGroup) {
      this.markerClusterGroup = L.markerClusterGroup({
        chunkedLoading: true,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        maxClusterRadius: 50,
        iconCreateFunction: (cluster) => {
          const count = cluster.getChildCount();
          let size = 'small';
          let className = 'marker-cluster-small';
          
          if (count > 100) {
            size = 'large';
            className = 'marker-cluster-large';
          } else if (count > 50) {
            size = 'medium';
            className = 'marker-cluster-medium';
          }
          
          return L.divIcon({
            html: `<div><span>${count}</span></div>`,
            className: `marker-cluster ${className}`,
            iconSize: L.point(40, 40)
          });
        }
      });
      
      this.map.addLayer(this.markerClusterGroup);
    }
  }
  
  updateDisplay() {
    if (this.data.length === 0) {
      console.log('MapTimeline: No data to display');
      return;
    }
    
    const currentData = this.data[this.currentIndex];
    if (!currentData) return;
    
    console.log('MapTimeline: Displaying period', currentData.period, 'index', this.currentIndex);
    
    // Update period display
    const periodEl = document.getElementById('timelinePeriod');
    if (periodEl) {
      periodEl.textContent = this.formatPeriod(currentData.period);
    }
    
    // Update slider
    const slider = document.getElementById('timelineSlider');
    if (slider) {
      slider.value = this.currentIndex;
    }
    
    // Update progress bar
    const progress = document.getElementById('timelineProgress');
    if (progress && this.data.length > 1) {
      const percent = (this.currentIndex / (this.data.length - 1)) * 100;
      progress.style.width = `${percent}%`;
    }
    
    // Calculate cumulative accident count up to current index
    let cumulativeCount = 0;
    for (let i = 0; i <= this.currentIndex; i++) {
      cumulativeCount += (this.data[i].accidents ? this.data[i].accidents.length : this.data[i].count || 0);
    }
    
    // Update stats
    const accidentCountEl = document.getElementById('timelineAccidentCount');
    const totalCountEl = document.getElementById('timelineTotalCount');
    
    if (accidentCountEl) {
      accidentCountEl.textContent = cumulativeCount.toLocaleString();
    }
    
    if (totalCountEl) {
      const total = this.data.reduce((sum, item) => sum + (item.accidents ? item.accidents.length : item.count || 0), 0);
      totalCountEl.textContent = total.toLocaleString();
    }
    
    // Update map markers based on current time period
    this.updateMapVisualization(currentData, cumulativeCount);
  }
  
  updateMapVisualization(currentData, cumulativeCount) {
    if (!this.map) return;
    
    // Clear existing markers
    if (this.markerClusterGroup) {
      this.markerClusterGroup.clearLayers();
    }
    
    // Clear individual markers if no cluster group
    this.markers.forEach(marker => {
      this.map.removeLayer(marker);
    });
    this.markers = [];
    
    // Get all accidents up to current time period for cumulative view
    let accidentsToShow = [];
    for (let i = 0; i <= this.currentIndex; i++) {
      if (this.data[i] && this.data[i].accidents) {
        accidentsToShow = accidentsToShow.concat(this.data[i].accidents);
      }
    }
    
    console.log('MapTimeline: Showing', accidentsToShow.length, 'accidents for period', currentData.period);
    
    // Add markers for each accident with coordinates
    accidentsToShow.forEach(accident => {
      const lat = accident.lat;
      const lng = accident.lng;
      
      if (!lat || !lng) return;
      
      const marker = L.circleMarker([lat, lng], {
        radius: 7,
        fillColor: this.getSeverityColor(accident.severity),
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.7
      });
      
      marker.bindPopup(`
        <div style="min-width: 150px;">
          <strong>${accident.governorate || 'Unknown'}</strong><br>
          <small>Severity: ${accident.severity || 'N/A'}</small>
        </div>
      `);
      
      if (this.markerClusterGroup) {
        this.markerClusterGroup.addLayer(marker);
      } else {
        marker.addTo(this.map);
        this.markers.push(marker);
      }
    });
  }
  
  getSeverityColor(severity) {
    const colors = {
      'high': '#ef4444',
      'medium': '#f59e0b',
      'low': '#22c55e',
      'moderate': '#f59e0b'
    };
    return colors[severity?.toLowerCase()] || '#6366f1';
  }
  
  formatPeriod(period) {
    if (!period) return '--';
    
    // Handle YYYY-MM format
    const parts = period.split('-');
    if (parts.length === 2) {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const monthIndex = parseInt(parts[1]) - 1;
      return `${months[monthIndex] || parts[1]} ${parts[0]}`;
    }
    
    return period;
  }
  
  togglePlay() {
    this.isPlaying = !this.isPlaying;
    console.log('MapTimeline: togglePlay, isPlaying =', this.isPlaying);
    
    const playIcon = document.querySelector('#timelinePlayBtn .play-icon');
    const pauseIcon = document.querySelector('#timelinePlayBtn .pause-icon');
    
    if (this.isPlaying) {
      if (playIcon) playIcon.style.display = 'none';
      if (pauseIcon) pauseIcon.style.display = 'block';
      this.play();
    } else {
      if (playIcon) playIcon.style.display = 'block';
      if (pauseIcon) pauseIcon.style.display = 'none';
      this.pause();
    }
  }
  
  play() {
    console.log('MapTimeline: Starting playback, speed =', this.playSpeed, 'data length =', this.data.length);
    if (this.playInterval) clearInterval(this.playInterval);
    
    this.playInterval = setInterval(() => {
      this.currentIndex++;
      console.log('MapTimeline: Playing, index =', this.currentIndex, '/', this.data.length);
      
      if (this.currentIndex >= this.data.length) {
        this.currentIndex = 0; // Loop back to start
      }
      
      this.updateDisplay();
    }, this.playSpeed);
  }
  
  pause() {
    if (this.playInterval) {
      clearInterval(this.playInterval);
      this.playInterval = null;
    }
  }
  
  changeSpeed(direction) {
    const speeds = [2000, 1000, 500, 250, 100];
    const labels = ['0.25x', '0.5x', '1x', '2x', '4x'];
    
    let currentSpeedIndex = speeds.indexOf(this.playSpeed);
    if (currentSpeedIndex === -1) currentSpeedIndex = 2;
    
    currentSpeedIndex += direction;
    currentSpeedIndex = Math.max(0, Math.min(speeds.length - 1, currentSpeedIndex));
    
    this.playSpeed = speeds[currentSpeedIndex];
    
    const speedLabel = document.getElementById('speedLabel');
    if (speedLabel) {
      speedLabel.textContent = labels[currentSpeedIndex];
    }
    
    // If playing, restart with new speed
    if (this.isPlaying) {
      this.pause();
      this.play();
    }
  }
  
  destroy() {
    this.pause();
    
    if (this.markerClusterGroup) {
      this.map.removeLayer(this.markerClusterGroup);
    }
    
    this.markers.forEach(marker => {
      this.map.removeLayer(marker);
    });
    this.markers = [];
  }
}

// Export for global use
window.MapTimeline = MapTimeline;
