let severityChart, causeChart, timeChart, delegationChart, statusChart, confirmedReportedChart;
let severityGovChart, severityDelChart, causeSeverityChart;
let smallMultipleCharts = [];
let sparklineCharts = [];
let timelineLabels = [];
let zoomChart = null;
// cache the light tooltip config so we can swap colors for dark mode
const baseTooltip = { ...ChartTheme.tooltip };
// paging state shared across controls
let currentPage = 1;
let pages = [];
let carouselIndex = 0;
let carouselPages = [];
let touchStartX = null;

function applyChartModeTheme() {
  const isDark = document.body.classList.contains('dark-mode');
  const textColor = isDark ? '#f5f7fa' : '#0f172a';
  const gridColor = isDark ? 'rgba(255,255,255,0.16)' : 'rgba(15,23,42,0.08)';
  const borderColor = isDark ? 'rgba(255,255,255,0.28)' : 'rgba(15,23,42,0.15)';
  Chart.defaults.color = textColor;
  Chart.defaults.borderColor = borderColor;
  if (!Chart.defaults.scale) Chart.defaults.scale = {};
  Chart.defaults.scale.grid = Chart.defaults.scale.grid || {};
  Chart.defaults.scale.grid.color = gridColor;
  Chart.defaults.scale.ticks = Chart.defaults.scale.ticks || {};
  Chart.defaults.scale.ticks.color = textColor;
  Chart.defaults.plugins = Chart.defaults.plugins || {};
  Chart.defaults.plugins.legend = Chart.defaults.plugins.legend || {};
  Chart.defaults.plugins.legend.labels = Chart.defaults.plugins.legend.labels || {};
  Chart.defaults.plugins.legend.labels.color = textColor;
  // adjust tooltip theme
  if (isDark) {
    ChartTheme.tooltip = {
      backgroundColor: '#0b1220',
      titleColor: '#f5f7fa',
      bodyColor: '#e5e7eb',
      borderColor: 'rgba(255,255,255,0.16)',
      borderWidth: 1,
      padding: 10,
      displayColors: false,
      titleFont: { weight: '600' },
      bodyFont: { weight: '400' }
    };
  } else {
    ChartTheme.tooltip = { ...baseTooltip };
  }
  // refresh existing charts to pick up new colors
  try {
    const charts = Object.values(Chart.instances || {});
    charts.forEach(c => {
      if (!c || !c.options) return;
      if (c.options.plugins && c.options.plugins.legend && c.options.plugins.legend.labels) {
        c.options.plugins.legend.labels.color = textColor;
      }
      if (c.options.scales) {
        Object.values(c.options.scales).forEach(s => {
          if (!s) return;
          if (!s.ticks) s.ticks = {};
          s.ticks.color = textColor;
          if (!s.grid) s.grid = {};
          s.grid.color = gridColor;
        });
      }
      c.options.borderColor = borderColor;
      c.update('none');
    });
  } catch (e) { /* non-fatal */ }
}

function openChartZoom(canvasEl) {
  try {
    let inst = Chart.getChart(canvasEl);
    if (!inst && Chart.instances) {
      try {
        const list = Object.values(Chart.instances || {});
        inst = list.find(c => c && c.canvas === canvasEl);
      } catch (e) { /* ignore */ }
    }
    if (!inst) return;
    const overlay = document.getElementById('chartZoomOverlay');
    const zoomCanvas = document.getElementById('chartZoomCanvas');
    const zoomBody = document.getElementById('chartZoomBody');
    const zoomImg = document.getElementById('chartZoomImg');
    const titleEl = document.getElementById('chartZoomTitle');
    if (!overlay || !zoomCanvas) return;
    // destroy prior zoom chart
    if (zoomChart) { try { zoomChart.destroy(); } catch (e) {} zoomChart = null; }
    // reset displays
    if (zoomCanvas) zoomCanvas.style.display = 'block';
    if (zoomImg) zoomImg.style.display = 'none';
    applyChartModeTheme();
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';

    // Set chart title based on canvas
    if (titleEl) {
      const chartTitles = {
        'timeChart': 'Accidents Over Time',
        'severityChart': 'By Severity',
        'causeChart': 'By Cause',
        'delegationChart': 'Top Delegations',
        'statusChart': 'By Status',
        'severityGovChart': 'Severity by Governorate',
        'severityDelChart': 'Severity by Delegation',
        'causeSeverityChart': 'Cause by Severity',
        'confirmedReportedChart': 'Confirmed vs Reported'
      };
      titleEl.textContent = chartTitles[canvasEl.id] || 'Chart';
    }

    // build chart after overlay is visible to get correct dimensions
    requestAnimationFrame(() => {
      // size canvas to available body area
      if (zoomBody) {
        const rect = zoomBody.getBoundingClientRect();
        zoomCanvas.width = Math.max(400, rect.width - 40);
        zoomCanvas.height = Math.max(300, rect.height - 40);
      }
      const ctx = zoomCanvas.getContext('2d');
      // clone options safely (structuredClone can fail on functions in callbacks)
      let clonedOptions;
      try {
        clonedOptions = (typeof structuredClone === 'function') ? structuredClone(inst.options || {}) : JSON.parse(JSON.stringify(inst.options || {}));
      } catch (cloneErr) {
        try { clonedOptions = JSON.parse(JSON.stringify(inst.options || {})); }
        catch (_) { clonedOptions = {}; }
      }
      clonedOptions.responsive = false;
      clonedOptions.maintainAspectRatio = false;
      clonedOptions.animation = false;

      // rebuild datasets so gradients become valid on the new canvas
      const palette = (ChartTheme.colors && ChartTheme.colors.severity) ? ChartTheme.colors.severity : [ChartTheme.palette.primaryA, ChartTheme.palette.primaryB, ChartTheme.palette.success];
      function darken(hex, amount = 0.2) {
        if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) return hex;
        const h = hex.replace('#','');
        if (h.length !== 6) return hex;
        const num = parseInt(h, 16);
        const r = Math.max(0, Math.min(255, Math.floor((num >> 16) * (1 - amount))));
        const g = Math.max(0, Math.min(255, Math.floor(((num >> 8) & 0xff) * (1 - amount))));
        const b = Math.max(0, Math.min(255, Math.floor((num & 0xff) * (1 - amount))));
        const toHex = (v) => v.toString(16).padStart(2, '0');
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
      }
      function cloneColor(val, fallback){
        const base = fallback || '#3b82f6';
        if (typeof val === 'string') return val;
        if (Array.isArray(val)) return val.map(v => (typeof v === 'string') ? v : base);
        if (val && typeof val === 'object') return makeGradient(ctx, base, darken(base, 0.22));
        return base;
      }
      const clonedData = { labels: inst.data && inst.data.labels ? [...inst.data.labels] : [] , datasets: [] };
      const full = inst._fullData; // optional richer data for zoom (e.g., full cause list)
      if (full && full.labels && full.values) {
        clonedData.labels = [...full.labels];
        const ds0 = (inst.data && inst.data.datasets && inst.data.datasets[0]) || {};
        const baseColor = Array.isArray(ds0.borderColor) ? (ds0.borderColor[0] || palette[0]) : (ds0.borderColor || palette[0] || '#3b82f6');
        clonedData.datasets.push({
          type: ds0.type || inst.config.type || 'bar',
          data: [...full.values],
          backgroundColor: full.colors || cloneColor(ds0.backgroundColor, baseColor),
          borderColor: cloneColor(ds0.borderColor, baseColor),
          borderRadius: ds0.borderRadius,
          borderSkipped: ds0.borderSkipped,
          barThickness: ds0.barThickness,
          maxBarThickness: ds0.maxBarThickness,
          categoryPercentage: ds0.categoryPercentage,
          barPercentage: ds0.barPercentage,
        });
      } else {
        (inst.data && inst.data.datasets || []).forEach((ds, idx) => {
          const baseColor = Array.isArray(ds.borderColor) ? (ds.borderColor[0] || palette[idx % palette.length]) : (ds.borderColor || palette[idx % palette.length] || '#3b82f6');
          const copy = { ...ds };
          copy.data = Array.isArray(ds.data) ? [...ds.data] : ds.data;
          copy.backgroundColor = cloneColor(ds.backgroundColor, baseColor);
          copy.borderColor = cloneColor(ds.borderColor, baseColor);
          clonedData.datasets.push(copy);
        });
      }
      try {
        zoomChart = new Chart(ctx, {
          type: inst.config.type,
          data: clonedData,
          options: clonedOptions,
          plugins: inst.config.plugins || [],
        });
      } catch (e) {
        console.warn('zoom chart clone failed, using snapshot', e);
      }
      if (titleEl) {
        // derive title from chart title plugin or canvas aria-label/id
        const friendly = {
          severityChart: 'Accidents by Severity',
          causeChart: 'Accidents by Cause',
          timeChart: 'Accidents Over Time',
          delegationChart: 'Accidents by Delegation',
          statusChart: 'Report Status',
          severityGovChart: 'Severity by Governorate',
          severityDelChart: 'Severity by Delegation',
          causeSeverityChart: 'Causes by Severity',
          confirmedReportedChart: 'Reported vs Confirmed'
        };
        const t = (inst.options && inst.options.plugins && inst.options.plugins.title && inst.options.plugins.title.text)
          || canvasEl.getAttribute('aria-label')
          || friendly[canvasEl.id]
          || canvasEl.id
          || 'Chart';
        titleEl.textContent = Array.isArray(t) ? t.join(' ') : t;
      }
      try {
        // ensure chart actually rendered; if datasets missing or constructor failed, fallback to image
        if (!zoomChart || !(clonedData.datasets || []).length) {
          throw new Error('zoom chart missing datasets');
        }
      } catch (err) {
        // fallback: snapshot original chart image
        try {
          const imgData = inst.toBase64Image();
          if (zoomImg) { zoomImg.src = imgData; zoomImg.style.display = 'block'; }
          if (zoomCanvas) zoomCanvas.style.display = 'none';
        } catch (e) {
          console.warn('zoom fallback failed', e);
        }
      }
    });
  } catch (e) { console.warn('openChartZoom failed', e); }
}

function closeChartZoom() {
  const overlay = document.getElementById('chartZoomOverlay');
  if (zoomChart) { try { zoomChart.destroy(); } catch (e) {} zoomChart = null; }
  if (overlay) overlay.classList.remove('show');
  document.body.style.overflow = '';
}

function ensureZoomBinding(el) {
  if (!el || el.dataset.zoomBound === '1') return;
  el.dataset.zoomBound = 'binding';
  const tryBind = (attempts = 0) => {
    const inst = Chart.getChart(el) || (Object.values(Chart.instances || {}).find(c => c && c.canvas === el));
    if (!inst) {
      if (attempts < 20) { requestAnimationFrame(() => tryBind(attempts + 1)); }
      else {
        el.dataset.zoomBound = '';
        // retry once later in case chart renders after data fetch
        setTimeout(() => { if (el.dataset.zoomBound !== '1') tryBind(0); }, 800);
      }
      return;
    }
    el.dataset.zoomBound = '1';
    el.style.cursor = 'pointer';
    el.addEventListener('click', (ev) => { ev.stopPropagation(); openChartZoom(el); });
  };
  tryBind();
}

