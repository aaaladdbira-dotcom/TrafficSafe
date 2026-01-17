/**
 * Toast Notification System
 * A beautiful, accessible toast notification system
 */

(function() {
  'use strict';

  // Create toast container if it doesn't exist
  function getContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('aria-atomic', 'true');
      document.body.appendChild(container);
    }
    return container;
  }

  // Icons for different toast types
  const icons = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
    error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
    warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
    info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
  };

  // Default titles for toast types
  const defaultTitles = {
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Information'
  };

  /**
   * Show a toast notification
   * @param {Object} options - Toast options
   * @param {string} options.type - Toast type: 'success', 'error', 'warning', 'info'
   * @param {string} options.title - Toast title (optional)
   * @param {string} options.message - Toast message
   * @param {number} options.duration - Duration in ms (default: 5000, 0 = no auto-dismiss)
   * @param {boolean} options.closable - Show close button (default: true)
   * @param {function} options.onClick - Click callback
   * @param {function} options.onClose - Close callback
   */
  function show(options) {
    const {
      type = 'info',
      title = defaultTitles[type] || 'Notification',
      message = '',
      duration = 5000,
      closable = true,
      onClick = null,
      onClose = null
    } = options;

    const container = getContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'alert');

    const closeIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || icons.info}</div>
      <div class="toast-content">
        <div class="toast-title">${escapeHtml(title)}</div>
        ${message ? `<div class="toast-message">${escapeHtml(message)}</div>` : ''}
      </div>
      ${closable ? `<button class="toast-close" aria-label="Close">${closeIcon}</button>` : ''}
      ${duration > 0 ? `<div class="toast-progress"><div class="toast-progress-bar" style="animation-duration: ${duration}ms;"></div></div>` : ''}
    `;

    // Click handler
    if (onClick) {
      toast.style.cursor = 'pointer';
      toast.addEventListener('click', (e) => {
        if (!e.target.closest('.toast-close')) {
          onClick();
        }
      });
    }

    // Close button handler
    if (closable) {
      const closeBtn = toast.querySelector('.toast-close');
      closeBtn.addEventListener('click', () => dismiss(toast, onClose));
    }

    // Add to container
    container.appendChild(toast);

    // Auto dismiss
    if (duration > 0) {
      setTimeout(() => dismiss(toast, onClose), duration);
    }

    return toast;
  }

  /**
   * Dismiss a toast
   */
  function dismiss(toast, callback) {
    if (!toast || toast.classList.contains('toast-exit')) return;

    toast.classList.add('toast-exit');
    setTimeout(() => {
      toast.remove();
      if (callback) callback();
    }, 300);
  }

  /**
   * Clear all toasts
   */
  function clearAll() {
    const container = document.getElementById('toast-container');
    if (container) {
      container.querySelectorAll('.toast').forEach(toast => dismiss(toast));
    }
  }

  /**
   * Escape HTML to prevent XSS
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Convenience methods
  const toast = {
    show,
    success: (message, title) => show({ type: 'success', message, title }),
    error: (message, title) => show({ type: 'error', message, title }),
    warning: (message, title) => show({ type: 'warning', message, title }),
    info: (message, title) => show({ type: 'info', message, title }),
    clearAll
  };

  // Expose globally
  window.Toast = toast;

  // Auto-convert flash messages on page load
  document.addEventListener('DOMContentLoaded', () => {
    // Convert Bootstrap alerts to toasts
    document.querySelectorAll('.alert[data-auto-toast="true"]').forEach(alert => {
      const type = alert.classList.contains('alert-success') ? 'success' :
                   alert.classList.contains('alert-danger') ? 'error' :
                   alert.classList.contains('alert-warning') ? 'warning' : 'info';
      const message = alert.textContent.trim();
      
      toast.show({ type, message });
      alert.remove();
    });
  });

})();
