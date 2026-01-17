/**
 * Confirmation Dialogs
 * Beautiful confirmation modals for destructive actions
 */

(function() {
  'use strict';

  /**
   * Show a confirmation dialog
   * @param {Object} options
   * @param {string} options.title - Dialog title
   * @param {string} options.message - Dialog message
   * @param {string} options.confirmText - Confirm button text (default: 'Confirm')
   * @param {string} options.cancelText - Cancel button text (default: 'Cancel')
   * @param {string} options.type - Dialog type: 'danger', 'warning', 'info' (default: 'danger')
   * @param {function} options.onConfirm - Callback when confirmed
   * @param {function} options.onCancel - Callback when cancelled
   * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
   */
  function confirm(options) {
    return new Promise((resolve) => {
      const {
        title = 'Confirm Action',
        message = 'Are you sure you want to proceed?',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        type = 'danger',
        onConfirm = null,
        onCancel = null
      } = options;

      const icons = {
        danger: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
        warning: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
        info: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
      };

      const colors = {
        danger: { bg: '#FEE2E2', color: '#DC2626', btnBg: '#EF4444' },
        warning: { bg: '#FEF3C7', color: '#D97706', btnBg: '#F59E0B' },
        info: { bg: '#DBEAFE', color: '#2563EB', btnBg: '#3B82F6' }
      };

      const colorSet = colors[type] || colors.danger;

      // Create modal
      const modal = document.createElement('div');
      modal.className = 'confirm-modal-overlay';
      modal.innerHTML = `
        <div class="confirm-modal-backdrop"></div>
        <div class="confirm-modal">
          <div class="confirm-modal-icon" style="background: ${colorSet.bg}; color: ${colorSet.color};">
            ${icons[type] || icons.danger}
          </div>
          <h3 class="confirm-modal-title">${escapeHtml(title)}</h3>
          <p class="confirm-modal-message">${escapeHtml(message)}</p>
          <div class="confirm-modal-buttons">
            <button class="confirm-modal-btn confirm-modal-btn-cancel">${escapeHtml(cancelText)}</button>
            <button class="confirm-modal-btn confirm-modal-btn-confirm" style="background: ${colorSet.btnBg};">${escapeHtml(confirmText)}</button>
          </div>
        </div>
      `;

      document.body.appendChild(modal);

      // Focus trap
      const confirmBtn = modal.querySelector('.confirm-modal-btn-confirm');
      const cancelBtn = modal.querySelector('.confirm-modal-btn-cancel');
      confirmBtn.focus();

      function close(confirmed) {
        modal.classList.add('confirm-modal-exit');
        setTimeout(() => {
          modal.remove();
          if (confirmed) {
            if (onConfirm) onConfirm();
            resolve(true);
          } else {
            if (onCancel) onCancel();
            resolve(false);
          }
        }, 200);
      }

      // Event handlers
      cancelBtn.addEventListener('click', () => close(false));
      confirmBtn.addEventListener('click', () => close(true));
      modal.querySelector('.confirm-modal-backdrop').addEventListener('click', () => close(false));

      // Keyboard
      modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') close(false);
        if (e.key === 'Enter') close(true);
      });
    });
  }

  /**
   * Convenience method for delete confirmation
   */
  function confirmDelete(itemName = 'this item') {
    return confirm({
      title: 'Delete Confirmation',
      message: `Are you sure you want to delete ${itemName}? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Keep',
      type: 'danger'
    });
  }

  /**
   * Escape HTML
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Expose globally
  window.ConfirmDialog = {
    confirm,
    confirmDelete
  };

})();