function initZoomHandlers() {
  try {
    // initial bind for existing canvases
    document.querySelectorAll('.chart-canvas').forEach(ensureZoomBinding);
    // observe new canvases added later
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(m => {
        m.addedNodes.forEach(node => {
          if (node.classList && node.classList.contains('chart-canvas')) {
            ensureZoomBinding(node);
          } else if (node.querySelectorAll) {
            node.querySelectorAll('.chart-canvas').forEach(ensureZoomBinding);
          }
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });

    const overlay = document.getElementById('chartZoomOverlay');
    const closeBtn = document.getElementById('chartZoomClose');
    if (closeBtn) closeBtn.addEventListener('click', closeChartZoom);
    if (overlay) overlay.addEventListener('click', (ev) => { if (ev.target === overlay) closeChartZoom(); });
    document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') closeChartZoom(); });
  } catch (e) { console.warn('initZoomHandlers failed', e); }
}

// small helper to display cause labels as human readable (replace underscores with spaces)
function prettifyLabel(s) {
  if (s === undefined || s === null) return '';
  return String(s).replace(/_/g, ' ');
}

// selection state for highlighted map feature
let selectedMapLayer = null;
let tempHighlightLayer = null;
let spotlightOverlay = null; // soft radial dim outside selection
let spotlightPane = null;
let selectionPin = null;
let selectedCenter = null;
let selectedBounds = null;
function resetSelectionStyle() {
  try {
    if (selectedMapLayer) {
      // polygons have setStyle, markers have setStyle as well
      if (selectedMapLayer.setStyle && selectedMapLayer.defaultStyle) {
        selectedMapLayer.setStyle(selectedMapLayer.defaultStyle);
      } else if (selectedMapLayer.setStyle) {
        // attempt to reset common properties
        selectedMapLayer.setStyle({ color: '#fff', weight: 1 });
      }
    }
    selectedMapLayer = null;
    selectedCenter = null;
    selectedBounds = null;
    if (tempHighlightLayer && mapObj) { try { mapObj.removeLayer(tempHighlightLayer); } catch (e) {} tempHighlightLayer = null; }
    if (selectionPin && mapObj) { try { mapObj.removeLayer(selectionPin); } catch (e) {} selectionPin = null; }
    clearSpotlight();
    showRegionInfo(null);
  } catch (e) { /* ignore */ }
}

function normalizeName(n) {
  if (!n) return '';
  return n.toString().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/gi, '').toLowerCase();
}

function findLayerByName(name) {
  if (!mapLayer) return null;
  const target = normalizeName(name);
  let found = null;
  const walk = (layer) => {
    if (found || !layer) return;
    try {
      const props = (layer.feature && layer.feature.properties) || {};
      const opts = layer.options || {};
      const lname = props.name || props.NAME || props.gov_name || props.governorate || props.delegation || props.deleg || opts.name || opts.label || opts.title || opts._name;
      if (normalizeName(lname) === target) {
        found = layer; return;
      }
      if (layer.getLayers) {
        const kids = layer.getLayers();
        if (kids && kids.length) kids.forEach(walk);
      }
    } catch (e) { /* ignore */ }
  };
  walk(mapLayer);
  return found;
}

function focusGovernorate(name) {
  try {
    if (!name) return;
    const govSel = document.getElementById('filterGovernorate'); if (govSel) govSel.value = name;
    const layer = findLayerByName(name);
    if (layer) selectRegion(name, layer);
    else {
      resetSelectionStyle();
      // fallback: try to find feature in cached geojson and fit to its bounds
      if (lastGeoJson && lastGeoJson.features && mapObj) {
        const target = normalizeName(name);
        const match = lastGeoJson.features.find(f => normalizeName((f.properties && (f.properties.name || f.properties.NAME || f.properties.gov_name || f.properties.governorate)) || '') === target);
        if (match) {
          try {
            if (tempHighlightLayer && mapObj) { try { mapObj.removeLayer(tempHighlightLayer); } catch (e) {} tempHighlightLayer = null; }
            // If the geojson is point-based, do NOT add a default Leaflet marker (it would create a 2nd pin).
            // Instead, just set the center and show our custom pin + spotlight.
            const geomType = match.geometry && match.geometry.type;
            if (geomType === 'Point' && Array.isArray(match.geometry.coordinates)) {
              const coords = match.geometry.coordinates;
              const latlng = L.latLng(coords[1], coords[0]);
              // Mark as selected so we don't fall through to the "reset view" branch below.
              selectedMapLayer = selectionPin;
              selectedCenter = latlng;
              selectedBounds = null;
              updateSpotlight(latlng, null);
              placeSelectionPin(latlng);
              try { mapObj.flyTo(latlng, 9.2, { animate: true, duration: 0.9 }); } catch (e) {}
              setTimeout(() => { if (selectedCenter) updateSpotlight(selectedCenter, selectedBounds); }, 60);
            } else {
              tempHighlightLayer = L.geoJSON(match, { style: { color: '#f59e0b', weight: 3, fillOpacity: 0.35 } }).addTo(mapObj);
              // Route through selectRegion so spotlight + pin are applied consistently
              selectRegion(name, tempHighlightLayer);
            }
          } catch (e) { /* ignore */ }
        }
      }
      if (mapObj && !selectedMapLayer && !selectedCenter) { mapObj.setView([34, 9.5], 6.5); }
    }
    showRegionInfo(name);
    applyFilters();
    try { loadDelegationLayer(name); } catch (e) { /* ignore */ }
  } catch (e) { console.warn('focusGovernorate failed', e); }
}

function selectRegion(name, layer) {
  try {
    // reset previous
    if (selectedMapLayer && selectedMapLayer !== layer) resetSelectionStyle();
    // overlay a subtle dim layer for context
    if (mapObj) {
      if (tempHighlightLayer && tempHighlightLayer !== layer && mapObj) {
        try { mapObj.removeLayer(tempHighlightLayer); } catch (e) {}
        tempHighlightLayer = null;
      }
    }
    // dim others and softly highlight selection
    if (mapLayer && mapLayer.eachLayer) {
      mapLayer.eachLayer(l => {
        try {
          if (l === layer) return;
          if (l.setStyle) l.setStyle({ fillOpacity: 0.12, opacity: 0.26, color: '#475569', weight: 1 });
        } catch (e) { /* ignore */ }
      });
    }
    if (layer && layer.setStyle) {
      // store default style if not present
      if (!layer.defaultStyle && layer.options) layer.defaultStyle = Object.assign({}, layer.options);
      try { layer.setStyle({ color: '#e2e8f0', weight: 2.2, fillColor: '#60a5fa', fillOpacity: 0.55, opacity: 0.96 }); } catch (e) {}
      if (layer.bringToFront) try { layer.bringToFront(); } catch (e) {}
    } else if (layer && layer.setRadius) {
      // marker
      try { layer.setStyle && layer.setStyle({ color: '#e2e8f0', weight: 2, fillOpacity: 0.85, opacity: 0.96, fillColor: '#60a5fa' }); layer.setRadius && layer.setRadius((layer.options && layer.options.radius || 8) * 1.35); } catch (e) {}
    }
    selectedMapLayer = layer;
    let center = null;
    let bounds = null;
    try {
      if (layer.getBounds) { bounds = layer.getBounds(); center = bounds.getCenter(); }
      else if (layer.getLatLng) { center = layer.getLatLng(); }
    } catch (e) { /* ignore */ }
    selectedCenter = center;
    selectedBounds = bounds;
    updateSpotlight(center, bounds);
    placeSelectionPin(center);
    // zoom to layer if possible (slightly closer)
    try {
      if (layer.getBounds) {
          mapObj.flyToBounds(layer.getBounds(), { padding: [28, 28], maxZoom: 9.4, animate: true, duration: 0.9 });
      } else if (layer.getLatLng) {
        mapObj.flyTo(layer.getLatLng(), 9.2, { animate: true, duration: 0.9 });
      }
    } catch (e) {}
    // reapply spotlight after any view change
    setTimeout(() => { if (selectedCenter) updateSpotlight(selectedCenter, selectedBounds); }, 60);
  } catch (e) { console.warn('selectRegion failed', e); }
}

// Soft radial spotlight that fades the rest of the map
function ensureSpotlightOverlay() {
  const mapEl = document.getElementById('map') || (mapObj && mapObj._container);
  if (!mapEl) return null;

  if (!spotlightOverlay || !spotlightOverlay.isConnected) {
    const div = document.createElement('div');
    div.id = 'mapSpotlightOverlay';
    div.style.cssText = 'position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;opacity:0;transition:opacity 200ms ease, background 140ms ease;background:transparent;z-index:450;overflow:hidden;';
    // Append directly to map element so it stays contained
    mapEl.style.position = 'relative';
    mapEl.appendChild(div);
    spotlightOverlay = div;
  }
  return spotlightOverlay;
}

function updateSpotlight(latlng, bounds) {
  if (!mapObj || !latlng) return;
  const overlay = ensureSpotlightOverlay();
  if (!overlay) return;
  const mapEl = document.getElementById('map') || (mapObj && mapObj._container);
  const rect = mapEl ? { width: mapEl.clientWidth || 1, height: mapEl.clientHeight || 1 } : { width: 1, height: 1 };
  const pt = mapObj.latLngToContainerPoint(latlng);
  const xPx = pt.x;
  const yPx = pt.y;
  let radius = Math.max(rect.width, rect.height) * 0.22;
  if (bounds) {
    try {
      const nw = mapObj.latLngToContainerPoint(bounds.getNorthWest());
      const se = mapObj.latLngToContainerPoint(bounds.getSouthEast());
      const w = Math.abs(se.x - nw.x);
      const h = Math.abs(se.y - nw.y);
      radius = Math.max(w, h) * 0.52;
    } catch (e) { /* fallback to default radius */ }
  }
  radius = Math.max(140, Math.min(radius, Math.max(rect.width, rect.height) * 0.8));
  // Keep the vignette subtle: highlight selection and gently fade surroundings.
  const isDarkMode = document.body.classList.contains('dark-mode');
  const maxDim = isDarkMode ? 0.55 : 0.45;
  const midDim = Math.max(0.12, maxDim * 0.45);
  overlay.style.background = `radial-gradient(circle at ${xPx}px ${yPx}px,
    rgba(0,0,0,0) 0px,
    rgba(0,0,0,${midDim}) ${radius * 0.70}px,
    rgba(0,0,0,${Math.min(maxDim, midDim + 0.12)}) ${radius * 1.05}px,
    rgba(0,0,0,${maxDim}) ${radius * 1.55}px)`;
  overlay.style.opacity = '1';
}

function clearSpotlight() {
  if (spotlightOverlay) spotlightOverlay.style.opacity = '0';
}

function destroySpotlight() {
  try { clearSpotlight(); } catch (e) {}
  try { if (spotlightOverlay && spotlightOverlay.remove) spotlightOverlay.remove(); } catch (e) {}
  spotlightOverlay = null;
}

function ensurePinStyles() {
  if (document.getElementById('selection-pin-style')) return;
  const style = document.createElement('style');
  style.id = 'selection-pin-style';
  style.textContent = `
    .ghost-marker { background: transparent; border: none; width: 18px; height: 18px; }
    .selection-pin-wrap { background: transparent; border: none; width: 26px; height: 40px; position: relative; }
    .selection-pin-wrap.leaflet-div-icon { background: transparent; border: none; }
    .selection-pin-icon {
      width: 26px;
      height: 40px;
      display: block;
      color: var(--color-primary-dark);
      filter: drop-shadow(0 8px 16px rgba(0,0,0,0.28));
    }
  `;
  document.head.appendChild(style);
}

function placeSelectionPin(latlng) {
  if (!mapObj || !latlng) return;
  ensurePinStyles();
  if (selectionPin) { try { mapObj.removeLayer(selectionPin); } catch (e) {} selectionPin = null; }

  const pinSvg = [
    '<svg class="selection-pin-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">',
    // Standard map-pin silhouette
    '<path fill="currentColor" d="M12 2c-3.86 0-7 3.14-7 7 0 5.25 7 13 7 13s7-7.75 7-13c0-3.86-3.14-7-7-7z"/>',
    // inner hole
    '<circle cx="12" cy="9" r="3" fill="#ffffff" opacity="0.98"/>',
    '</svg>'
  ].join('');

  selectionPin = L.marker(latlng, {
    icon: L.divIcon({
      className: 'selection-pin-wrap',
      html: pinSvg,
      iconSize: [26, 40],
      iconAnchor: [13, 38]
    }),
    zIndexOffset: 1200
  }).addTo(mapObj);
  try { selectionPin.bringToFront && selectionPin.bringToFront(); } catch (e) {}
}

function renderGeoJsonOnMap(gj, mapCounts) {
  if (!mapObj) return;
  // force choropleth mode to avoid visible proportional circles
  mapRenderMode = 'choropleth';
  // remove existing mapLayer
  if (mapLayer) { try { mapObj.removeLayer(mapLayer); } catch (e) {} mapLayer = null; }
  if (tempHighlightLayer && mapObj) { try { mapObj.removeLayer(tempHighlightLayer); } catch (e) {} tempHighlightLayer = null; }
  clearSpotlight();
  if (selectionPin && mapObj) { try { mapObj.removeLayer(selectionPin); } catch (e) {} selectionPin = null; }
  selectedCenter = null; selectedBounds = null;
  // If features are points, render circle markers; otherwise render polygons or proportional circles
  const isPoint = gj && gj.features && gj.features.length && gj.features[0].geometry && gj.features[0].geometry.type === 'Point';
  function getColor(v){
    if (!v) return '#f2f6fb';
    const vals = Object.values(mapCounts);
    const max = vals.length ? Math.max(...vals) : 0;
    const pct = v / (max || 1);
    if (pct > 0.75) return '#2b6cb0';
    if (pct > 0.5) return '#3b82f6';
    if (pct > 0.25) return '#60a5fa';
    return '#bfdbfe';
  }

  if (isPoint) {
    const ghostIcon = L.divIcon({ className: 'ghost-marker', iconSize: [18, 18], iconAnchor: [9, 9] });
    const markers = [];
    gj.features.forEach(f => {
      const name = (f.properties && (f.properties.name || f.properties.NAME || f.properties.gov_name)) || 'Unknown';
      const coords = f.geometry && f.geometry.coordinates || [];
      const latlng = [coords[1], coords[0]];
      const v = mapCounts[name] || 0;
      const m = L.marker(latlng, { icon: ghostIcon, opacity: 0, zIndexOffset: 50 });
      m.bindTooltip(`${name}<br/>Accidents: ${v}`, { sticky: true });
      m.on('click', () => {
        const govSel = document.getElementById('filterGovernorate'); if (govSel) govSel.value = name;
        selectRegion(name, m);
        showRegionInfo(name);
        applyFilters();
        try { loadDelegationLayer(name); } catch(e){ console.warn('delegation layer failed', e); }
      });
      markers.push(m);
    });
    mapLayer = L.layerGroup(markers).addTo(mapObj);
  } else {
    // polygons
    if (mapRenderMode === 'choropleth') {
      function style(feature){
        const name = feature.properties && (feature.properties.name || feature.properties.NAME || feature.properties.gov_name);
        const v = mapCounts[name] || 0;
        return { fillColor: getColor(v), weight: 1, opacity: 1, color: '#ffffff', fillOpacity: 0.85 };
      }
      function onEachFeature(feature, layer){
        const name = feature.properties && (feature.properties.name || feature.properties.NAME || feature.properties.gov_name) || 'Unknown';
        const v = mapCounts[name] || 0;
        layer.bindTooltip(`${name}<br/>Accidents: ${v}`, { sticky: true });
        layer.on('click', () => {
          const govSel = document.getElementById('filterGovernorate'); if (govSel) govSel.value = name;
          selectRegion(name, layer);
          showRegionInfo(name);
          applyFilters();
          try { loadDelegationLayer(name); } catch(e){ console.warn('delegation layer failed', e); }
        });
      }
      mapLayer = L.geoJSON(gj, { style, onEachFeature }).addTo(mapObj);
    } else {
      // proportional mode: compute centroid for each polygon and draw a proportional circle marker
      const markers = [];
      gj.features.forEach(f => {
        try {
          const props = f.properties || {};
          const name = props.name || props.NAME || props.gov_name || 'Unknown';
          // compute centroid using bbox fallback
          let latlng = null;
          if (f.geometry && f.geometry.type === 'Polygon') {
            const coords = f.geometry.coordinates[0];
            const avg = coords.reduce((acc, c) => { acc[0]+=c[1]; acc[1]+=c[0]; return acc; }, [0,0]);
            const n = coords.length || 1;
            latlng = [avg[0]/n, avg[1]/n];
          }
          const v = mapCounts[name] || 0;
          const radius = Math.max(6, Math.min(40, Math.sqrt(v || 1) * 4));
          if (latlng) {
            const m = L.circleMarker(latlng, { radius, fillColor: getColor(v), color:'#fff', weight:1, fillOpacity:0.9 });
            // attach identifying metadata for lookup
            m.feature = { properties: { name, gov_name: name, governorate: name } };
            m.options._name = name;
            m.bindTooltip(`${name}<br/>Accidents: ${v}`, { sticky: true });
            m.on('click', () => { const govSel = document.getElementById('filterGovernorate'); if (govSel) govSel.value = name; selectRegion(name, m); showRegionInfo(name); applyFilters(); try { loadDelegationLayer(name); } catch(e){} });
            markers.push(m);
          }
        } catch (e) { /* skip feature if centroid fails */ }
      });
      mapLayer = L.layerGroup(markers).addTo(mapObj);
    }
  }
  try { if (mapLayer && mapLayer.getBounds && !mapLayer.getBounds().isValid()) {} else if (mapLayer) mapObj.fitBounds(mapLayer.getBounds()); } catch(e){}
}

function showPage(n) {
  // only page through elements that explicitly opt-in via data-page
  const pageEls = Array.from(document.querySelectorAll('.charts-page[data-page]'));
  if (!pageEls.length) return; // no paged sections; leave content visible
  pageEls.forEach(p => p.classList.add('d-none'));
  const idx = Math.max(1, Math.min(n, pageEls.length));
  const el = pageEls[idx - 1] || pageEls[0];
  if (el) el.classList.remove('d-none');
  // update page indicator
  const indicator = document.getElementById('pageIndicator');
  if (indicator) {
    indicator.textContent = `${idx} / ${pageEls.length}`;
  }
}

/* Helpers: skeleton toggles and animated count-up */
function showSkeleton(base, canvasId) {
  const sk = document.getElementById(`skeleton-${base}`);
  const canvas = document.getElementById(canvasId || `${base}Chart`);
  if (sk) sk.style.display = '';
  if (canvas) canvas.style.display = 'none';
}

function hideSkeleton(base, canvasId) {
  const sk = document.getElementById(`skeleton-${base}`);
  const canvas = document.getElementById(canvasId || `${base}Chart`);
  if (sk) sk.style.display = 'none';
  if (canvas) canvas.style.display = '';
}

function showBlock(el) {
  if (el) el.style.display = 'block';
}

function showCardSkeleton(base) {
  const sk = document.getElementById(`skeleton-${base}`);
  const val = document.getElementById(base === 'total' ? 'totalAccidents' : base === 'high' ? 'highSeverity' : 'lowSeverity');
  if (sk) sk.style.display = '';
  if (val) val.style.display = 'none';
}

function makeGradient(ctx, c1, c2) {
  if (!ctx || !ctx.createLinearGradient) return c1;
  const g = ctx.createLinearGradient(0, 0, 0, 260);
  g.addColorStop(0, c1);
  g.addColorStop(1, c2 || c1);
  return g;
}

function hideCardSkeleton(base, value) {
  const sk = document.getElementById(`skeleton-${base}`);
  if (sk) sk.style.display = 'none';
  // animate number into the value element
  if (base === 'total') animateCount('totalAccidents', value);
  else if (base === 'high') animateCount('highSeverity', value);
  else if (base === 'low') animateCount('lowSeverity', value);
}

function animateCount(id, endValue, duration = 900) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = 0;
  const end = Number(endValue) || 0;
  if (isNaN(end)) { el.textContent = '—'; el.style.display = ''; return; }
  const range = end - start;
  const startTime = performance.now();

  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = Math.floor(start + range * progress);
    el.textContent = value.toLocaleString();
    el.style.display = '';
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = end.toLocaleString();
  }
  requestAnimationFrame(step);
}

