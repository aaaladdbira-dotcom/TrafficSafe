/**
 * UI Enhancements for Traffic Accident System
 * - Toast notifications
 * - Sparklines
 * - Keyboard shortcuts
 * - Loading states
 */

(function() {
  'use strict';

  // ============================================
  // 1. TOAST NOTIFICATION SYSTEM
  // ============================================
  const ToastManager = {
    container: null,
    queue: [],
    
    init() {
      if (this.container) return;
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.setAttribute('aria-live', 'polite');
      document.body.appendChild(this.container);
    },
    
    show(message, type = 'info', duration = 4000) {
      this.init();
      
      const toast = document.createElement('div');
      toast.className = `toast-notification toast-${type}`;
      
      const icons = {
        success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
      };
      
      toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" aria-label="Close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      `;
      
      const closeBtn = toast.querySelector('.toast-close');
      closeBtn.addEventListener('click', () => this.dismiss(toast));
      
      this.container.appendChild(toast);
      
      // Trigger animation
      requestAnimationFrame(() => {
        toast.classList.add('toast-visible');
      });
      
      // Auto dismiss
      if (duration > 0) {
        setTimeout(() => this.dismiss(toast), duration);
      }
      
      return toast;
    },
    
    dismiss(toast) {
      if (!toast || !toast.parentNode) return;
      toast.classList.remove('toast-visible');
      toast.classList.add('toast-hiding');
      setTimeout(() => toast.remove(), 300);
    },
    
    success(message, duration) { return this.show(message, 'success', duration); },
    error(message, duration) { return this.show(message, 'error', duration); },
    warning(message, duration) { return this.show(message, 'warning', duration); },
    info(message, duration) { return this.show(message, 'info', duration); }
  };
  
  // Expose globally
  window.Toast = ToastManager;

  // ============================================
  // 2. SPARKLINE CHARTS
  // ============================================
  class Sparkline {
    constructor(container, data, options = {}) {
      this.container = typeof container === 'string' ? document.querySelector(container) : container;
      if (!this.container) return;
      
      this.data = data || [];
      this.options = {
        width: options.width || this.container.offsetWidth || 80,
        height: options.height || 30,
        strokeColor: options.strokeColor || '#3b82f6',
        fillColor: options.fillColor || 'rgba(59, 130, 246, 0.1)',
        strokeWidth: options.strokeWidth || 1.5,
        showDots: options.showDots !== false,
        animated: options.animated !== false,
        ...options
      };
      
      this.render();
    }
    
    render() {
      if (!this.data.length) return;
      
      const { width, height, strokeColor, fillColor, strokeWidth, showDots, animated } = this.options;
      const max = Math.max(...this.data);
      const min = Math.min(...this.data);
      const range = max - min || 1;
      
      const points = this.data.map((val, i) => {
        const x = (i / (this.data.length - 1)) * width;
        const y = height - ((val - min) / range) * (height - 4) - 2;
        return { x, y, val };
      });
      
      const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
      const areaD = pathD + ` L ${width} ${height} L 0 ${height} Z`;
      
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('width', width);
      svg.setAttribute('height', height);
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.classList.add('sparkline-svg');
      
      // Area fill
      const area = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      area.setAttribute('d', areaD);
      area.setAttribute('fill', fillColor);
      area.classList.add('sparkline-area');
      svg.appendChild(area);
      
      // Line
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', pathD);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', strokeColor);
      path.setAttribute('stroke-width', strokeWidth);
      path.setAttribute('stroke-linecap', 'round');
      path.setAttribute('stroke-linejoin', 'round');
      path.classList.add('sparkline-line');
      
      if (animated) {
        const length = path.getTotalLength ? path.getTotalLength() : width * 2;
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;
      }
      
      svg.appendChild(path);
      
      // End dot
      if (showDots && points.length > 0) {
        const lastPoint = points[points.length - 1];
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('cx', lastPoint.x);
        dot.setAttribute('cy', lastPoint.y);
        dot.setAttribute('r', 3);
        dot.setAttribute('fill', strokeColor);
        dot.classList.add('sparkline-dot');
        svg.appendChild(dot);
      }
      
      this.container.innerHTML = '';
      this.container.appendChild(svg);
      
      // Trigger animation
      if (animated) {
        requestAnimationFrame(() => {
          path.style.transition = 'stroke-dashoffset 1s ease-out';
          path.style.strokeDashoffset = '0';
        });
      }
    }
    
    update(newData) {
      this.data = newData;
      this.render();
    }
  }
  
  window.Sparkline = Sparkline;

  // ============================================
  // 3. KEYBOARD SHORTCUTS
  // ============================================
  const KeyboardShortcuts = {
    shortcuts: {},
    enabled: true,
    helpVisible: false,
    
    init() {
      document.addEventListener('keydown', (e) => this.handleKeydown(e));
      this.registerDefaults();
      this.createHelpModal();
    },
    
    registerDefaults() {
      // Global shortcuts
      this.register('?', 'Show keyboard shortcuts', () => this.toggleHelp(), { shift: true });
      this.register('/', 'Focus search', () => this.focusSearch());
      this.register('g h', 'Go to Dashboard', () => this.navigate('/ui/dashboard'));
      this.register('g a', 'Go to Accidents', () => this.navigate('/ui/accidents'));
      this.register('g s', 'Go to Statistics', () => this.navigate('/ui/statistics'));
      this.register('g r', 'Go to Reports', () => this.navigate('/ui/my-reports'));
      this.register('n', 'New accident report', () => this.navigate('/ui/report-accident'));
      this.register('Escape', 'Close modal/panel', () => this.closeModal());
    },
    
    register(keys, description, callback, options = {}) {
      this.shortcuts[keys] = { keys, description, callback, options };
    },
    
    handleKeydown(e) {
      if (!this.enabled) return;
      
      // Ignore when typing in inputs
      const tag = e.target.tagName.toLowerCase();
      const isEditable = e.target.isContentEditable;
      if (['input', 'textarea', 'select'].includes(tag) || isEditable) {
        if (e.key === 'Escape') {
          e.target.blur();
        }
        return;
      }
      
      const key = e.key;
      const shortcut = Object.values(this.shortcuts).find(s => {
        if (s.options.shift && !e.shiftKey) return false;
        if (s.options.ctrl && !e.ctrlKey) return false;
        if (s.options.alt && !e.altKey) return false;
        return s.keys === key || s.keys === e.code;
      });
      
      if (shortcut) {
        e.preventDefault();
        shortcut.callback();
      }
    },
    
    focusSearch() {
      const search = document.querySelector('input[type="search"], input[name="search"], #search, .search-input');
      if (search) {
        search.focus();
        search.select();
      }
    },
    
    navigate(url) {
      window.location.href = url;
    },
    
    closeModal() {
      // Close Bootstrap modals
      const modal = document.querySelector('.modal.show');
      if (modal) {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) bsModal.hide();
        return;
      }
      // Close help
      if (this.helpVisible) {
        this.toggleHelp();
      }
    },
    
    createHelpModal() {
      const modal = document.createElement('div');
      modal.className = 'keyboard-help-modal';
      modal.innerHTML = `
        <div class="keyboard-help-content">
          <div class="keyboard-help-header">
            <h3>Keyboard Shortcuts</h3>
            <button class="keyboard-help-close" aria-label="Close">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          <div class="keyboard-help-body">
            <div class="shortcut-group">
              <h4>Navigation</h4>
              <div class="shortcut-item"><kbd>g</kbd> <kbd>h</kbd> <span>Dashboard</span></div>
              <div class="shortcut-item"><kbd>g</kbd> <kbd>a</kbd> <span>Accidents</span></div>
              <div class="shortcut-item"><kbd>g</kbd> <kbd>s</kbd> <span>Statistics</span></div>
              <div class="shortcut-item"><kbd>g</kbd> <kbd>r</kbd> <span>My Reports</span></div>
            </div>
            <div class="shortcut-group">
              <h4>Actions</h4>
              <div class="shortcut-item"><kbd>n</kbd> <span>New report</span></div>
              <div class="shortcut-item"><kbd>/</kbd> <span>Focus search</span></div>
              <div class="shortcut-item"><kbd>Esc</kbd> <span>Close modal</span></div>
            </div>
            <div class="shortcut-group">
              <h4>Help</h4>
              <div class="shortcut-item"><kbd>Shift</kbd> <kbd>?</kbd> <span>Show this help</span></div>
            </div>
          </div>
        </div>
      `;
      
      modal.querySelector('.keyboard-help-close').addEventListener('click', () => this.toggleHelp());
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.toggleHelp();
      });
      
      document.body.appendChild(modal);
      this.helpModal = modal;
    },
    
    toggleHelp() {
      this.helpVisible = !this.helpVisible;
      if (this.helpModal) {
        this.helpModal.classList.toggle('visible', this.helpVisible);
      }
    }
  };

  // ============================================
  // 4. FLOATING ACTION BUTTON (FAB)
  // ============================================
  const FAB = {
    container: null,
    isOpen: false,
    
    init() {
      // Only show on certain pages for logged-in users
      if (!document.querySelector('.navbar')) return;
      
      this.container = document.createElement('div');
      this.container.className = 'fab-container';
      this.container.innerHTML = `
        <div class="fab-actions">
          <a href="/ui/report-accident" class="fab-action" data-tooltip="Report Accident">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
          </a>
          <a href="/ui/accidents" class="fab-action" data-tooltip="View Accidents">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </a>
          <a href="/ui/statistics" class="fab-action" data-tooltip="Statistics">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
          </a>
        </div>
        <button class="fab-main" aria-label="Quick actions">
          <svg class="fab-icon-open" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          <svg class="fab-icon-close" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      `;
      
      document.body.appendChild(this.container);
      
      const mainBtn = this.container.querySelector('.fab-main');
      mainBtn.addEventListener('click', () => this.toggle());
      
      // Close when clicking outside
      document.addEventListener('click', (e) => {
        if (this.isOpen && !this.container.contains(e.target)) {
          this.close();
        }
      });
    },
    
    toggle() {
      this.isOpen = !this.isOpen;
      this.container.classList.toggle('fab-open', this.isOpen);
    },
    
    close() {
      this.isOpen = false;
      this.container.classList.remove('fab-open');
    }
  };

  // ============================================
  // 5. SKELETON LOADERS
  // ============================================
  const SkeletonLoader = {
    create(type = 'text', options = {}) {
      const el = document.createElement('div');
      el.className = 'skeleton-loader';
      
      switch(type) {
        case 'text':
          el.classList.add('skeleton-text');
          el.style.width = options.width || '100%';
          el.style.height = options.height || '1em';
          break;
        case 'avatar':
          el.classList.add('skeleton-avatar');
          el.style.width = options.size || '40px';
          el.style.height = options.size || '40px';
          break;
        case 'card':
          el.classList.add('skeleton-card');
          el.innerHTML = `
            <div class="skeleton-header"></div>
            <div class="skeleton-body">
              <div class="skeleton-line" style="width: 80%"></div>
              <div class="skeleton-line" style="width: 60%"></div>
              <div class="skeleton-line" style="width: 70%"></div>
            </div>
          `;
          break;
        case 'table-row':
          el.classList.add('skeleton-table-row');
          const cols = options.columns || 4;
          for (let i = 0; i < cols; i++) {
            const cell = document.createElement('div');
            cell.className = 'skeleton-cell';
            cell.style.width = `${100/cols}%`;
            el.appendChild(cell);
          }
          break;
        case 'chart':
          el.classList.add('skeleton-chart');
          el.style.height = options.height || '200px';
          break;
      }
      
      return el;
    },
    
    wrap(container, type = 'text', options = {}) {
      const skeleton = this.create(type, options);
      container.innerHTML = '';
      container.appendChild(skeleton);
      return skeleton;
    },
    
    remove(skeleton) {
      if (skeleton && skeleton.parentNode) {
        skeleton.classList.add('skeleton-fade-out');
        setTimeout(() => skeleton.remove(), 300);
      }
    }
  };
  
  window.SkeletonLoader = SkeletonLoader;

  // ============================================
  // 6. ENHANCED TABLE ROWS
  // ============================================
  function enhanceTables() {
    document.querySelectorAll('table tbody tr').forEach((row, i) => {
      if (!row.classList.contains('table-row-enhanced')) {
        row.classList.add('table-row-enhanced');
        row.style.setProperty('--row-index', i);
      }
    });
  }

  // ============================================
  // 7. MICRO-INTERACTIONS
  // ============================================
  function addMicroInteractions() {
    // Card hover lift effect
    document.querySelectorAll('.card:not(.no-hover)').forEach(card => {
      if (!card.dataset.microInit) {
        card.dataset.microInit = 'true';
        card.classList.add('card-interactive');
      }
    });
    
    // Button ripple effect
    document.querySelectorAll('.btn:not(.no-ripple)').forEach(btn => {
      if (!btn.dataset.rippleInit) {
        btn.dataset.rippleInit = 'true';
        btn.addEventListener('click', createRipple);
      }
    });
  }
  
  function createRipple(e) {
    const btn = e.currentTarget;
    const ripple = document.createElement('span');
    ripple.className = 'btn-ripple';
    
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  }

  // ============================================
  // 8. INITIALIZE ON DOM READY
  // ============================================
  function init() {
    KeyboardShortcuts.init();
    FAB.init();
    enhanceTables();
    addMicroInteractions();
    
    // Re-run on dynamic content
    const observer = new MutationObserver(() => {
      enhanceTables();
      addMicroInteractions();
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Intercept alerts and convert to toasts
  const originalAlert = window.alert;
  window.alert = function(message) {
    Toast.info(message);
  };

})();
