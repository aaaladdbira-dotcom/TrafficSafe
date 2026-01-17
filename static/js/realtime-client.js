/**
 * WebSocket Real-Time Client
 * ===========================
 * Connect to server for live accident updates and KPI notifications
 */

class RealtimeClient {
  constructor(options = {}) {
    this.options = {
      url: options.url || `${window.location.protocol.replace('http', 'ws')}//${window.location.host}`,
      autoConnect: options.autoConnect !== false,
      debug: options.debug || false,
      ...options
    };
    
    this.socket = null;
    this.isConnected = false;
    this.subscriptions = new Map();
    this.listeners = new Map();
    
    if (this.options.autoConnect) {
      this.connect();
    }
  }
  
  connect() {
    try {
      // Import Socket.IO client
      if (typeof io === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
        document.head.appendChild(script);
        script.onload = () => this.initializeSocket();
        return;
      }
      
      this.initializeSocket();
    } catch (error) {
      this.log('Connection error:', error);
    }
  }
  
  initializeSocket() {
    const token = localStorage.getItem('access_token');
    
    this.socket = io(this.options.url, {
      query: { token: token || '' },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });
    
    // Setup event handlers
    this.socket.on('connect', () => {
      this.isConnected = true;
      this.log('Connected to real-time server');
      this.emit('connected', { timestamp: new Date() });
    });
    
    this.socket.on('disconnect', () => {
      this.isConnected = false;
      this.log('Disconnected from server');
      this.emit('disconnected', { timestamp: new Date() });
    });
    
    this.socket.on('connection_response', (data) => {
      this.log('Server response:', data);
    });
    
    this.socket.on('subscription_confirmed', (data) => {
      this.log('Subscription confirmed:', data);
      this.emit('subscribed', data);
    });
    
    // Real-time data events
    this.socket.on('new_accident', (data) => {
      this.log('New accident:', data);
      this.emit('accident', data);
      this.showNotification('New Accident', `${data.location} - ${data.severity}`);
    });
    
    this.socket.on('kpi_update', (data) => {
      this.log('KPI update:', data);
      this.emit('kpi_update', data);
    });
    
    this.socket.on('live_stats', (data) => {
      this.log('Live stats:', data);
      this.emit('stats_update', data);
    });
    
    this.socket.on('pong', (data) => {
      this.log('Pong received');
    });
    
    this.socket.on('error', (error) => {
      this.log('Socket error:', error);
      this.emit('error', error);
    });
  }
  
  subscribe(type, filters = {}) {
    if (!this.socket) {
      this.log('Socket not connected');
      return false;
    }
    
    const subscriptionKey = `${type}:${JSON.stringify(filters)}`;
    
    if (type === 'accidents') {
      this.socket.emit('subscribe_accidents', { filters });
    } else if (type === 'kpis') {
      this.socket.emit('subscribe_kpis');
    }
    
    this.subscriptions.set(subscriptionKey, { type, filters });
    return true;
  }
  
  unsubscribe(type) {
    if (!this.socket) return false;
    
    this.socket.emit('unsubscribe', { type });
    
    // Remove from subscriptions map
    for (let [key, value] of this.subscriptions) {
      if (value.type === type) {
        this.subscriptions.delete(key);
      }
    }
    
    return true;
  }
  
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }
  
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }
  
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          this.log(`Error in ${event} listener:`, error);
        }
      });
    }
  }
  
  ping() {
    if (this.socket) {
      this.socket.emit('ping');
    }
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.isConnected = false;
    }
  }
  
  showNotification(title, message) {
    // Use Toast if available
    if (window.Toast) {
      Toast.info(`${title}: ${message}`);
    }
    
    // Browser notification if supported
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: '/static/images/icon.png'
      });
    }
  }
  
  log(...args) {
    if (this.options.debug) {
      console.log('[RealtimeClient]', ...args);
    }
  }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  // Create global instance
  window.realtimeClient = new RealtimeClient({
    debug: false,
    autoConnect: true
  });
  
  // Request notification permission
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
  
  // Subscribe to accidents on dashboard
  if (document.querySelector('[data-page="dashboard"]')) {
    window.realtimeClient.subscribe('accidents', { severity: 'high' });
    window.realtimeClient.subscribe('kpis');
    
    // Update dashboard on new accident
    window.realtimeClient.on('accident', (data) => {
      // Trigger dashboard refresh
      if (window.refreshDashboard) {
        window.refreshDashboard();
      }
    });
  }
});