// Utility to hide or show the closest card for a given skeleton id
function toggleCardForSkeleton(skelId, visible) {
  const sk = document.getElementById(skelId);
  if (!sk) return;
  // find ancestor card element
  let el = sk;
  while (el && el !== document.body) {
    if (el.classList && el.classList.contains('card')) break;
    el = el.parentElement;
  }
  if (!el || !el.classList) return;
  // animate via fade classes; and show an inline no-data message when not visible
  if (visible) {
    el.classList.remove('fade-hidden');
    el.classList.add('fade-visible');
    // remove any existing no-data message
    const existing = el.querySelector('.no-data-message'); if (existing) existing.remove();
  } else {
    el.classList.remove('fade-visible');
    el.classList.add('fade-hidden');
    // insert an inline no-data message into the card body if not present
    const body = el.querySelector('.card-body');
    if (body && !body.querySelector('.no-data-message')) {
      const msg = document.createElement('div'); msg.className = 'no-data-message'; msg.textContent = 'No data for current filters';
      body.appendChild(msg);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // sync chart theme with current mode and watch for changes
  applyChartModeTheme();
  try {
    const obs = new MutationObserver(() => applyChartModeTheme());
    obs.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  } catch (e) { /* ignore */ }

  // Initialize navigation/carousel immediately to avoid flicker
  try { initCarousel(); } catch (e) { console.warn('Carousel init failed', e); }
  try { initStatsNav(); } catch (e) { console.warn('Stats nav init failed', e); }

  // Support deep-links from the top navigation dropdown
  function applyHashToStatsPage() {
    try {
      const raw = (window.location.hash || '').replace(/^#/, '');
      if (!raw) return;
      const key = raw.toLowerCase();
      const map = {
        summary: 0,
        visuals: 1,
        charts: 1,
        map: 2,
        predictions: 3,
        'stats-summary': 0,
        'stats-charts': 1,
        'stats-map': 2,
        'stats-predictions': 3,
      };
      const idx = map[key];
      if (typeof idx === 'number') {
        showCarouselPage(idx);
        // If navigating to predictions, also load the data
        if (idx === 3 && typeof loadPredictionsData === 'function') {
          loadPredictionsData();
        }
      }
    } catch (e) {
      /* ignore */
    }
  }

  applyHashToStatsPage();
  window.addEventListener('hashchange', applyHashToStatsPage);

  setTimeout(() => {
    loadSummaryCards();
    initCharts();
    initZoomHandlers();
    initControls();
    try { initMap(); } catch (e) { console.warn('Map init failed', e); }
    // Setup map toolbar buttons
    setupMapToolbarButtons();
  }, 120);
});

// Setup map toolbar buttons
function setupMapToolbarButtons() {
  // Zoom in button
  const zoomInBtn = document.getElementById('quickActionZoomIn');
  if (zoomInBtn) {
    zoomInBtn.addEventListener('click', () => {
      if (mapObj) mapObj.zoomIn();
    });
  }
  
  // Zoom out button
  const zoomOutBtn = document.getElementById('quickActionZoomOut');
  if (zoomOutBtn) {
    zoomOutBtn.addEventListener('click', () => {
      if (mapObj) mapObj.zoomOut();
    });
  }
  
  // Reset view button
  const resetBtn = document.getElementById('resetMapView');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      resetSelection();
      if (mapObj) {
        mapObj.setView([34.0, 9.5], 6.5);
      }
      // Also reset governorate select
      const govSelect = document.getElementById('mapGovernorateSelect');
      if (govSelect) govSelect.value = '';
      // Reset region info
      showRegionInfo(null);
    });
  }
  
  // Update map stats bar
  updateMapStatsBar();
}

// Update map stats bar with overall data
async function updateMapStatsBar() {
  try {
    const res = await fetch(buildUrlWithFilters('/api/v1/stats/kpis'));
    const data = await res.json();
    
    const totalEl = document.getElementById('mapTotalAccidents');
    const highEl = document.getElementById('mapHighSeverity');
    const avgEl = document.getElementById('mapAvgDaily');
    
    if (totalEl) totalEl.textContent = (data.total || 0).toLocaleString();
    if (highEl) {
      const highRate = data.highSeverityRate != null ? Math.round(data.highSeverityRate * 10000)/100 : 0;
      highEl.textContent = `${highRate}%`;
    }
    if (avgEl) avgEl.textContent = (data.avgPerDay || 0).toFixed(1);
  } catch (e) {
    console.warn('Failed to update map stats bar', e);
  }
}

// No-op debug to avoid on-page overlay
function attachStatsDebug() { /* disabled */ }

function initCarousel() {
  const container = document.getElementById('statsCarousel');
  if (!container) return;
  carouselPages = Array.from(container.querySelectorAll('.carousel-page'));
  const pagesRow = container.querySelector('.carousel-pages');
  // keep hidden until we position the correct page; CSS controls visibility via .carousel-ready
  try { container.classList.remove('carousel-ready'); } catch (e) {}
  // Note: do not clear inline opacity/visibility here; the template hides it immediately
  // and we will reveal it only after positioning the saved page.
  // set widths handled by CSS; restore last viewed page if available
  let startIdx = 0;
  try {
    const stored = localStorage.getItem('statsActivePage');
    if (stored !== null) {
      const n = parseInt(stored, 10);
      if (!isNaN(n)) startIdx = n;
    }
  } catch (e) { /* ignore */ }
  showCarouselPage(startIdx);
  // reveal after the correct page is positioned to avoid initial flicker
  requestAnimationFrame(() => {
    try {
      if (pagesRow) {
        pagesRow.style.opacity = '';
        pagesRow.style.visibility = '';
      }
      container.classList.add('carousel-ready');
      document.body.classList.add('stats-carousel-ready');
      // Reveal the nav only after the correct page is active
      const nav = document.querySelector('.stats-nav');
      if (nav) {
        nav.style.opacity = '';
        nav.style.visibility = '';
      }
    } catch (e) {}
  });
  // touch handlers for swipe
  let startX = null;
  container.addEventListener('touchstart', (ev) => { startX = ev.touches && ev.touches[0] && ev.touches[0].clientX; });
  container.addEventListener('touchend', (ev) => {
    if (startX == null) return; const endX = ev.changedTouches && ev.changedTouches[0] && ev.changedTouches[0].clientX; if (!endX) return; const dx = endX - startX; if (Math.abs(dx) > 40) { if (dx < 0) showCarouselPage(carouselIndex + 1); else showCarouselPage(carouselIndex - 1); } startX = null;
  });

  // keyboard navigation: left/right arrows, Home/End
  container.addEventListener('keydown', (ev) => {
    if (ev.key === 'ArrowLeft') { ev.preventDefault(); showCarouselPage(carouselIndex - 1); }
    else if (ev.key === 'ArrowRight') { ev.preventDefault(); showCarouselPage(carouselIndex + 1); }
    else if (ev.key === 'Home') { ev.preventDefault(); showCarouselPage(0); }
    else if (ev.key === 'End') { ev.preventDefault(); showCarouselPage(carouselPages.length - 1); }
  });
  // allow global keyboard nav as well
  document.addEventListener('keydown', (ev) => {
    if (ev.target && (ev.target.tagName === 'INPUT' || ev.target.tagName === 'SELECT' || ev.target.isContentEditable)) return; // ignore typing
    if (ev.key === 'ArrowLeft') { showCarouselPage(carouselIndex - 1); }
    else if (ev.key === 'ArrowRight') { showCarouselPage(carouselIndex + 1); }
    else if (ev.key === 'Home') { showCarouselPage(0); }
    else if (ev.key === 'End') { showCarouselPage(carouselPages.length - 1); }
  });
}

// wire the in-page nav buttons (Summary / Visuals / Map / Predictions)
function initStatsNav() {
  ['navSummary','navCharts','navMap','navPredictions'].forEach((id, idx) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('click', (ev) => { 
      ev.preventDefault(); 
      showCarouselPage(idx);
      // If predictions, also load data
      if (idx === 3 && typeof loadPredictionsData === 'function') {
        loadPredictionsData();
      }
    });
    el.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); showCarouselPage(idx); } });
  });
}

