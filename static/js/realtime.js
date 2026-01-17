/**
 * Real-time Dashboard Updates
 * Uses Server-Sent Events (SSE) for live updates
 */

(function() {
  'use strict';

  let eventSource = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 3000;

  // Dashboard elements to update
  const elements = {
    accidentsCount: '.kpi-value[data-stat="accidents"]',
    reportsCount: '.kpi-value[data-stat="reports"]',
    importsCount: '.kpi-value[data-stat="imports"]',
    recentTable: '#recentAccidentsTable tbody'
  };

  /**
   * Connect to SSE endpoint
   */
  function connect() {
    if (eventSource) {
      eventSource.close();
    }

    // Check if on dashboard page
    if (!window.location.pathname.includes('dashboard')) {
      return;
    }

    try {
      eventSource = new EventSource('/api/events/dashboard');

      eventSource.onopen = () => {
        console.log('Real-time connection established');
        reconnectAttempts = 0;
        updateConnectionStatus(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleUpdate(data);
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      };

      eventSource.addEventListener('stats', (event) => {
        try {
          const stats = JSON.parse(event.data);
          updateStats(stats);
        } catch (e) {
          console.error('Error parsing stats:', e);
        }
      });

      eventSource.addEventListener('accident', (event) => {
        try {
          const accident = JSON.parse(event.data);
          addNewAccident(accident);
          showNotification('New Accident Reported', accident.location || 'Unknown location');
        } catch (e) {
          console.error('Error parsing accident:', e);
        }
      });

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        eventSource.close();
        updateConnectionStatus(false);
        attemptReconnect();
      };

    } catch (e) {
      console.error('Failed to create EventSource:', e);
      // Fallback to polling
      startPolling();
    }
  }

  /**
   * Attempt to reconnect
   */
  function attemptReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++;
      console.log(`Reconnecting in ${RECONNECT_DELAY}ms (attempt ${reconnectAttempts})`);
      setTimeout(connect, RECONNECT_DELAY);
    } else {
      console.log('Max reconnect attempts reached, falling back to polling');
      startPolling();
    }
  }

  /**
   * Fallback: Poll for updates
   */
  let pollingInterval = null;

  function startPolling() {
    if (pollingInterval) return;

    pollingInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/stats/dashboard');
        if (response.ok) {
          const stats = await response.json();
          updateStats(stats);
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 30000); // Poll every 30 seconds
  }

  function stopPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  }

  /**
   * Update dashboard stats
   */
  function updateStats(stats) {
    // Update KPI cards with animation
    if (stats.total_accidents !== undefined) {
      animateValue(elements.accidentsCount, stats.total_accidents);
    }
    if (stats.reports_count !== undefined) {
      animateValue(elements.reportsCount, stats.reports_count);
    }
    if (stats.imports_today !== undefined) {
      animateValue(elements.importsCount, stats.imports_today);
    }
  }

  /**
   * Animate number change
   */
  function animateValue(selector, newValue) {
    const element = document.querySelector(selector);
    if (!element) return;

    const currentValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
    
    if (currentValue === newValue) return;

    // Add highlight effect
    element.classList.add('stat-updated');
    
    // Animate the number
    const duration = 500;
    const steps = 20;
    const increment = (newValue - currentValue) / steps;
    let current = currentValue;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current += increment;
      
      if (step >= steps) {
        element.textContent = newValue.toLocaleString();
        clearInterval(timer);
        
        // Remove highlight
        setTimeout(() => {
          element.classList.remove('stat-updated');
        }, 1000);
      } else {
        element.textContent = Math.round(current).toLocaleString();
      }
    }, duration / steps);
  }

  /**
   * Add new accident to recent table
   */
  function addNewAccident(accident) {
    const tbody = document.querySelector(elements.recentTable);
    if (!tbody) return;

    const row = document.createElement('tr');
    row.className = 'new-row-highlight';
    row.innerHTML = `
      <td>${accident.id}</td>
      <td>${accident.occurred_at || 'N/A'}</td>
      <td>${accident.location || 'Unknown'}</td>
      <td><span class="badge bg-${getSeverityClass(accident.severity)}">${accident.severity || 'Unknown'}</span></td>
      <td><a href="/ui/accidents/${accident.id}">View</a></td>
    `;

    // Add at top
    tbody.insertBefore(row, tbody.firstChild);

    // Remove last row if too many
    if (tbody.children.length > 10) {
      tbody.removeChild(tbody.lastChild);
    }

    // Remove highlight after animation
    setTimeout(() => {
      row.classList.remove('new-row-highlight');
    }, 3000);
  }

  /**
   * Get severity badge class
   */
  function getSeverityClass(severity) {
    const map = {
      'fatal': 'danger',
      'severe': 'warning',
      'moderate': 'info',
      'minor': 'secondary'
    };
    return map[severity?.toLowerCase()] || 'secondary';
  }

  /**
   * Show notification
   */
  function showNotification(title, message) {
    if (window.Toast) {
      Toast.info(message, title);
    }
  }

  /**
   * Update connection status indicator
   */
  function updateConnectionStatus(connected) {
    const indicator = document.querySelector('.realtime-indicator');
    if (indicator) {
      indicator.classList.toggle('connected', connected);
      indicator.title = connected ? 'Live updates active' : 'Reconnecting...';
    }
  }

  /**
   * Handle generic update
   */
  function handleUpdate(data) {
    if (data.type === 'stats') {
      updateStats(data);
    } else if (data.type === 'accident') {
      addNewAccident(data.accident);
    }
  }

  /**
   * Disconnect
   */
  function disconnect() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    stopPolling();
  }

  // Initialize on page load
  document.addEventListener('DOMContentLoaded', () => {
    // Only connect on dashboard
    if (window.location.pathname.includes('dashboard')) {
      // Start with polling (more reliable than SSE for this demo)
      startPolling();
    }
  });

  // Cleanup on page unload
  window.addEventListener('beforeunload', disconnect);

  // Expose API
  window.RealtimeUpdates = {
    connect,
    disconnect,
    refresh: () => {
      fetch('/api/stats/dashboard')
        .then(r => r.json())
        .then(updateStats)
        .catch(console.error);
    }
  };

})();
