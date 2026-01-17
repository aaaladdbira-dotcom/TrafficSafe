/**
 * Keyboard Shortcuts System
 * Global keyboard shortcuts for quick navigation
 */

(function() {
  'use strict';

  const shortcuts = new Map();
  let sequenceBuffer = '';
  let sequenceTimeout = null;

  // Default shortcuts
  const defaultShortcuts = [
    // Navigation (g + key sequences)
    { keys: 'g h', description: 'Go to Dashboard', action: () => navigate('/ui/dashboard') },
    { keys: 'g a', description: 'Go to Accidents', action: () => navigate('/ui/accidents') },
    { keys: 'g s', description: 'Go to Statistics', action: () => navigate('/ui/statistics') },
    { keys: 'g r', description: 'Go to Reports', action: () => navigate('/ui/gov-reports') },
    { keys: 'g u', description: 'Go to Users', action: () => navigate('/ui/users') },
    { keys: 'g i', description: 'Go to Import', action: () => navigate('/ui/import/csv') },
    { keys: 'g p', description: 'Go to Profile', action: () => navigate('/ui/account') },
    
    // Actions
    { keys: 'n', description: 'New Report', action: () => navigate('/ui/report') },
    { keys: '/', description: 'Search', action: openSearch, allowInInput: false },
    { keys: '?', description: 'Show Shortcuts', action: showShortcutsModal },
    
    // UI Toggles
    { keys: 'Escape', description: 'Close Modal', action: closeAllModals },
  ];

  function navigate(url) {
    window.location.href = url;
  }

  function openSearch() {
    if (window.openGlobalSearch) {
      window.openGlobalSearch();
    }
  }

  function closeAllModals() {
    // Close Bootstrap modals
    document.querySelectorAll('.modal.show').forEach(modal => {
      const bsModal = bootstrap?.Modal?.getInstance(modal);
      if (bsModal) bsModal.hide();
    });
    
    // Close global search
    if (window.closeGlobalSearch) {
      window.closeGlobalSearch();
    }

    // Close shortcuts modal
    const shortcutsModal = document.getElementById('shortcutsModal');
    if (shortcutsModal) shortcutsModal.remove();
  }

  function showShortcutsModal() {
    // Remove existing modal
    const existing = document.getElementById('shortcutsModal');
    if (existing) {
      existing.remove();
      return;
    }

    const modal = document.createElement('div');
    modal.id = 'shortcutsModal';
    modal.className = 'shortcuts-modal-overlay';
    modal.innerHTML = `
      <div class="shortcuts-modal-backdrop"></div>
      <div class="shortcuts-modal">
        <div class="shortcuts-modal-header">
          <h3>Keyboard Shortcuts</h3>
          <button class="shortcuts-modal-close" aria-label="Close">&times;</button>
        </div>
        <div class="shortcuts-modal-body">
          <div class="shortcuts-section">
            <h4>Navigation</h4>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>H</kbd> <span>Dashboard</span></div>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>A</kbd> <span>Accidents</span></div>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>S</kbd> <span>Statistics</span></div>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>R</kbd> <span>Reports</span></div>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>U</kbd> <span>Users</span></div>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>I</kbd> <span>Import</span></div>
            <div class="shortcut-item"><kbd>G</kbd> <kbd>P</kbd> <span>Profile</span></div>
          </div>
          <div class="shortcuts-section">
            <h4>Actions</h4>
            <div class="shortcut-item"><kbd>N</kbd> <span>New Report</span></div>
            <div class="shortcut-item"><kbd>/</kbd> or <kbd>Ctrl</kbd> <kbd>K</kbd> <span>Search</span></div>
            <div class="shortcut-item"><kbd>?</kbd> <span>Show Shortcuts</span></div>
            <div class="shortcut-item"><kbd>Esc</kbd> <span>Close Modal</span></div>
          </div>
        </div>
        <div class="shortcuts-modal-footer">
          Press <kbd>?</kbd> to toggle this menu
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Close handlers
    modal.querySelector('.shortcuts-modal-backdrop').addEventListener('click', () => modal.remove());
    modal.querySelector('.shortcuts-modal-close').addEventListener('click', () => modal.remove());
  }

  function isInputFocused() {
    const active = document.activeElement;
    return active && (
      active.tagName === 'INPUT' ||
      active.tagName === 'TEXTAREA' ||
      active.tagName === 'SELECT' ||
      active.isContentEditable
    );
  }

  function handleKeyDown(e) {
    // Skip if modifier keys (except for Ctrl+K)
    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'k') {
        e.preventDefault();
        openSearch();
      }
      return;
    }

    if (e.altKey) return;

    // Skip if in input (unless allowInInput)
    if (isInputFocused() && e.key !== 'Escape') return;

    const key = e.key.toLowerCase();

    // Handle sequence shortcuts
    clearTimeout(sequenceTimeout);
    sequenceBuffer += key + ' ';
    
    sequenceTimeout = setTimeout(() => {
      sequenceBuffer = '';
    }, 800);

    // Check for matching shortcut
    for (const shortcut of defaultShortcuts) {
      const normalizedKeys = shortcut.keys.toLowerCase() + ' ';
      
      if (sequenceBuffer === normalizedKeys) {
        e.preventDefault();
        shortcut.action();
        sequenceBuffer = '';
        return;
      }
      
      // Single key shortcuts
      if (shortcut.keys.length === 1 && key === shortcut.keys.toLowerCase()) {
        if (shortcut.allowInInput === false && isInputFocused()) continue;
        e.preventDefault();
        shortcut.action();
        sequenceBuffer = '';
        return;
      }
    }
  }

  // Initialize
  document.addEventListener('keydown', handleKeyDown);

  // Expose API
  window.KeyboardShortcuts = {
    show: showShortcutsModal,
    register: (keys, action, description) => {
      defaultShortcuts.push({ keys, action, description });
    }
  };

})();