function showCarouselPage(idx) {
  const container = document.getElementById('statsCarousel');
  if (!container) return;
  const pages = Array.from(container.querySelectorAll('.carousel-page'));
  if (!pages.length) return;
  if (idx < 0) idx = 0; if (idx >= pages.length) idx = pages.length - 1;
  carouselIndex = idx;
  
  // Show/hide pages
  pages.forEach((page, i) => {
    if (i === idx) {
      page.classList.add('active');
    } else {
      page.classList.remove('active');
    }
  });
  
  // allow template/CSS to switch to an immersive layout on the map page
  try {
    document.body.classList.toggle('stats-active-map', idx === 2);
  } catch (e) { /* ignore */ }

  // Map page: fit to viewport and avoid body scrolling (right panel scrolls instead)
  try {
    if (idx === 2) {
      // Don't lock body scroll - allow page to scroll if content overflows
      // Just add a class for styling purposes
      document.body.classList.add('stats-active-map');
    } else {
      container.style.height = '';
      document.documentElement.style.overflowY = '';
      document.body.style.overflowY = '';
      document.body.classList.remove('stats-active-map');
      destroySpotlight();
    }
  } catch (e) { /* ignore */ }

  try { localStorage.setItem('statsActivePage', String(idx)); } catch (e) { /* ignore */ }
  
  // update in-page nav buttons if present
  try {
    const map = {0: 'navSummary', 1: 'navCharts', 2: 'navMap', 3: 'navPredictions'};
    Object.values(map).forEach(id => { 
      const b = document.getElementById(id); 
      if (b) { 
        b.classList.remove('active'); 
        b.setAttribute('aria-selected','false'); 
      } 
    });
    const activeId = map[idx];
    const activeBtn = document.getElementById(activeId);
    if (activeBtn) { 
      activeBtn.classList.add('active'); 
      activeBtn.setAttribute('aria-selected','true'); 
    }
  } catch (e) { /* non-fatal */ }

  // if navigating to Visuals page, ensure charts resize and heatmap grid is rendered
  try {
    if (idx === 1) {
      // force Chart.js to recalc sizes
      [timeChart, severityChart, causeChart, delegationChart, statusChart, confirmedReportedChart].forEach(c => { if (c && typeof c.resize === 'function') try { c.resize(); } catch(e) {} });
      // (re)render heatmap grid to ensure it's visible
      try { renderHeatmap(); } catch (e) {}
    }
    if (idx === 2) {
      // map page: invalidate leaflet map size so it renders correctly
      if (mapObj && typeof mapObj.invalidateSize === 'function') { setTimeout(() => { try { mapObj.invalidateSize(); } catch(e){} }, 120); }
    }
  } catch (e) { /* ignore */ }
}

function initCharts() {
  renderSeverity();
  renderCause();
  renderTime();
  renderDelegation();
  renderStatus();
  renderSeverityByRegion('governorate');
  renderSeverityByRegion('delegation');
  renderCauseBySeverity();
  renderHeatmap();
  // render confirmed/reported on init
  renderConfirmedReported();
  // init map
  try { initMap(); } catch(e) { console.warn('Map init failed', e); }
}

let mapLayer = null;
let mapObj = null;
let delegationLayer = null;
let googleMap = null;
let googleActive = false;
let lastMapCounts = {};
let embedActive = false;
let lastGeoJson = null;
let mapRenderMode = 'choropleth'; // other option: 'proportional'
const ALL_GOVERNORATES = [
  'Ariana','Beja','Ben Arous','Bizerte','Gabes','Gafsa','Jendouba','Kairouan','Kasserine','Kebili','Kef','Mahdia','Manouba','Medenine','Monastir','Nabeul','Sfax','Sidi Bouzid','Siliana','Sousse','Tataouine','Tozeur','Tunis','Zaghouan'
];

// Full inline fallback (points) so every governorate remains clickable even if polygon files are missing
function buildGovernoratePointGeoJson() {
  const coords = {
    'Ariana': [10.1647, 36.8665],
    'Beja': [9.1833, 36.7333],
    'Ben Arous': [10.2183, 36.7531],
    'Bizerte': [9.8739, 37.2746],
    'Gabes': [10.0982, 33.8815],
    'Gafsa': [8.7842, 34.425],
    'Jendouba': [8.78, 36.5019],
    'Kairouan': [10.0963, 35.6781],
    'Kasserine': [8.8365, 35.1676],
    'Kebili': [8.969, 33.7044],
    'Kef': [8.714, 36.1829],
    'Mahdia': [11.0622, 35.5047],
    'Manouba': [10.0868, 36.8086],
    'Medenine': [10.5055, 33.3549],
    'Monastir': [10.8262, 35.7779],
    'Nabeul': [10.7376, 36.4513],
    'Sfax': [10.7603, 34.7406],
    'Sidi Bouzid': [9.4849, 35.0382],
    'Siliana': [9.3667, 36.0833],
    'Sousse': [10.63699, 35.8256],
    'Tataouine': [10.4518, 32.9297],
    'Tozeur': [8.1336, 33.92],
    'Tunis': [10.1815, 36.8065],
    'Zaghouan': [10.1429, 36.4029]
  };
  return {
    type: 'FeatureCollection',
    features: ALL_GOVERNORATES.map(name => ({
      type: 'Feature',
      properties: { name },
      geometry: { type: 'Point', coordinates: coords[name] || [9, 34.5] }
    }))
  };
}

// noop info updater to prevent ReferenceErrors when absent in DOM
function updateInfo() { /* noop */ }

async function initMap() {
  if (typeof L === 'undefined') return console.warn('Leaflet not loaded');
  // If initMap runs more than once (re-init / switching basemaps), fully clean up
  // the previous map instance to avoid duplicated panes/markers (e.g., double pins).
  try {
    if (mapObj) {
      try { mapObj.off(); } catch (e) {}
      try { mapObj.remove(); } catch (e) {}
      mapObj = null;
    }
    const mapEl = document.getElementById('map');
    if (mapEl) {
      try { mapEl.innerHTML = ''; } catch (e) {}
      try { delete mapEl._leaflet_id; } catch (e) { try { mapEl._leaflet_id = null; } catch (ee) {} }
    }
    try { if (spotlightOverlay && spotlightOverlay.remove) spotlightOverlay.remove(); } catch (e) {}
    spotlightOverlay = null;
    spotlightPane = null;
    if (selectionPin) { try { selectionPin.remove && selectionPin.remove(); } catch (e) {} selectionPin = null; }
    selectedCenter = null;
    selectedBounds = null;
    selectedMapLayer = null;
    tempHighlightLayer = null;
    mapLayer = null;
    delegationLayer = null;
  } catch (e) { /* ignore */ }
  // create map
  mapObj = L.map('map', { center: [34.0, 9.5], zoom: 6.5, minZoom: 5, maxZoom: 10, zoomSnap: 0.1, zoomDelta: 0.5 });
  
  // Store map globally for heatmap timeline
  window.statsMap = mapObj;
  
  // Use a clean, Google-like light basemap (CartoDB Positron) that requires no API key.
  // If you prefer the actual Google Maps basemap, provide a Google Maps JS API key and
  // we can switch to the Google Maps SDK or a paid tile provider.
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a> &mdash; OpenStreetMap contributors',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(mapObj);

  // spotlight pane above overlay pane but below markers
  try {
    spotlightPane = mapObj.createPane('spotlightPane');
    if (spotlightPane) {
      spotlightPane.style.zIndex = '750'; // above markers/tooltips, below popups
      spotlightPane.style.pointerEvents = 'none';
    }
  } catch (e) { /* optional */ }

  // keep spotlight centered on map movements
  mapObj.on('move zoom', () => {
    if (selectedCenter) updateSpotlight(selectedCenter, selectedBounds);
  });
  mapObj.on('zoomend moveend', () => {
    if (selectedCenter) updateSpotlight(selectedCenter, selectedBounds);
  });

  // load GeoJSON
  let gj = null;
  try {
    const gjRes = await fetch('/static/geo/tunisia_governorates.geojson');
    gj = await gjRes.json();
  } catch(e) { console.warn('Failed to load governorate geojson', e); }

  // If the polygon file is empty or missing, fall back to a small sample points file
  let usedFallback = null; // 'polygon' or 'points' when fallback used
  if (!gj || !gj.features || gj.features.length === 0) {
    // try a fallback polygon approximation first (higher-fidelity than points)
    try {
      const fbRes = await fetch('/static/geo/tunisia_governorates_fallback.geojson');
      if (fbRes && fbRes.ok) {
        const fb = await fbRes.json();
        if (fb && fb.features && fb.features.length) {
          gj = fb;
          usedFallback = 'polygon';
          console.info('Using fallback governorate polygons');
        }
      }
    } catch (e) { console.warn('No fallback polygon geojson available', e); }

    // if still no geojson, fall back to sample points
    if (!gj || !gj.features || gj.features.length === 0) {
      try {
        const sampleRes = await fetch('/static/geo/tunisia_governorates_sample.geojson');
        const sample = await sampleRes.json();
        if (sample && sample.features && sample.features.length) {
          gj = sample;
          usedFallback = 'points';
          console.info('Using sample governorate geojson (points) as fallback');
        }
      } catch (e) {
        console.warn('No sample geojson available', e);
      }
    }
  }

  // If we still do not have full coverage (less than 20 regions), use the complete point fallback
  if (!gj || !gj.features || gj.features.length < 20) {
    gj = buildGovernoratePointGeoJson();
    usedFallback = usedFallback || 'points-full';
    console.info('Using inline point fallback for all governorates');
  }

  // get counts
  const countsRes = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_governorate'));
  const counts = await countsRes.json();
  const mapCounts = {};
  // prefer server-provided items[] (key,label,count) when available
  if (counts.items && counts.items.length) {
    counts.items.forEach(it => { mapCounts[it.label || it.key] = it.count; });
  } else if (counts.labels && counts.values) {
    counts.labels.forEach((lab, i) => { mapCounts[lab] = counts.values[i]; });
  }
  // store globally for potential Google map use
  lastMapCounts = mapCounts;

  // populate governorate dropdown for direct selection (use geojson to ensure full list)
  populateMapGovernorateSelect(mapCounts, gj);

  // compute color scale
  const vals = Object.values(mapCounts);
  const max = vals.length ? Math.max(...vals) : 0;
  function getColor(v){
    if (!v) return '#f2f6fb';
    const pct = v / (max || 1);
    if (pct > 0.75) return '#2b6cb0';
    if (pct > 0.5) return '#3b82f6';
    if (pct > 0.25) return '#60a5fa';
    return '#bfdbfe';
  }

  lastGeoJson = gj;
  // render depending on geometry type and current render mode
  renderGeoJsonOnMap(gj, mapCounts);
  // fit bounds if features exist
  try {
    if (mapLayer && mapLayer.getBounds && mapLayer.getBounds().isValid()) {
      mapObj.fitBounds(mapLayer.getBounds(), { padding: [30, 30], maxZoom: 7.2 });
    }
  } catch(e){}
  // add legend
  addMapLegend(mapObj, mapCounts, usedFallback);
  addMapControls(mapObj);

  // show fallback notice if used
  try {
    const notice = document.getElementById('mapFallbackNotice');
    if (notice) {
      if (usedFallback) {
        notice.classList.remove('d-none');
        notice.innerHTML = `<strong>Notice:</strong> Using ${usedFallback === 'polygon' ? 'approximate polygon' : 'sample point'} boundaries. Replace with authoritative GeoJSON for accurate maps. <button id=\"dismissMapNotice\" class=\"btn btn-sm btn-outline-secondary ms-2\">Dismiss</button>`;
        const btn = document.getElementById('dismissMapNotice');
        if (btn) btn.addEventListener('click', () => { notice.classList.add('d-none'); });
      } else {
        notice.classList.add('d-none');
      }
    }
  } catch (e) { console.warn('Failed to set fallback notice', e); }

  // Initialize Map Timeline after map is ready
  setTimeout(() => {
    try {
      if (window.MapTimeline && window.statsMap && !window._mapTimelineInstance) {
        window._mapTimelineInstance = new MapTimeline({
          map: window.statsMap,
          containerId: 'mapTimeline'
        });
      }
    } catch (e) { console.warn('Failed to initialize map timeline', e); }
  }, 300);
}

// ------------------
// Google Maps integration (dynamic)
// ------------------

