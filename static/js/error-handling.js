/**
 * Error Handling & Retry Mechanisms
 * Graceful error states, automatic retry, and user feedback
 */

(function() {
  'use strict';

  // ============================================
  // ERROR HANDLER CLASS
  // ============================================
  
  class ErrorHandler {
    constructor() {
      this.retryAttempts = new Map();
      this.maxRetries = 3;
      this.retryDelays = [1000, 2000, 4000]; // Exponential backoff
      this.errorCallbacks = new Set();
    }

    /**
     * Wrap an async function with error handling and retry logic
     */
    async withRetry(fn, options = {}) {
      const {
        maxRetries = this.maxRetries,
        retryCondition = () => true,
        onRetry = () => {},
        onError = () => {},
        retryKey = null
      } = options;

      let lastError;
      const key = retryKey || fn.toString().slice(0, 50);
      
      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          const result = await fn();
          this.retryAttempts.delete(key);
          return result;
        } catch (error) {
          lastError = error;
          
          if (attempt < maxRetries && retryCondition(error)) {
            const delay = this.retryDelays[attempt] || this.retryDelays[this.retryDelays.length - 1];
            this.retryAttempts.set(key, { attempt: attempt + 1, maxRetries });
            onRetry(attempt + 1, maxRetries, delay);
            await this.sleep(delay);
          } else {
            onError(error);
          }
        }
      }
      
      throw lastError;
    }

    /**
     * Sleep helper
     */
    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Check if error is retryable
     */
    isRetryable(error) {
      // Network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return true;
      }
      
      // Server errors (5xx)
      if (error.status >= 500) {
        return true;
      }
      
      // Rate limiting (429)
      if (error.status === 429) {
        return true;
      }
      
      // Timeout errors
      if (error.name === 'AbortError') {
        return true;
      }
      
      return false;
    }

    /**
     * Handle API errors gracefully
     */
    handleApiError(error, context = {}) {
      const errorInfo = {
        message: error.message,
        status: error.status,
        context,
        timestamp: new Date().toISOString()
      };

      // Log for debugging
      console.error('[API Error]', errorInfo);

      // Determine user-friendly message
      let userMessage;
      if (error.status === 401) {
        userMessage = 'Your session has expired. Please log in again.';
        // Redirect to login after delay
        setTimeout(() => {
          window.location.href = '/ui/login';
        }, 2000);
      } else if (error.status === 403) {
        userMessage = 'You don\'t have permission to perform this action.';
      } else if (error.status === 404) {
        userMessage = 'The requested resource was not found.';
      } else if (error.status >= 500) {
        userMessage = 'A server error occurred. Please try again later.';
      } else if (!navigator.onLine) {
        userMessage = 'You appear to be offline. Please check your connection.';
      } else {
        userMessage = 'An unexpected error occurred. Please try again.';
      }

      // Show toast notification
      this.showErrorToast(userMessage);
      
      // Notify listeners
      this.errorCallbacks.forEach(cb => cb(errorInfo));

      return errorInfo;
    }

    /**
     * Show error toast
     */
    showErrorToast(message, options = {}) {
      if (typeof showToast === 'function') {
        showToast(message, 'error', options.duration || 5000);
      } else {
        // Fallback: create inline toast
        this.createFallbackToast(message, 'error');
      }
    }

    /**
     * Show success toast
     */
    showSuccessToast(message, options = {}) {
      if (typeof showToast === 'function') {
        showToast(message, 'success', options.duration || 3000);
      } else {
        this.createFallbackToast(message, 'success');
      }
    }

    /**
     * Create fallback toast if toast system not available
     */
    createFallbackToast(message, type = 'info') {
      let container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
      }

      const toast = document.createElement('div');
      toast.className = `toast-notification toast-${type}`;
      toast.innerHTML = `
        <div class="toast-icon">
          ${type === 'error' ? '❌' : type === 'success' ? '✓' : 'ℹ'}
        </div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
      `;

      container.appendChild(toast);
      
      // Animate in
      requestAnimationFrame(() => {
        toast.classList.add('toast-visible');
      });

      // Auto remove
      setTimeout(() => {
        toast.classList.add('toast-hiding');
        setTimeout(() => toast.remove(), 300);
      }, 5000);
    }

    /**
     * Register error callback
     */
    onError(callback) {
      this.errorCallbacks.add(callback);
      return () => this.errorCallbacks.delete(callback);
    }
  }

  // ============================================
  // API CLIENT WITH ERROR HANDLING
  // ============================================
  
  class ApiClient {
    constructor(baseUrl = '') {
      this.baseUrl = baseUrl;
      this.errorHandler = new ErrorHandler();
      this.defaultTimeout = 30000;
    }

    async fetch(url, options = {}) {
      const {
        timeout = this.defaultTimeout,
        retry = true,
        maxRetries = 3,
        ...fetchOptions
      } = options;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const headers = {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      };

      // Add auth token if available
      const token = this.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const doFetch = async () => {
        try {
          const response = await fetch(this.baseUrl + url, {
            ...fetchOptions,
            headers,
            signal: controller.signal
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            const error = new Error(response.statusText);
            error.status = response.status;
            try {
              error.data = await response.json();
            } catch (e) {}
            throw error;
          }

          return response.json();
        } catch (error) {
          clearTimeout(timeoutId);
          throw error;
        }
      };

      if (retry) {
        return this.errorHandler.withRetry(doFetch, {
          maxRetries,
          retryCondition: (error) => this.errorHandler.isRetryable(error),
          onRetry: (attempt, max, delay) => {
            console.log(`Retrying request (${attempt}/${max}) in ${delay}ms...`);
          },
          onError: (error) => {
            this.errorHandler.handleApiError(error, { url, method: fetchOptions.method });
          }
        });
      }

      try {
        return await doFetch();
      } catch (error) {
        this.errorHandler.handleApiError(error, { url, method: fetchOptions.method });
        throw error;
      }
    }

    getAuthToken() {
      // Try to get token from various sources
      return sessionStorage.getItem('access_token') 
          || localStorage.getItem('access_token')
          || this.getCookie('access_token');
    }

    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? match[2] : null;
    }

    // Convenience methods
    get(url, options = {}) {
      return this.fetch(url, { ...options, method: 'GET' });
    }

    post(url, data, options = {}) {
      return this.fetch(url, { 
        ...options, 
        method: 'POST',
        body: JSON.stringify(data)
      });
    }

    put(url, data, options = {}) {
      return this.fetch(url, { 
        ...options, 
        method: 'PUT',
        body: JSON.stringify(data)
      });
    }

    delete(url, options = {}) {
      return this.fetch(url, { ...options, method: 'DELETE' });
    }
  }

  // ============================================
  // OFFLINE HANDLER
  // ============================================
  
  class OfflineHandler {
    constructor() {
      this.isOnline = navigator.onLine;
      this.pendingRequests = [];
      this.setupListeners();
    }

    setupListeners() {
      window.addEventListener('online', () => {
        this.isOnline = true;
        this.showOnlineStatus();
        this.processPendingRequests();
      });

      window.addEventListener('offline', () => {
        this.isOnline = false;
        this.showOfflineStatus();
      });
    }

    showOfflineStatus() {
      let banner = document.getElementById('offline-banner');
      if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.className = 'offline-banner';
        banner.innerHTML = `
          <span class="offline-icon">📡</span>
          <span class="offline-message">You're offline. Some features may be unavailable.</span>
        `;
        document.body.prepend(banner);
      }
      banner.classList.add('show');
    }

    showOnlineStatus() {
      const banner = document.getElementById('offline-banner');
      if (banner) {
        banner.classList.remove('show');
        setTimeout(() => banner.remove(), 300);
      }
      
      // Show reconnected toast
      if (typeof showToast === 'function') {
        showToast('You\'re back online!', 'success', 2000);
      }
    }

    queueRequest(request) {
      this.pendingRequests.push(request);
      localStorage.setItem('pendingRequests', JSON.stringify(this.pendingRequests));
    }

    async processPendingRequests() {
      const pending = [...this.pendingRequests];
      this.pendingRequests = [];
      localStorage.removeItem('pendingRequests');

      for (const request of pending) {
        try {
          await fetch(request.url, request.options);
        } catch (e) {
          // Re-queue if still failing
          this.queueRequest(request);
        }
      }
    }
  }

  // ============================================
  // ERROR UI COMPONENTS
  // ============================================
  
  function createErrorUI() {
    // Add offline banner styles
    const style = document.createElement('style');
    style.textContent = `
      .offline-banner {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        font-size: 14px;
        font-weight: 600;
        z-index: 99999;
        transform: translateY(-100%);
        transition: transform 300ms ease;
      }
      
      .offline-banner.show {
        transform: translateY(0);
      }
      
      .error-boundary {
        padding: 40px;
        text-align: center;
        background: var(--ui-surface, #fff);
        border-radius: 16px;
        border: 1px solid var(--ui-border, #e5e7eb);
      }
      
      .error-boundary-icon {
        font-size: 48px;
        margin-bottom: 16px;
      }
      
      .error-boundary-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
        color: var(--ui-text, #1f2937);
      }
      
      .error-boundary-message {
        color: var(--ui-muted, #6b7280);
        margin-bottom: 20px;
      }
      
      .retry-button {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 24px;
        background: var(--ui-primary, #3b82f6);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        transition: all 200ms ease;
      }
      
      .retry-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      }
      
      .retry-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
      }
      
      .retry-button .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Create error boundary component
   */
  function createErrorBoundary(container, options = {}) {
    const {
      title = 'Something went wrong',
      message = 'We encountered an error loading this content.',
      retryFn = null,
      icon = '⚠️'
    } = options;

    const boundary = document.createElement('div');
    boundary.className = 'error-boundary';
    boundary.innerHTML = `
      <div class="error-boundary-icon">${icon}</div>
      <h3 class="error-boundary-title">${title}</h3>
      <p class="error-boundary-message">${message}</p>
      ${retryFn ? '<button class="retry-button">Try again</button>' : ''}
    `;

    if (retryFn) {
      const btn = boundary.querySelector('.retry-button');
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Retrying...';
        try {
          await retryFn();
          boundary.remove();
        } catch (e) {
          btn.disabled = false;
          btn.textContent = 'Try again';
        }
      });
    }

    container.innerHTML = '';
    container.appendChild(boundary);
    return boundary;
  }

  // ============================================
  // INITIALIZE
  // ============================================
  
  document.addEventListener('DOMContentLoaded', () => {
    createErrorUI();
    
    // Initialize offline handler
    window.offlineHandler = new OfflineHandler();
    
    // Load any pending requests from storage
    try {
      const pending = localStorage.getItem('pendingRequests');
      if (pending) {
        window.offlineHandler.pendingRequests = JSON.parse(pending);
      }
    } catch (e) {}
  });

  // Global error handler
  window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Global error:', { msg, url, lineNo, columnNo, error });
    return false;
  };

  // Unhandled promise rejection handler
  window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
  });

  // ============================================
  // EXPORTS
  // ============================================
  
  window.ErrorHandling = {
    ErrorHandler,
    ApiClient,
    OfflineHandler,
    createErrorBoundary
  };

  // Create default instances
  window.errorHandler = new ErrorHandler();
  window.apiClient = new ApiClient();

})();
