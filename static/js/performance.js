/**
 * Performance Optimization Layer
 * - Request caching and deduplication
 * - Lazy loading utilities
 * - Debounce/throttle helpers
 * - Connection-aware loading
 */

(function() {
  'use strict';

  // ============================================
  // REQUEST CACHE & DEDUPLICATION
  // ============================================
  
  const RequestCache = {
    cache: new Map(),
    pending: new Map(),
    defaultTTL: 30000, // 30 seconds
    
    /**
     * Get cached response or make new request
     */
    async fetch(url, options = {}) {
      const cacheKey = this.getCacheKey(url, options);
      const ttl = options.cacheTTL || this.defaultTTL;
      
      // Check cache first
      const cached = this.cache.get(cacheKey);
      if (cached && Date.now() < cached.expires) {
        return cached.data;
      }
      
      // Check if request is already in flight (deduplication)
      if (this.pending.has(cacheKey)) {
        return this.pending.get(cacheKey);
      }
      
      // Make new request
      const promise = this.makeRequest(url, options)
        .then(data => {
          // Cache successful response
          this.cache.set(cacheKey, {
            data,
            expires: Date.now() + ttl
          });
          this.pending.delete(cacheKey);
          return data;
        })
        .catch(err => {
          this.pending.delete(cacheKey);
          throw err;
        });
      
      this.pending.set(cacheKey, promise);
      return promise;
    },
    
    getCacheKey(url, options) {
      return `${options.method || 'GET'}:${url}`;
    },
    
    async makeRequest(url, options) {
      const response = await fetch(url, {
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        body: options.body ? JSON.stringify(options.body) : undefined
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response.json();
    },
    
    /**
     * Invalidate cache entries
     */
    invalidate(pattern) {
      if (!pattern) {
        this.cache.clear();
        return;
      }
      
      for (const key of this.cache.keys()) {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      }
    },
    
    /**
     * Preload URLs
     */
    preload(urls) {
      urls.forEach(url => {
        this.fetch(url, { cacheTTL: 60000 }).catch(() => {});
      });
    }
  };

  // ============================================
  // DEBOUNCE & THROTTLE
  // ============================================
  
  function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        timeout = null;
        if (!immediate) func.apply(this, args);
      };
      const callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(this, args);
    };
  }

  function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // ============================================
  // INTERSECTION OBSERVER FOR LAZY LOADING
  // ============================================
  
  const LazyLoader = {
    observer: null,
    
    init() {
      if (!('IntersectionObserver' in window)) return;
      
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.loadElement(entry.target);
            this.observer.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: '50px',
        threshold: 0.01
      });
    },
    
    observe(element) {
      if (this.observer) {
        this.observer.observe(element);
      } else {
        // Fallback: load immediately
        this.loadElement(element);
      }
    },
    
    loadElement(element) {
      // Handle lazy images
      if (element.dataset.src) {
        element.src = element.dataset.src;
        element.removeAttribute('data-src');
      }
      
      // Handle lazy backgrounds
      if (element.dataset.bg) {
        element.style.backgroundImage = `url(${element.dataset.bg})`;
        element.removeAttribute('data-bg');
      }
      
      // Trigger custom load event
      element.dispatchEvent(new CustomEvent('lazyload'));
      element.classList.add('loaded');
    }
  };

  // ============================================
  // CONNECTION-AWARE LOADING
  // ============================================
  
  const ConnectionAware = {
    getConnectionQuality() {
      const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      
      if (!connection) return 'unknown';
      
      const effectiveType = connection.effectiveType;
      if (effectiveType === '4g') return 'high';
      if (effectiveType === '3g') return 'medium';
      return 'low';
    },
    
    shouldLoadHighRes() {
      const quality = this.getConnectionQuality();
      return quality === 'high' || quality === 'unknown';
    },
    
    shouldPreload() {
      const quality = this.getConnectionQuality();
      const saveData = navigator.connection?.saveData;
      return !saveData && (quality === 'high' || quality === 'unknown');
    }
  };

  // ============================================
  // PERFORMANCE MONITORING
  // ============================================
  
  const PerfMonitor = {
    marks: new Map(),
    
    mark(name) {
      this.marks.set(name, performance.now());
    },
    
    measure(name, startMark) {
      const start = this.marks.get(startMark);
      if (!start) return null;
      
      const duration = performance.now() - start;
      console.debug(`[Perf] ${name}: ${duration.toFixed(2)}ms`);
      return duration;
    },
    
    reportVitals() {
      if (!window.PerformanceObserver) return;
      
      // Largest Contentful Paint
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lcp = entries[entries.length - 1];
        console.debug(`[Perf] LCP: ${lcp.startTime.toFixed(2)}ms`);
      }).observe({ entryTypes: ['largest-contentful-paint'] });
      
      // First Input Delay
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.debug(`[Perf] FID: ${entry.processingStart - entry.startTime}ms`);
        }
      }).observe({ entryTypes: ['first-input'] });
      
      // Cumulative Layout Shift
      let clsValue = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        }
        console.debug(`[Perf] CLS: ${clsValue.toFixed(4)}`);
      }).observe({ entryTypes: ['layout-shift'] });
    }
  };

  // ============================================
  // ANIMATED NUMBER COUNTER
  // ============================================
  
  function animateValue(element, start, end, duration = 1000) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      element.textContent = formatNumber(end);
      return;
    }
    
    const range = end - start;
    const startTime = performance.now();
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out-quart)
      const eased = 1 - Math.pow(1 - progress, 4);
      const current = Math.floor(start + range * eased);
      
      element.textContent = formatNumber(current);
      element.classList.add('counting');
      
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = formatNumber(end);
        element.classList.remove('counting');
      }
    }
    
    requestAnimationFrame(update);
  }
  
  function formatNumber(num) {
    return num.toLocaleString();
  }

  // ============================================
  // VIRTUAL SCROLL HELPER
  // ============================================
  
  class VirtualScroller {
    constructor(container, options = {}) {
      this.container = container;
      this.itemHeight = options.itemHeight || 50;
      this.buffer = options.buffer || 5;
      this.items = [];
      this.renderItem = options.renderItem || (() => '');
      
      this.container.style.overflow = 'auto';
      this.container.style.position = 'relative';
      
      this.content = document.createElement('div');
      this.content.style.position = 'relative';
      this.container.appendChild(this.content);
      
      this.container.addEventListener('scroll', throttle(() => this.render(), 16));
    }
    
    setItems(items) {
      this.items = items;
      this.content.style.height = `${items.length * this.itemHeight}px`;
      this.render();
    }
    
    render() {
      const scrollTop = this.container.scrollTop;
      const viewportHeight = this.container.clientHeight;
      
      const startIndex = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.buffer);
      const endIndex = Math.min(
        this.items.length,
        Math.ceil((scrollTop + viewportHeight) / this.itemHeight) + this.buffer
      );
      
      const fragment = document.createDocumentFragment();
      
      for (let i = startIndex; i < endIndex; i++) {
        const item = this.items[i];
        const el = this.renderItem(item, i);
        el.style.position = 'absolute';
        el.style.top = `${i * this.itemHeight}px`;
        el.style.left = '0';
        el.style.right = '0';
        el.style.height = `${this.itemHeight}px`;
        fragment.appendChild(el);
      }
      
      this.content.innerHTML = '';
      this.content.appendChild(fragment);
    }
  }

  // ============================================
  // RESOURCE HINTS
  // ============================================
  
  function preconnect(url) {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = url;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  }
  
  function prefetch(url) {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
  }

  // ============================================
  // INITIALIZE
  // ============================================
  
  document.addEventListener('DOMContentLoaded', () => {
    LazyLoader.init();
    
    // Add preconnects for common resources
    preconnect('https://cdn.jsdelivr.net');
    preconnect('https://fonts.googleapis.com');
    
    // Initialize lazy loading for elements
    document.querySelectorAll('[data-lazy]').forEach(el => {
      LazyLoader.observe(el);
    });
    
    // Auto-animate counters
    document.querySelectorAll('[data-count-to]').forEach(el => {
      const endValue = parseInt(el.dataset.countTo, 10);
      const startValue = parseInt(el.dataset.countFrom || '0', 10);
      const duration = parseInt(el.dataset.countDuration || '1000', 10);
      
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          animateValue(el, startValue, endValue, duration);
          observer.disconnect();
        }
      });
      
      observer.observe(el);
    });
    
    // Debug mode performance reporting
    if (localStorage.getItem('debug') === 'true') {
      PerfMonitor.reportVitals();
    }
  });

  // ============================================
  // EXPORTS
  // ============================================
  
  window.Performance = {
    Cache: RequestCache,
    LazyLoader,
    ConnectionAware,
    Monitor: PerfMonitor,
    debounce,
    throttle,
    animateValue,
    VirtualScroller,
    preconnect,
    prefetch
  };

})();