function loadGoogleScript(key) {
  return new Promise((resolve, reject) => {
    if (window.google && window.google.maps) return resolve();
    const s = document.createElement('script');
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}`;
    s.async = true; s.defer = true;
    s.onload = () => resolve();
    s.onerror = (e) => reject(e);
    document.head.appendChild(s);
  });
}

async function getGovernorateGeoJson() {
  // try primary polygon, then fallback polygon, then sample points
  const tryUrls = ['/static/geo/tunisia_governorates.geojson', '/static/geo/tunisia_governorates_fallback.geojson', '/static/geo/tunisia_governorates_sample.geojson'];
  for (const u of tryUrls) {
    try {
      const r = await fetch(u);
      if (!r.ok) continue;
      const j = await r.json();
      if (j && j.features && j.features.length) return j;
    } catch (e) { continue; }
  }
  return null;
}

async function switchToGoogleMap(apiKey) {
  try {
    // load script
    await loadGoogleScript(apiKey);
  } catch (e) {
    alert('Failed to load Google Maps script. Check API key and network.');
    return;
  }

  // destroy Leaflet map to reuse container
  try { if (mapObj) { mapObj.remove(); mapObj = null; } } catch (e) { }

  // create google map
  const el = document.getElementById('map');
  el.innerHTML = '';
  googleMap = new google.maps.Map(el, { center: { lat: 34.0, lng: 9.0 }, zoom: 6, mapTypeId: 'roadmap' });
  googleActive = true;
  document.getElementById('useGoogleBasemap')?.classList.add('d-none');
  document.getElementById('useLeafletBasemap')?.classList.remove('d-none');

  // load GeoJSON and render
  const gj = await getGovernorateGeoJson();
  if (!gj) return;

  googleMap.data.forEach(f => googleMap.data.remove(f));
  googleMap.data.addGeoJson(gj);

  // style features using lastMapCounts
  googleMap.data.setStyle(function(feature) {
    const name = feature.getProperty('name') || feature.getProperty('NAME') || feature.getProperty('gov_name') || 'Unknown';
    const v = lastMapCounts[name] || 0;
    const color = (function(){ const max = Math.max(...Object.values(lastMapCounts)||[1]); const pct = v/(max||1); if (pct>0.75) return '#2b6cb0'; if (pct>0.5) return '#3b82f6'; if (pct>0.25) return '#60a5fa'; return '#bfdbfe'; })();
    return { fillColor: color, strokeWeight: 1, strokeColor: '#ffffff', fillOpacity: 0.85 };
  });

  // click handler
  googleMap.data.addListener('click', function(e) {
    const props = e.feature.getProperty('name') || e.feature.getProperty('NAME') || e.feature.getProperty('gov_name');
    const name = props || 'Unknown';
    const govSel = document.getElementById('filterGovernorate'); if (govSel) govSel.value = name;
    showRegionInfo(name);
    applyFilters();
  });

  // fit bounds to data
  try {
    const bounds = new google.maps.LatLngBounds();
    googleMap.data.forEach(function(feature){
      const geom = feature.getGeometry();
      geom.forEachLatLng && geom.forEachLatLng(function(latlng){ bounds.extend(latlng); });
    });
    googleMap.fitBounds(bounds);
  } catch (e) { }
}

function switchToLeafletMap() {
  // remove google map
  if (googleMap) {
    try { googleMap.data && googleMap.data.forEach(f=>googleMap.data.remove(f)); } catch(e){}
    googleMap = null; googleActive = false;
  }
  document.getElementById('useGoogleBasemap')?.classList.remove('d-none');
  document.getElementById('useLeafletBasemap')?.classList.add('d-none');
  // reinitialize leaflet map
  try { initMap(); } catch (e) { console.warn('Failed to re-init leaflet map', e); }
}

function switchFromEmbedToLeaflet() {
  // remove iframe if present and re-init leaflet
  try {
    const el = document.getElementById('map');
    if (el) el.innerHTML = '';
  } catch (e) {}
  embedActive = false;
  document.getElementById('useGoogleBasemap')?.classList.remove('d-none');
  document.getElementById('embedGoogleMap')?.classList.remove('d-none');
  document.getElementById('useLeafletBasemap')?.classList.add('d-none');
  try { initMap(); } catch (e) { console.warn('Failed to init leaflet map after embed', e); }
}

function switchToGoogleEmbed() {
  // Replace map container with a Google Maps embed iframe centered on Tunisia
  try {
    // remove leaflet or google map
    try { if (mapObj) { mapObj.remove(); mapObj = null; } } catch(e){}
    if (googleMap) { googleMap = null; }

    const el = document.getElementById('map');
    el.innerHTML = '';
    const iframe = document.createElement('iframe');
    iframe.width = '100%';
    iframe.height = '520';
    iframe.frameBorder = '0';
    iframe.style.border = '0';
    // Use a simple embed URL centered on Tunisia; interactive and requires no API key
    iframe.src = 'https://www.google.com/maps?q=Tunisia&z=6&output=embed';
    el.appendChild(iframe);
    embedActive = true;
    document.getElementById('useGoogleBasemap')?.classList.add('d-none');
    document.getElementById('embedGoogleMap')?.classList.add('d-none');
    document.getElementById('useLeafletBasemap')?.classList.remove('d-none');
  } catch (e) {
    console.warn('Failed to create embed iframe', e);
    alert('Failed to embed Google Map.');
  }
}

function addMapControls(map) {
  if (!map) { console.warn('addMapControls: map is not initialized'); return; }
  // remove existing control
  if (map._backControl) { map.removeControl(map._backControl); map._backControl = null; }
  const BackControl = L.Control.extend({
    options: { position: 'topleft' },
    onAdd: function () {
      const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
      const btn = L.DomUtil.create('a', '', container);
      btn.href = '#'; btn.id = 'backToGovs'; btn.title = 'Back to governorates'; btn.innerHTML = '&#x2190; Back';
      L.DomEvent.on(btn, 'click', L.DomEvent.stop).on(btn, 'click', (ev) => {
        L.DomEvent.preventDefault(ev);
        // remove delegation layer if present
        if (delegationLayer) { try { map.removeLayer(delegationLayer); delegationLayer = null; } catch(e){} }
        // show governorate layer bounds
        if (mapLayer && mapLayer.getBounds) { try { map.fitBounds(mapLayer.getBounds()); } catch(e){} }
        // clear delegation filter
        const delSel = document.getElementById('filterDelegation'); if (delSel) delSel.value = '';
        applyFilters();
      });
      return container;
    }
  });
  const ctrl = new BackControl(); ctrl.addTo(map); map._backControl = ctrl;
  // Mode control disabled to avoid proportional circles overlay
}

async function loadDelegationLayer(governorateName) {
  if (!mapObj) return;
  // ensure delegations geojson exists
  try {
    const gjRes = await fetch('/static/geo/tunisia_delegations.geojson');
    if (!gjRes.ok) throw new Error('delegation geojson not found');
    const gj = await gjRes.json();
    // get delegation counts
  const countsRes = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_delegation'));
  const counts = await countsRes.json();
  const mapCounts = {};
  if (counts.items && counts.items.length) counts.items.forEach(it => mapCounts[it.label || it.key] = it.count);
  else if (counts.labels && counts.values) counts.labels.forEach((lab,i)=>mapCounts[lab]=counts.values[i]);

    // filter features to this governorate (attempt several property names)
    const features = gj.features.filter(f => {
      const p = f.properties || {};
      const gov = p.governorate || p.gov_name || p.Governorate || p.admin || p.GOV_NAME || p.province;
      if (!gov) return false;
      return String(gov).toLowerCase().trim() === String(governorateName).toLowerCase().trim();
    });
    if (!features || !features.length) {
      console.warn('No delegation features found for', governorateName);
      return;
    }
    const subset = { type: 'FeatureCollection', features: features };

    // remove existing delegation layer
    if (delegationLayer) { try { mapObj.removeLayer(delegationLayer); } catch(e){} delegationLayer = null; }

    function getColorForDel(name){ const v = mapCounts[name]||0; const max = Math.max(...Object.values(mapCounts)||[1]); const pct = v/(max||1); if (pct>0.75) return '#7f1d1d'; if (pct>0.5) return '#ef4444'; if (pct>0.25) return '#fca5a5'; return '#fee2e2'; }
      // create either polygon layer or marker cluster / layerGroup depending on features
      function getColorForDel(name){ const v = mapCounts[name]||0; const max = Math.max(...Object.values(mapCounts)||[1]); const pct = v/(max||1); if (pct>0.75) return '#7f1d1d'; if (pct>0.5) return '#ef4444'; if (pct>0.25) return '#fca5a5'; return '#fee2e2'; }

      // If features are points, render clustered markers when possible
      if (subset.features[0] && subset.features[0].geometry && subset.features[0].geometry.type === 'Point') {
        const markers = [];
        subset.features.forEach(f => {
          const p = f.properties || {};
          const name = p.name || p.NAME || p.delegation || p.deleg || 'Unknown';
          const coords = f.geometry.coordinates || [];
          const lat = coords[1], lon = coords[0];
          const v = mapCounts[name] || 0;
          const m = L.circleMarker([lat, lon], { radius: Math.max(4, Math.min(16, Math.sqrt(v||1)*3)), fillColor: getColorForDel(name), color:'#fff', weight:1, fillOpacity:0.9 });
          m.bindTooltip(`${name}<br/>Accidents: ${v}`, { sticky:true });
          m.on('click', () => { const delSel = document.getElementById('filterDelegation'); if (delSel) delSel.value = name; applyFilters(); });
          markers.push(m);
        });
        // use marker cluster plugin when available
        if (window.L && window.L.markerClusterGroup) {
          const mcg = window.L.markerClusterGroup(); markers.forEach(m => mcg.addLayer(m)); delegationLayer = mcg; delegationLayer.addTo(mapObj);
        } else {
          delegationLayer = L.layerGroup(markers).addTo(mapObj);
        }
        try { mapObj.fitBounds(delegationLayer.getBounds(), { padding: [18, 18], maxZoom: 7 }); } catch(e){}
      } else {
        function style(feature){ const n = feature.properties && (feature.properties.name || feature.properties.NAME || feature.properties.delegation || feature.properties.deleg) ; return { fillColor: getColorForDel(n), weight: 1, opacity: 1, color: '#ffffff', fillOpacity: 0.85 }; }
        function onEach(feature, layer){ const n = feature.properties && (feature.properties.name || feature.properties.NAME || feature.properties.delegation || feature.properties.deleg) || 'Unknown'; const v = mapCounts[n]||0; layer.bindTooltip(`${n}<br/>Accidents: ${v}`, { sticky:true }); layer.on('click', () => { const delSel = document.getElementById('filterDelegation'); if (delSel) delSel.value = n; applyFilters(); }); }
        delegationLayer = L.geoJSON(subset, { style, onEachFeature: onEach }).addTo(mapObj);
        try { mapObj.fitBounds(delegationLayer.getBounds(), { padding: [18, 18], maxZoom: 7 }); } catch(e){}
      }
  } catch (e) {
    console.warn('Failed to load delegation layer', e);
  }
}

function addMapLegend(map, counts, usedFallback) {
  // Legend disabled - not needed
  if (map && map._legendControl) { map.removeControl(map._legendControl); map._legendControl = null; }
  return;
}

function populateMapGovernorateSelect(mapCounts, geo) {
  try {
    const sel = document.getElementById('mapGovernorateSelect');
    if (!sel) return;
    const current = sel.value;
    const names = new Set();
    // include all geojson names first (ensures 24 governorates)
    if (geo && geo.features) {
      geo.features.forEach(f => {
        const props = f.properties || {};
        const n = props.name || props.NAME || props.gov_name || props.governorate;
        if (n) names.add(n);
      });
    }
    // include any names from counts
    Object.keys(mapCounts || {}).forEach(n => names.add(n));
    // ensure full canonical list is present
    ALL_GOVERNORATES.forEach(n => names.add(n));

    sel.innerHTML = '<option value="">Select governorate</option>';
    Array.from(names).sort().forEach(name => {
      const opt = document.createElement('option');
      opt.value = name; opt.textContent = name;
      sel.appendChild(opt);
    });
    // preselect current filter if present
    const govFilter = document.getElementById('filterGovernorate');
    if (govFilter && govFilter.value && mapCounts[govFilter.value]) {
      sel.value = govFilter.value;
    } else if (current && mapCounts[current]) {
      sel.value = current;
    }
    sel.onchange = () => {
      const name = sel.value;
      if (!name) { resetSelectionStyle(); return; }
      focusGovernorate(name);
    };
  } catch (e) { console.warn('populateMapGovernorateSelect failed', e); }
}

async function showRegionInfo(name) {
  // Dashboard-style layout elements
  const regionEmptyState = document.getElementById('regionEmptyState');
  const regionData = document.getElementById('regionData');
  const nameEl = document.getElementById('regionName');
  const totalEl = document.getElementById('regionTotal');
  const highPctEl = document.getElementById('regionHighPct');
  const topCauseEl = document.getElementById('regionTopCause');
  const sparkHost = document.getElementById('regionMiniChart');
  const regionFlag = document.getElementById('regionFlag');

  // Clear to placeholder state when no selection
  if (!name) {
    if (regionEmptyState) regionEmptyState.style.display = '';
    if (regionData) regionData.style.display = 'none';
    if (sparkHost) sparkHost.innerHTML = '<canvas id="regionMiniCanvas" style="width:100%; height:120px;"></canvas>';
    if (nameEl) nameEl.textContent = '—';
    if (totalEl) totalEl.textContent = '—';
    if (highPctEl) highPctEl.textContent = '—';
    if (topCauseEl) topCauseEl.textContent = '—';
    if (regionFlag) regionFlag.textContent = 'T';
    return;
  }

  // Show data, hide empty state
  if (regionEmptyState) regionEmptyState.style.display = 'none';
  if (regionData) regionData.style.display = '';
  if (nameEl) nameEl.textContent = name;
  if (regionFlag) regionFlag.textContent = name.charAt(0).toUpperCase();
  
  try {
    const res = await fetch(buildUrlWithFilters('/api/v1/stats/kpis', { governorate: name }));
    const data = await res.json();
    if (totalEl) totalEl.textContent = (data.total || 0).toLocaleString();
    if (highPctEl) highPctEl.textContent = `${Math.round((data.highSeverityRate||0)*10000)/100}%`;
    if (topCauseEl) topCauseEl.textContent = data.topCause?.label ? data.topCause.label : (data.topCause?.cause ? prettifyLabel(data.topCause.cause) : '—');

    // small sparkline using Chart.js if available
    try {
      if (sparkHost) sparkHost.innerHTML = '<canvas id="regionMiniCanvas" style="width:100%; height:100px;"></canvas>';
      const ctx = document.getElementById('regionMiniCanvas');
      if (ctx) {
        const existing = Chart.getChart(ctx);
        if (existing) existing.destroy();
        const tRes = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_month', { granularity: 'month', governorate: name }));
        const tData = await tRes.json();
        new Chart(ctx, {
          type: 'line',
          data: { labels: tData.labels || [], datasets: [{ data: tData.values || [], borderColor: ChartTheme.palette.primaryA, backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.35 }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: true } }, elements: { point: { radius: 2 } }, scales: { x: { display: false }, y: { display: false } } }
        });
      }
    } catch (e) { console.warn('mini chart failed', e); }
  } catch (e) {
    console.warn('region KPIs failed', e);
  }
}

async function loadSummaryCards() {
  // show skeletons for the nine KPI cards on the summary page
  const kpiSkeletons = ['total','ytd','mtd','highrate','topcause','topgov','topdel','avg','yoy'];
  kpiSkeletons.forEach(s => {
    const sk = document.getElementById(`skeleton-${s}`);
    if (sk) sk.style.display = '';
  });
  // hide value elements until filled
  ['totalAccidents','accidentsYTD','accidentsMTD','highSeverityRate','topCause','topGovernorate','topDelegation','avgPerDay','yoyChangePct'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });

  try {
    const res = await fetch(buildUrlWithFilters('/api/v1/stats/kpis'));
    const data = await res.json();
    // total
    animateCount('totalAccidents', data.total || 0);
    const skTotal = document.getElementById('skeleton-total'); if (skTotal) skTotal.style.display = 'none';

    // YTD / MTD
    animateCount('accidentsYTD', data.yearToDate || 0);
    const skY = document.getElementById('skeleton-ytd'); if (skY) skY.style.display = 'none';
    animateCount('accidentsMTD', data.monthToDate || 0);
    const skM = document.getElementById('skeleton-mtd'); if (skM) skM.style.display = 'none';

    // high severity rate (percent)
    const rate = data.highSeverityRate != null ? Math.round(data.highSeverityRate * 10000)/100 : 0;
    const elHighRate = document.getElementById('highSeverityRate'); if (elHighRate) { elHighRate.textContent = `${rate}%`; elHighRate.style.display = ''; }
    const skHR = document.getElementById('skeleton-highrate'); if (skHR) skHR.style.display = 'none';

    // top cause (text)
    const tc = data.topCause || {};
    const elTopCause = document.getElementById('topCause'); if (elTopCause) {
      // prefer server label if present
      const name = tc.label ? tc.label : (tc.cause ? prettifyLabel(tc.cause) : '—');
      const c = tc.count || 0;
      const pct = tc.pct ? Math.round(tc.pct * 10000)/100 : 0;
      elTopCause.textContent = `${name} (${c.toLocaleString()} — ${pct}%)`;
      elTopCause.style.display = '';
    }
    const skTC = document.getElementById('skeleton-topcause'); if (skTC) skTC.style.display = 'none';

  // top governorate
  const tg = data.topGovernorate || {};
  const elTG = document.getElementById('topGovernorate'); if (elTG) { const tgName = tg.label || tg.name || '—'; elTG.textContent = `${tgName} (${tg.count || 0})`; elTG.style.display = ''; }
  const skTG = document.getElementById('skeleton-topgov'); if (skTG) skTG.style.display = 'none';

  // top delegation
  const td = data.topDelegation || {};
  const elTD = document.getElementById('topDelegation'); if (elTD) { const tdName = td.label || td.name || '—'; elTD.textContent = `${tdName} (${td.count || 0})`; elTD.style.display = ''; }
  const skTD = document.getElementById('skeleton-topdel'); if (skTD) skTD.style.display = 'none';

  // avg per day
  const elAvg = document.getElementById('avgPerDay'); if (elAvg) { elAvg.textContent = (data.avgPerDay || 0).toLocaleString(); elAvg.style.display = ''; }
  const skAvg = document.getElementById('skeleton-avg'); if (skAvg) skAvg.style.display = 'none';

  // yoy
  const elY = document.getElementById('yoyChangePct'); if (elY) { elY.textContent = `${data.yoyChangePct != null ? data.yoyChangePct : 0}%`; elY.style.display = ''; }
  const skYoy = document.getElementById('skeleton-yoy'); if (skYoy) skYoy.style.display = 'none';
  } catch (err) {
    console.error('Failed to load KPIs', err);
    // hide all skeletons and show placeholders
    ['total','ytd','mtd','highrate','topcause','topgov'].forEach(s => { const sk = document.getElementById(`skeleton-${s}`); if (sk) sk.style.display='none'; });
    ['totalAccidents','accidentsYTD','accidentsMTD','highSeverityRate','topCause','topGovernorate'].forEach(id => { const el = document.getElementById(id); if (el) { el.textContent = '—'; el.style.display = ''; } });
  }
}

function initControls() {
  // granularity buttons
  document.getElementById('gran-day').addEventListener('click', () => setGranularity('day'));
  document.getElementById('gran-month').addEventListener('click', () => setGranularity('month'));
  document.getElementById('gran-year').addEventListener('click', () => setGranularity('year'));
  // toggles
  const tArea = document.getElementById('toggleArea');
  const tStack = document.getElementById('toggleStack');
  if (tArea) tArea.addEventListener('change', () => { setGranularity(document.querySelector('#gran-day.active, #gran-month.active, #gran-year.active')?.id?.split('-')[1] || 'month'); });
  if (tStack) tStack.addEventListener('change', () => { setGranularity(document.querySelector('#gran-day.active, #gran-month.active, #gran-year.active')?.id?.split('-')[1] || 'month'); });
  // paging
  pages = Array.from(document.querySelectorAll('.charts-page[data-page]'));
  // init indicator and show first page (if any)
  if (pages.length) {
    currentPage = Math.min(currentPage || 1, pages.length);
    showPage(currentPage);
  } else {
    const indicator = document.getElementById('pageIndicator');
    if (indicator) indicator.textContent = '—';
  }
  const prevBtn = document.getElementById('prevPage');
  const nextBtn = document.getElementById('nextPage');
  if (prevBtn) prevBtn.addEventListener('click', () => {
    if (!pages.length) return;
    currentPage = currentPage <= 1 ? pages.length : currentPage - 1;
    showPage(currentPage);
  });
  if (nextBtn) nextBtn.addEventListener('click', () => {
    if (!pages.length) return;
    currentPage = currentPage >= pages.length ? 1 : currentPage + 1;
    showPage(currentPage);
  });

  // Filters: populate options and wire apply/reset
  populateFilterOptions();
  const applyBtn = document.getElementById('applyFilters');
  const resetBtn = document.getElementById('resetFilters');
  if (applyBtn) applyBtn.addEventListener('click', applyFilters);
  if (resetBtn) resetBtn.addEventListener('click', resetFilters);

  // Google basemap controls
  const gBtn = document.getElementById('useGoogleBasemap');
  const lBtn = document.getElementById('useLeafletBasemap');
  if (gBtn) gBtn.addEventListener('click', async () => {
    const saved = sessionStorage.getItem('googleMapsApiKey');
    let key = saved || window.prompt('Paste your Google Maps JavaScript API key (stored in this browser session only):');
    if (!key) return;
    sessionStorage.setItem('googleMapsApiKey', key);
    await switchToGoogleMap(key);
  });
  if (lBtn) lBtn.addEventListener('click', () => { switchToLeafletMap(); });
  const embedBtn = document.getElementById('embedGoogleMap');
  if (embedBtn) embedBtn.addEventListener('click', () => { switchToGoogleEmbed(); });
}

function getFilterParams() {
  const q = new URLSearchParams();
  const start = document.getElementById('filterStart')?.value;
  const end = document.getElementById('filterEnd')?.value;
  const year = document.getElementById('filterYear')?.value;
  const month = document.getElementById('filterMonth')?.value;
  const cause = document.getElementById('filterCause')?.value;
  const gov = document.getElementById('filterGovernorate')?.value;
  const del = document.getElementById('filterDelegation')?.value;
  const sev = document.getElementById('filterSeverity')?.value;
  const src = document.getElementById('filterSource')?.value;
  if (start) q.set('start', start);
  if (end) q.set('end', end);
  if (year) q.set('year', year);
  if (month) q.set('month', month);
  if (cause) q.set('cause', cause);
  if (gov) q.set('governorate', gov);
  if (del) q.set('delegation', del);
  if (sev) q.set('severity', sev);
  if (src) q.set('source', src);
  return q;
}

function buildUrlWithFilters(base, extras) {
  const q = getFilterParams();
  if (extras) {
    Object.keys(extras).forEach(k => {
      if (extras[k] !== undefined && extras[k] !== null && extras[k] !== '') q.set(k, extras[k]);
    });
  }
  const qs = q.toString();
  return qs ? `${base}?${qs}` : base;
}

async function applyFilters() {
  // reset to first page to keep UX predictable
  currentPage = 1; showPage(currentPage);
  // re-fetch KPIs and charts
  await loadSummaryCards();
  const activeGran = document.querySelector('#gran-day.active, #gran-month.active, #gran-year.active')?.id?.split('-')[1] || 'month';
  await Promise.all([
    renderTime(activeGran),
    renderSeverity(),
    renderCause(),
    renderDelegation(),
    renderHeatmap(),
    renderStatus(),
    renderSeverityByRegion('governorate'),
    renderSeverityByRegion('delegation'),
    renderCauseBySeverity(),
    renderConfirmedReported(activeGran, document.getElementById('filterYear')?.value || ''),
  ]);
}

function resetFilters() {
  ['filterStart','filterEnd','filterYear','filterMonth','filterGovernorate','filterDelegation','filterCause','filterSeverity','filterSource'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === 'SELECT' || el.tagName === 'INPUT') el.value = '';
  });
  applyFilters();
}

async function populateFilterOptions() {
  // populate governorates and delegations from the API
  try {
    const govRes = await fetch('/api/v1/stats/accidents/by_governorate');
    const govData = await govRes.json();
    const govSel = document.getElementById('filterGovernorate');
    if (govSel) {
      // prefer items[] with label/key/count
      if (govData.items && govData.items.length) {
        govData.items.forEach(it => { const opt = document.createElement('option'); opt.value = it.key || it.label; opt.text = it.label || it.key; govSel.appendChild(opt); });
      } else if (govData.labels) {
        govData.labels.forEach(g => { const opt = document.createElement('option'); opt.value = g; opt.text = g; govSel.appendChild(opt); });
      }
    }
    const delRes = await fetch('/api/v1/stats/accidents/by_delegation');
    const delData = await delRes.json();
    const delSel = document.getElementById('filterDelegation');
    if (delSel) {
      if (delData.items && delData.items.length) {
        delData.items.forEach(it => { const opt = document.createElement('option'); opt.value = it.key || it.label; opt.text = it.label || it.key; delSel.appendChild(opt); });
      } else if (delData.labels) {
        delData.labels.forEach(d => { const opt = document.createElement('option'); opt.value = d; opt.text = d; delSel.appendChild(opt); });
      }
    }
    // populate causes from breakdown endpoint
    try {
      const causeRes = await fetch('/api/v1/stats/accidents/by_cause');
      const causeData = await causeRes.json();
      const causeSel = document.getElementById('filterCause');
      if (causeSel) {
        if (causeData.items && causeData.items.length) {
          causeData.items.forEach(it => { const opt = document.createElement('option'); opt.value = it.key || it.label; opt.text = it.label || (it.key || '').replace(/_/g,' '); causeSel.appendChild(opt); });
        } else if (causeData.labels) {
          causeData.labels.forEach(c => { const opt = document.createElement('option'); opt.value = c; opt.text = (c || '').replace(/_/g,' '); causeSel.appendChild(opt); });
        }
      }
    } catch (e) { console.warn('Failed to populate causes', e); }
    // populate year and month selects
    const yearSel = document.getElementById('filterYear');
    if (yearSel) {
      const currentYear = new Date().getFullYear();
      for (let y = currentYear; y >= currentYear - 5; y--) {
        const opt = document.createElement('option'); opt.value = y; opt.text = y; yearSel.appendChild(opt);
      }
      yearSel.addEventListener('change', () => { applyFilters(); });
    }
    const monthSel = document.getElementById('filterMonth');
    if (monthSel) {
      const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
      months.forEach((m, idx) => { const opt = document.createElement('option'); opt.value = String(idx+1).padStart(2,'0'); opt.text = m; monthSel.appendChild(opt); });
      monthSel.addEventListener('change', () => { applyFilters(); });
    }
  } catch (err) {
    console.warn('Failed to populate filter options', err);
  }
}

async function setGranularity(gran) {
  document.querySelectorAll('#gran-day,#gran-month,#gran-year').forEach(b => b.classList.remove('active'));
  document.getElementById(`gran-${gran}`).classList.add('active');
  await renderTime(gran);
}

/* =======================
   SEVERITY
======================= */
async function renderSeverity() {
  showSkeleton('severity');
  toggleCardForSkeleton('skeleton-severity', true);
  const res = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_severity'));
  const data = await res.json();
  // accept either { labels, values } or { items: [{key,label,count}] }
  const hasItems = data.items && data.items.length;
  const labels = hasItems ? data.items.map(i => i.label || i.key) : (data.labels || []);
  const values = (hasItems ? data.items.map(i => i.count || 0) : (data.values || [])).map(v => Number(v) || 0);
  // drop any 'Moderate' bucket if present (not part of desired legend)
  const filteredLabels = [];
  const filteredValues = [];
  labels.forEach((lab, idx) => {
    if (String(lab).trim().toLowerCase() === 'moderate') return;
    filteredLabels.push(lab);
    filteredValues.push(values[idx] || 0);
  });
  if (!filteredLabels.length) { hideSkeleton('severity'); toggleCardForSkeleton('skeleton-severity', false); return; }
  hideSkeleton('severity');
  toggleCardForSkeleton('skeleton-severity', true);
  const ctx = document.getElementById("severityChart").getContext("2d");
  const canvas = document.getElementById('severityChart');
  if (severityChart) severityChart.destroy();

  const baseColors = (ChartTheme.colors && ChartTheme.colors.severity) ? ChartTheme.colors.severity : ['#e74c3c','#f59e0b','#10b981','#2563eb'];
  const bgColors = filteredLabels.map((_, idx) => baseColors[idx % baseColors.length]);

  try {
    severityChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: filteredLabels,
        datasets: [{
          data: filteredValues,
          backgroundColor: bgColors.length ? bgColors : baseColors,
          borderColor: 'transparent',
          borderWidth: 0,
          hoverBorderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        plugins: {
          legend: { position: "bottom" },
          tooltip: {
            ...ChartTheme.tooltip,
            callbacks: {
              label: (ctx) => {
                const total = filteredValues.reduce((a,b)=>a+(b||0),0) || 0;
                const val = ctx.parsed || 0;
                const pct = total ? ((val/total)*100).toFixed(1) : '0.0';
                return `${ctx.label}: ${val.toLocaleString()} (${pct}%)`;
              }
            }
          }
        },
        animation: ChartTheme.animation,
        onHover: function (_, el) {
          if (!el.length) return;
          const i = el[0].index;
          const total = filteredValues.reduce((a,b)=>a+(b||0),0) || 0;
          const pct = total ? ((filteredValues[i] || 0)/total*100).toFixed(1) : '0.0';
          updateInfo("Severity", [
            { label: "Severity", value: filteredLabels[i] },
            { label: "Accidents", value: filteredValues[i] },
            { label: "Percent", value: `${pct}%` }
          ]);
        }
      }
    });
  } catch (e) {
    console.warn('severity chart render failed', e);
  }
  // ensure the canvas is visible after render
  if (canvas) canvas.style.display = 'block';
}

/* =======================
   CAUSE
======================= */
async function renderCause() {
  showSkeleton('cause');
  toggleCardForSkeleton('skeleton-cause', true);
  const res = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_cause'));
  const data = await res.json();
  // accept either { labels, values } or { items: [{key,label,count}] }
  const hasItemsC = data.items && data.items.length;
  const pairs = hasItemsC
    ? data.items.map(i => ({ label: prettifyLabel(i.label || i.key), value: Number(i.count) || 0 }))
    : (data.labels || []).map((l, idx) => ({ label: prettifyLabel(l), value: Number((data.values || [])[idx]) || 0 }));
  // sort descending but keep every cause (no aggregation)
  pairs.sort((a, b) => (b.value || 0) - (a.value || 0));
  const maxInline = 8;
  const inlinePairs = pairs.slice(0, maxInline);
  const cLabels = inlinePairs.map(p => p.label);
  const cValues = inlinePairs.map(p => p.value);
  if (!cLabels.length) { hideSkeleton('cause'); toggleCardForSkeleton('skeleton-cause', false); return; }
  hideSkeleton('cause');
  toggleCardForSkeleton('skeleton-cause', true);
  const canvasEl = document.getElementById("causeChart");
  const ctx = canvasEl.getContext("2d");
  if (causeChart) causeChart.destroy();
  // make the inline chart readable by growing height based on number of bars
  const desiredHeight = Math.max(220, cLabels.length * 28);
  canvasEl.style.height = `${desiredHeight}px`;

  const causeColors = ['#e74c3c', '#f59e0b', '#10b981', '#2563eb', '#9b59b6', '#f97316', '#0ea5e9', '#fbbf24'];
  const barColors = cLabels.map((_, idx) => causeColors[idx % causeColors.length]);
  const fullColors = pairs.map((_, idx) => causeColors[idx % causeColors.length]);

  causeChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: cLabels,
      datasets: [{
        data: cValues,
        backgroundColor: barColors,
        borderRadius: 0,
        borderSkipped: false,
        barThickness: 18,
        maxBarThickness: 22,
        categoryPercentage: 0.9,
        barPercentage: 0.9
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 6, right: 12, bottom: 6, left: 8 } },
      plugins: {
        legend: { display: false },
        tooltip: {
          ...ChartTheme.tooltip,
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.parsed.y?.toLocaleString ? ctx.parsed.y.toLocaleString() : ctx.parsed}`
          }
        }
      },
      animation: ChartTheme.animation,
      indexAxis: 'y',
      scales: {
        x: { grid: { display: true, color: 'rgba(0,0,0,0.05)' } },
        y: { grid: { display: false }, ticks: { autoSkip: false, maxTicksLimit: 60 } }
      },
      onHover: function (_, el) {
        if (!el.length) return;
        const i = el[0].index;
        updateInfo("Cause", [
          { label: "Cause", value: cLabels[i] },
          { label: "Accidents", value: cValues[i] }
        ]);
      }
    }
  });
  // store full data for zoom overlay
  causeChart._fullData = { labels: pairs.map(p => p.label), values: pairs.map(p => p.value), colors: fullColors };
}

/* =======================
   TIME
======================= */
async function renderTime(granularity = 'month') {
  showSkeleton('time');
  toggleCardForSkeleton('skeleton-time', true);
  const area = document.getElementById('toggleArea')?.checked || false;
  const stacked = document.getElementById('toggleStack')?.checked || false;
  const res = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_month', { granularity: granularity, series: 'total' }));
  const data = await res.json();
  // data may be { labels, values } or { labels, datasets: [{ label, values}] }
  const multi = data.datasets && Array.isArray(data.datasets) && data.datasets.length;
  if (!data.labels || (!data.values && !multi)) { hideSkeleton('time'); toggleCardForSkeleton('skeleton-time', false); return; }
  hideSkeleton('time');
  toggleCardForSkeleton('skeleton-time', true);
  const ctx = document.getElementById("timeChart").getContext("2d");
  if (timeChart) timeChart.destroy();
  // build datasets depending on server response and UI toggles
  const datasets = [];
  if (multi) {
    // server provided datasets array
    data.datasets.forEach((ds, idx) => {
      const color = (ChartTheme.colors && ChartTheme.colors.severity && ChartTheme.colors.severity[idx]) || ChartTheme.palette.primaryA;
      datasets.push({ label: ds.label || `Series ${idx+1}`, data: ds.values || ds.data || [], fill: area, backgroundColor: area ? color + '55' : 'transparent', borderColor: color, tension: 0.3, stack: stacked ? 's1' : undefined });
    });
  } else {
    // single series
    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, "rgba(59,130,246,0.45)");
    gradient.addColorStop(1, "rgba(59,130,246,0)");
    datasets.push({ label: 'Accidents', data: data.values || [], fill: area, backgroundColor: area ? gradient : 'transparent', borderColor: ChartTheme.palette.primaryA, tension: 0.4, stack: stacked ? 's1' : undefined });
  }

  timeChart = new Chart(ctx, {
    type: 'line',
    data: { labels: data.labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: ChartTheme.defaults.maintainAspectRatio,
      plugins: { tooltip: ChartTheme.tooltip, legend: { position: 'bottom' } },
      animation: ChartTheme.animation,
      interaction: { mode: 'index', intersect: false },
      scales: { x: { display: true }, y: { stacked: stacked } },
      onHover: function (_, el) {
        if (!el.length) return;
        const i = el[0].index;
        // show generic info from the first dataset
        const val = (timeChart.data.datasets[0] && timeChart.data.datasets[0].data && timeChart.data.datasets[0].data[i]) || '';
        updateInfo("Period", [ { label: "Period", value: data.labels[i] }, { label: "Accidents", value: val } ]);
      }
    }
  });
}

/* =======================
   DELEGATION
======================= */
async function renderDelegation() {
  showSkeleton('delegation');
  toggleCardForSkeleton('skeleton-delegation', true);
  const res = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_delegation'));
  const data = await res.json();
  // accept either { labels, values } or { items: [{key,label,count}] }
  const hasItemsD = data.items && data.items.length;
  const dLabels = hasItemsD ? data.items.map(i => i.label || i.key) : (data.labels || []);
  const dValues = hasItemsD ? data.items.map(i => i.count || 0) : (data.values || []);
  if (!dLabels.length) { hideSkeleton('delegation'); toggleCardForSkeleton('skeleton-delegation', false); return; }
  hideSkeleton('delegation');
  toggleCardForSkeleton('skeleton-delegation', true);
  const ctx = document.getElementById('delegationChart').getContext('2d');
  if (delegationChart) delegationChart.destroy();
  const fill = makeGradient(ctx, ChartTheme.palette.primaryA, ChartTheme.palette.primaryB);

  delegationChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dLabels,
      datasets: [{
        data: dValues,
        backgroundColor: fill,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: ChartTheme.defaults.maintainAspectRatio,
      plugins: { tooltip: ChartTheme.tooltip },
      animation: ChartTheme.animation,
    }
  });
}

/* =======================
   REPORT STATUS
======================= */
async function renderStatus() {
  showSkeleton('status');
  toggleCardForSkeleton('skeleton-status', true);
  const res = await fetch(buildUrlWithFilters('/api/v1/stats/reports/status_counts'));
  const data = await res.json();
  const hasItems = data.items && data.items.length;
  const labels = hasItems ? data.items.map(i => i.label || i.key) : (data.labels || []);
  const values = (hasItems ? data.items.map(i => i.count || 0) : (data.values || [])).map(v => Number(v) || 0);
  if (!labels.length || !values.length) { hideSkeleton('status'); toggleCardForSkeleton('skeleton-status', false); return; }
  const total = values.reduce((a,b)=>a+(b||0),0);
  if (!total) { hideSkeleton('status'); toggleCardForSkeleton('skeleton-status', false); return; }
  hideSkeleton('status');
  toggleCardForSkeleton('skeleton-status', true);
  const canvas = document.getElementById('statusChart');
  const ctx = canvas?.getContext('2d');
  if (!ctx) { console.warn('statusChart context missing'); return; }
  if (canvas) canvas.style.display = 'block';
  if (statusChart) statusChart.destroy();

  const baseColors = (ChartTheme.colors && ChartTheme.colors.severity) ? ChartTheme.colors.severity : ['#e74c3c','#f59e0b','#10b981','#2563eb'];
  const bgColors = labels.map((_, idx) => baseColors[idx % baseColors.length]);

  try {
    statusChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: (bgColors && bgColors.length) ? bgColors : baseColors,
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            ...ChartTheme.tooltip,
            callbacks: {
              label: (ctx) => {
                const val = ctx.parsed || 0;
                const pct = total ? ((val/total)*100).toFixed(1) : '0.0';
                return `${ctx.label}: ${val.toLocaleString()} (${pct}%)`;
              }
            }
          }
        },
      }
    });
  } catch (e) {
    console.warn('status chart render failed', e);
  }
  if (canvas) canvas.style.display = 'block';
}

/* =======================
   SEVERITY BY REGION (stacked)
======================= */
async function renderSeverityByRegion(level = 'governorate') {
  const isGov = level === 'governorate';
  const skelId = isGov ? 'sev-gov' : 'sev-del';
  const canvasId = isGov ? 'severityGovChart' : 'severityDelChart';
  showSkeleton(skelId, canvasId);
  toggleCardForSkeleton(`skeleton-${skelId}`, true);

  const endpoint = isGov ? '/api/v1/stats/accidents/by_governorate' : '/api/v1/stats/accidents/by_delegation';
  const levels = [
    { key: 'HIGH', label: 'High' },
    { key: 'MEDIUM', label: 'Medium' },
    { key: 'LOW', label: 'Low' }
  ];

  const labelSet = new Set();
  const seriesMaps = [];
  try {
    for (const lvl of levels) {
      const res = await fetch(buildUrlWithFilters(endpoint, { severity: lvl.key }));
      const data = await res.json();
      const items = data.items || [];
      const m = {};
      items.forEach(it => { const lab = it.label || it.key || '—'; m[lab] = it.count || 0; labelSet.add(lab); });
      seriesMaps.push(m);
    }
    const labels = Array.from(labelSet);
    if (!labels.length) { hideSkeleton(skelId, canvasId); toggleCardForSkeleton(`skeleton-${skelId}`, false); return; }
    hideSkeleton(skelId, canvasId);
    toggleCardForSkeleton(`skeleton-${skelId}`, true);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    if (isGov && severityGovChart) severityGovChart.destroy();
    if (!isGov && severityDelChart) severityDelChart.destroy();
    const colors = ChartTheme.colors && ChartTheme.colors.severity ? ChartTheme.colors.severity : [ChartTheme.palette.primaryA, ChartTheme.palette.primaryB, ChartTheme.palette.success];
    const datasets = levels.map((lvl, idx) => ({
      label: lvl.label,
      data: labels.map(l => seriesMaps[idx]?.[l] || 0),
      backgroundColor: makeGradient(ctx, colors[idx % colors.length], colors[idx % colors.length]),
      stack: 'severity'
    }));
    const chart = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: ChartTheme.defaults.maintainAspectRatio,
        plugins: { tooltip: ChartTheme.tooltip, legend: { position: 'bottom' } },
        scales: { x: { stacked: true }, y: { stacked: true } }
      }
    });
    if (isGov) severityGovChart = chart; else severityDelChart = chart;
  } catch (e) {
    console.warn('renderSeverityByRegion failed', e);
    hideSkeleton(skelId, canvasId);
    toggleCardForSkeleton(`skeleton-${skelId}`, false);
  }
}

/* =======================
   CAUSE BY SEVERITY (stacked)
======================= */
async function renderCauseBySeverity() {
  const skelId = 'cause-sev';
  showSkeleton(skelId, 'causeSeverityChart');
  toggleCardForSkeleton(`skeleton-${skelId}`, true);
  const levels = [
    { key: 'HIGH', label: 'High' },
    { key: 'MEDIUM', label: 'Medium' },
    { key: 'LOW', label: 'Low' }
  ];
  const labelSet = new Set();
  const seriesMaps = [];
  try {
    for (const lvl of levels) {
      const res = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/by_cause', { severity: lvl.key }));
      const data = await res.json();
      const items = data.items || [];
      const m = {};
      items.forEach(it => { const lab = (it.label || it.key || '—').replace(/_/g, ' '); m[lab] = it.count || 0; labelSet.add(lab); });
      seriesMaps.push(m);
    }
    const labels = Array.from(labelSet);
    if (!labels.length) { hideSkeleton(skelId, 'causeSeverityChart'); toggleCardForSkeleton(`skeleton-${skelId}`, false); return; }
    hideSkeleton(skelId, 'causeSeverityChart');
    toggleCardForSkeleton(`skeleton-${skelId}`, true);
    const ctx = document.getElementById('causeSeverityChart')?.getContext('2d');
    if (!ctx) return;
    if (causeSeverityChart) { try { causeSeverityChart.destroy(); } catch(e){} }
    const colors = ChartTheme.colors && ChartTheme.colors.severity ? ChartTheme.colors.severity : [ChartTheme.palette.primaryA, ChartTheme.palette.primaryB, ChartTheme.palette.success];
    const datasets = levels.map((lvl, idx) => ({
      label: lvl.label,
      data: labels.map(l => seriesMaps[idx]?.[l] || 0),
      backgroundColor: makeGradient(ctx, colors[idx % colors.length], colors[idx % colors.length]),
      stack: 'causes'
    }));
    causeSeverityChart = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: ChartTheme.defaults.maintainAspectRatio,
        plugins: { tooltip: ChartTheme.tooltip, legend: { position: 'bottom' } },
        scales: { x: { stacked: true }, y: { stacked: true } }
      }
    });
  } catch (e) {
    console.warn('renderCauseBySeverity failed', e);
    hideSkeleton(skelId, 'causeSeverityChart');
    toggleCardForSkeleton(`skeleton-${skelId}`, false);
  }
}

/* =======================
   CONFIRMED vs REPORTED
======================= */
async function renderConfirmedReported(granularity = 'month', year = '') {
  showSkeleton('confirmed', 'confirmedReportedChart');
  toggleCardForSkeleton('skeleton-confirmed', true);
  const res = await fetch(buildUrlWithFilters('/api/v1/stats/reports/confirmed_vs_reported', { granularity: granularity, year: year }));
  const data = await res.json();
  if (!data.labels) { hideSkeleton('confirmed', 'confirmedReportedChart'); toggleCardForSkeleton('skeleton-confirmed', false); return; }
  hideSkeleton('confirmed', 'confirmedReportedChart');
  toggleCardForSkeleton('skeleton-confirmed', true);
  const ctx = document.getElementById('confirmedReportedChart').getContext('2d');
  if (typeof confirmedReportedChart !== 'undefined' && confirmedReportedChart && typeof confirmedReportedChart.destroy === 'function') {
    try { confirmedReportedChart.destroy(); } catch(e){}
  }
  // warm palette to match overlay preview (red/yellow)
  const gReported = makeGradient(ctx, '#c0392b', '#e74c3c');
  const gConfirmed = makeGradient(ctx, '#d97706', '#f59e0b');

  confirmedReportedChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
          { label: 'Reported', data: data.reported, backgroundColor: gReported, stack: 'reports' },
          { label: 'Confirmed', data: data.confirmed, backgroundColor: gConfirmed, stack: 'reports' }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: ChartTheme.defaults.maintainAspectRatio,
      plugins: { tooltip: ChartTheme.tooltip },
      scales: {
        x: { stacked: true },
        y: { stacked: true }
      }
    }
  });
}

// year/month filter population and handlers are wired in populateFilterOptions()

/* =======================
   HEATMAP (Hour vs Weekday)
   Expects optional endpoint /api/v1/stats/accidents/hour_weekday which returns:
   { hours: [0..23], weekdays: ['Mon','Tue',...], matrix: [[v...], ...] }
   If the endpoint doesn't exist, shows 'No data for current filters'.
======================= */
async function renderHeatmap() {
  showSkeleton('heatmap');
  toggleCardForSkeleton('skeleton-heatmap', true);
  const container = document.getElementById('heatmapContent');
  const legend = document.getElementById('heatmapLegend');
  if (!container) {
    console.warn('renderHeatmap: heatmapContent element not found in DOM');
    hideSkeleton('heatmap');
    toggleCardForSkeleton('skeleton-heatmap', false);
    if (legend) legend.innerHTML = '';
    return;
  }
  try {
    const res = await fetch(buildUrlWithFilters('/api/v1/stats/accidents/hour_weekday'));
    if (!res.ok) { throw new Error('no heatmap endpoint'); }
    const data = await res.json();
    if (!data || !data.hours || !data.weekdays || !data.matrix) { throw new Error('invalid heatmap data'); }
    
    // Filter to only hours that have at least one accident
    const activeHours = [];
    data.hours.forEach((h, idx) => {
      let hasData = false;
      data.matrix.forEach(row => { if (row[idx] > 0) hasData = true; });
      if (hasData) activeHours.push({ hour: h, idx: idx });
    });
    
    // If no active hours, show message
    if (activeHours.length === 0) {
      container.innerHTML = '<div class="text-muted small text-center py-4">No data for current filters</div>';
      hideSkeleton('heatmap');
      container.style.display = '';
      return;
    }
    
    // render a simple grid: weekdays rows x active hours columns
    container.innerHTML = '';
    const grid = document.createElement('div'); grid.className = 'heatmap-grid';
    
    // compute max for color scaling
    let max = 0; data.matrix.forEach(row => row.forEach(v => { if (v>max) max=v; }));
    
    // Add hour header row
    const headerRow = document.createElement('div'); headerRow.className = 'hm-header';
    activeHours.forEach(({ hour }) => {
      const hCell = document.createElement('div'); hCell.className = 'hm-header-cell';
      hCell.textContent = hour;
      headerRow.appendChild(hCell);
    });
    grid.appendChild(headerRow);
    
    // Weekday abbreviations
    const wdShort = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    data.weekdays.forEach((wd, rIdx) => {
      const row = document.createElement('div'); row.className = 'hm-row';
      
      // Row label (weekday)
      const label = document.createElement('div'); label.className = 'hm-row-label';
      label.textContent = wdShort[rIdx] || wd.slice(0,3);
      row.appendChild(label);
      
      activeHours.forEach(({ hour, idx }) => {
        const v = (data.matrix[rIdx] && data.matrix[rIdx][idx]) || 0;
        const pct = max ? v / max : 0;
        // Use a blue gradient
        const color = pct === 0 ? 'rgba(59,130,246,0.08)' : `rgba(59,130,246,${0.2 + 0.7 * pct})`;
        const cell = document.createElement('div'); cell.className = 'hm-cell'; 
        cell.style.background = color; 
        cell.style.color = pct > 0.5 ? '#fff' : 'var(--ui-text)';
        cell.title = `${wd} ${hour}:00 — ${v} accidents`;
        cell.textContent = v ? v : '';
        row.appendChild(cell);
      });
      grid.appendChild(row);
    });
    container.appendChild(grid);
    
    // Gradient legend
    legend.innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;">Low <span style="display:inline-block;width:60px;height:12px;border-radius:3px;background:linear-gradient(90deg,rgba(59,130,246,0.15),rgba(59,130,246,0.9));"></span> High</span>`;
    hideSkeleton('heatmap');
    container.style.display = '';
    toggleCardForSkeleton('skeleton-heatmap', true);
  } catch (e) {
    // no data
    hideSkeleton('heatmap');
      try { if (container) container.style.display = 'none'; } catch(e){}
    toggleCardForSkeleton('skeleton-heatmap', false);
    if (legend) legend.innerHTML = '';
  }
}

/* =======================
   SANKEY: Cause -> Severity -> Location
======================= */
async function renderSankey() {
  const sk = document.getElementById('skeleton-sankey');
  const el = document.getElementById('sankeyChart');
  if (!el) return;
  if (sk) sk.style.display = '';
  try { el.innerHTML = ''; } catch(e){}
  try {
    const res = await fetch(buildUrlWithFilters('/api/v1/stats/sankey/cause_severity_location'));
    const data = await res.json();
    if (!data || !data.nodes || !data.links || !data.links.length) {
      if (sk) sk.style.display = 'none';
      el.innerHTML = '<div class="text-muted small">No data for current filters</div>';
      return;
    }
    const plotData = [{
      type: 'sankey',
      orientation: 'h',
      node: { label: data.nodes, pad: 12, thickness: 18 },
      link: { source: data.links.map(l => l.source), target: data.links.map(l => l.target), value: data.links.map(l => l.value) }
    }];
    const layout = { margin: { l: 10, r: 10, t: 10, b: 10 }, height: 320, font: { family: 'Inter, system-ui', size: 12 } };
    Plotly.newPlot(el, plotData, layout, {displayModeBar: false});
  } catch (e) {
    console.warn('sankey render failed', e);
    el.innerHTML = '<div class="text-muted small">Failed to load sankey</div>';
  } finally {
    if (sk) sk.style.display = 'none';
  }
}

/* =======================
   SMALL MULTIPLES & SPARKLINES
======================= */
async function fetchGovTimeseries(months=6, top=6) {
  const res = await fetch(buildUrlWithFilters(`/api/v1/stats/accidents/by_governorate_timeseries?months=${months}&top=${top}`));
  return await res.json();
}

async function renderGovSmallMultiples() {
  const container = document.getElementById('govSmallMultiples');
  if (!container) return;
  container.innerHTML = '';
  smallMultipleCharts.forEach(ch => { try { ch.destroy(); } catch(e){} });
  smallMultipleCharts = [];
  const data = await fetchGovTimeseries(6, 6);
  if (!data || !data.series || !data.series.length) {
    container.innerHTML = '<div class="text-muted small">No data for current filters</div>';
    return;
  }
  data.series.forEach((s) => {
    const col = document.createElement('div'); col.className = 'col';
    const card = document.createElement('div'); card.className = 'p-2 border rounded bg-white';
    const title = document.createElement('div'); title.className = 'small fw-semibold mb-1'; title.textContent = s.label || '—';
    const canvas = document.createElement('canvas'); canvas.style.height = '120px'; canvas.style.width = '100%';
    card.appendChild(title); card.appendChild(canvas); col.appendChild(card); container.appendChild(col);
    const ctx = canvas.getContext('2d');
    const ch = new Chart(ctx, {
      type: 'line',
      data: { labels: data.labels, datasets: [{ data: s.values || [], borderColor: ChartTheme.palette.primaryA, backgroundColor: ChartTheme.palette.primaryA + '33', fill: true, tension: 0.35, pointRadius: 0 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } }, scales: { x: { display: false }, y: { display: false } } }
    });
    smallMultipleCharts.push(ch);
  });
}

async function renderSparklineTable() {
  const tbody = document.getElementById('sparklineTable');
  if (!tbody) return;
  tbody.innerHTML = '';
  sparklineCharts.forEach(ch => { try { ch.destroy(); } catch(e){} });
  sparklineCharts = [];
  const data = await fetchGovTimeseries(6, 8);
  if (!data || !data.series || !data.series.length) {
    tbody.innerHTML = '<tr><td colspan="2" class="text-muted small">No data for current filters</td></tr>';
    return;
  }
  data.series.forEach(s => {
    const tr = document.createElement('tr');
    const tdName = document.createElement('td'); tdName.textContent = s.label || '—';
    const tdSpark = document.createElement('td'); tdSpark.className = 'text-end';
    const canvas = document.createElement('canvas'); canvas.style.height = '40px'; canvas.style.width = '120px';
    tdSpark.appendChild(canvas);
    tr.appendChild(tdName); tr.appendChild(tdSpark); tbody.appendChild(tr);
    const ctx = canvas.getContext('2d');
    const ch = new Chart(ctx, {
      type: 'line',
      data: { labels: data.labels, datasets: [{ data: s.values || [], borderColor: ChartTheme.palette.primaryB, backgroundColor: ChartTheme.palette.primaryB + '33', fill: true, tension: 0.35, pointRadius: 0 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } }, scales: { x: { display: false }, y: { display: false } } }
    });
    sparklineCharts.push(ch);
  });
}

/* =======================
   TIMELINE SCRUBBER
======================= */
function updateTimelineScrubber(labels) {
  const slider = document.getElementById('timeScrubber');
  const lbl = document.getElementById('timeScrubberLabel');
  if (!slider || !labels || !labels.length) return;
  timelineLabels = labels;
  slider.max = labels.length - 1;
  slider.value = labels.length - 1;
  if (lbl) lbl.textContent = labels[labels.length - 1] || '—';
}

document.addEventListener('input', (ev) => {
  if (ev.target && ev.target.id === 'timeScrubber') {
    const idx = Number(ev.target.value) || 0;
    const lbl = document.getElementById('timeScrubberLabel');
    if (lbl && timelineLabels[idx]) lbl.textContent = timelineLabels[idx];
  }
});
