/**
 * Global Search (Command Palette)
 * Spotlight-style search for accidents, users, and navigation
 */

(function() {
  'use strict';

  let searchModal = null;
  let searchInput = null;
  let searchResults = null;
  let selectedIndex = -1;
  let searchTimeout = null;
  let currentResults = [];

  // Quick navigation pages
  const quickPages = [
    { title: 'Dashboard', url: '/ui/dashboard', icon: 'home', keywords: ['home', 'main', 'overview'] },
    { title: 'Browse Accidents', url: '/ui/accidents', icon: 'list', keywords: ['list', 'view', 'all'] },
    { title: 'Report Accident', url: '/ui/report-accident', icon: 'plus', keywords: ['new', 'create', 'add', 'submit'] },
    { title: 'My Reports', url: '/ui/my-reports', icon: 'file-text', keywords: ['submitted', 'my'] },
    { title: 'Statistics', url: '/ui/statistics', icon: 'bar-chart', keywords: ['stats', 'charts', 'analytics', 'graphs'] },
    { title: 'Import CSV', url: '/ui/import', icon: 'upload', keywords: ['upload', 'batch', 'data'] },
    { title: 'Users Management', url: '/ui/users', icon: 'users', keywords: ['accounts', 'manage'] },
    { title: 'Account Settings', url: '/ui/account-settings', icon: 'settings', keywords: ['preferences', 'profile'] },
  ];

  // Initialize
  function init() {
    createSearchModal();
    createSearchTrigger();
    bindKeyboardShortcuts();
  }

  // Create search modal HTML
  function createSearchModal() {
    searchModal = document.createElement('div');
    searchModal.className = 'search-modal';
    searchModal.innerHTML = `
      <div class="search-modal-backdrop"></div>
      <div class="search-container">
        <div class="search-input-wrapper">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" class="search-input" placeholder="Search accidents, users, or pages..." autocomplete="off">
          <div class="search-spinner"></div>
        </div>
        <div class="search-results"></div>
        <div class="search-quick-actions">
          <button class="quick-action" data-url="/ui/dashboard">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
            Dashboard
          </button>
          <button class="quick-action" data-url="/ui/accidents">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            Accidents
          </button>
          <button class="quick-action" data-url="/ui/statistics">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
            Statistics
          </button>
          <button class="quick-action" data-url="/ui/report-accident">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            New Report
          </button>
        </div>
        <div class="search-footer">
          <div class="search-footer-shortcuts">
            <span class="search-footer-shortcut"><kbd>↑↓</kbd> Navigate</span>
            <span class="search-footer-shortcut"><kbd>Enter</kbd> Select</span>
            <span class="search-footer-shortcut"><kbd>Esc</kbd> Close</span>
          </div>
          <span>Ctrl+K to search</span>
        </div>
      </div>
    `;

    document.body.appendChild(searchModal);

    // Get references
    searchInput = searchModal.querySelector('.search-input');
    searchResults = searchModal.querySelector('.search-results');

    // Bind events
    searchModal.querySelector('.search-modal-backdrop').addEventListener('click', closeSearch);
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keydown', handleSearchKeydown);

    // Quick action buttons
    searchModal.querySelectorAll('.quick-action').forEach(btn => {
      btn.addEventListener('click', () => {
        window.location.href = btn.dataset.url;
      });
    });
  }

  // Create search trigger in navbar
  function createSearchTrigger() {
    const topnavRight = document.querySelector('.topnav__right');
    if (!topnavRight) return;

    const trigger = document.createElement('button');
    trigger.className = 'search-trigger';
    trigger.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <span>Search</span>
      <kbd>Ctrl+K</kbd>
    `;
    trigger.addEventListener('click', openSearch);

    topnavRight.insertBefore(trigger, topnavRight.firstChild);
  }

  // Keyboard shortcuts
  function bindKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl+K or Cmd+K to open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openSearch();
      }

      // Escape to close
      if (e.key === 'Escape' && searchModal.classList.contains('active')) {
        closeSearch();
      }
    });
  }

  // Open search modal
  function openSearch() {
    searchModal.classList.add('active');
    searchInput.value = '';
    searchResults.innerHTML = '';
    searchResults.classList.remove('has-query');
    selectedIndex = -1;
    currentResults = [];
    setTimeout(() => searchInput.focus(), 100);
  }

  // Close search modal
  function closeSearch() {
    searchModal.classList.remove('active');
    searchInput.blur();
  }

  // Handle search input
  function handleSearchInput(e) {
    const query = e.target.value.trim();
    
    if (searchTimeout) clearTimeout(searchTimeout);

    if (query.length === 0) {
      searchResults.innerHTML = '';
      searchResults.classList.remove('has-query');
      currentResults = [];
      selectedIndex = -1;
      return;
    }

    searchResults.classList.add('has-query');

    // Show loading
    searchModal.querySelector('.search-input-wrapper').classList.add('loading');

    // Debounce search
    searchTimeout = setTimeout(() => {
      performSearch(query);
    }, 200);
  }

  // Perform search
  async function performSearch(query) {
    currentResults = [];
    selectedIndex = -1;

    try {
      // Search pages first (instant)
      const pageResults = searchPages(query);
      
      // Search API
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();

      // Build results
      let html = '';

      // Pages
      if (pageResults.length > 0) {
        html += `<div class="search-group">
          <div class="search-group-title">Pages</div>
          ${pageResults.map((p, i) => `
            <div class="search-result" data-index="${currentResults.length + i}" data-url="${p.url}">
              <div class="search-result-icon page">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              </div>
              <div class="search-result-content">
                <div class="search-result-title">${highlightMatch(p.title, query)}</div>
                <div class="search-result-subtitle">${p.url}</div>
              </div>
            </div>
          `).join('')}
        </div>`;
        currentResults.push(...pageResults.map(p => ({ type: 'page', ...p })));
      }

      // Accidents
      if (data.accidents && data.accidents.length > 0) {
        html += `<div class="search-group">
          <div class="search-group-title">Accidents</div>
          ${data.accidents.slice(0, 5).map((a, i) => `
            <div class="search-result" data-index="${currentResults.length + i}" data-url="/ui/accidents/${a.id}">
              <div class="search-result-icon accident">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path></svg>
              </div>
              <div class="search-result-content">
                <div class="search-result-title">${highlightMatch(a.location || a.governorate || 'Unknown location', query)}</div>
                <div class="search-result-subtitle">${a.governorate || ''} ${a.delegation ? '• ' + a.delegation : ''} ${a.occurred_at ? '• ' + formatDate(a.occurred_at) : ''}</div>
              </div>
              ${a.severity ? `<span class="search-result-badge ${a.severity.toLowerCase()}">${a.severity}</span>` : ''}
            </div>
          `).join('')}
        </div>`;
        currentResults.push(...data.accidents.slice(0, 5).map(a => ({ type: 'accident', url: `/ui/accidents/${a.id}`, ...a })));
      }

      // Users
      if (data.users && data.users.length > 0) {
        html += `<div class="search-group">
          <div class="search-group-title">Users</div>
          ${data.users.slice(0, 5).map((u, i) => `
            <div class="search-result" data-index="${currentResults.length + i}" data-url="/ui/users/${u.id}">
              <div class="search-result-icon user">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              </div>
              <div class="search-result-content">
                <div class="search-result-title">${highlightMatch(u.full_name || u.email, query)}</div>
                <div class="search-result-subtitle">${u.email} • ${u.role || 'user'}</div>
              </div>
            </div>
          `).join('')}
        </div>`;
        currentResults.push(...data.users.slice(0, 5).map(u => ({ type: 'user', url: `/ui/users/${u.id}`, ...u })));
      }

      searchResults.innerHTML = html || '';

      // Bind click events
      searchResults.querySelectorAll('.search-result').forEach(el => {
        el.addEventListener('click', () => {
          window.location.href = el.dataset.url;
        });
      });

    } catch (error) {
      console.error('Search error:', error);
      searchResults.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--ui-muted);">Search unavailable</div>';
    }

    searchModal.querySelector('.search-input-wrapper').classList.remove('loading');
  }

  // Search pages locally
  function searchPages(query) {
    const q = query.toLowerCase();
    return quickPages.filter(page => {
      return page.title.toLowerCase().includes(q) || 
             page.keywords.some(k => k.includes(q));
    });
  }

  // Highlight matching text
  function highlightMatch(text, query) {
    if (!text) return '';
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  // Escape regex special chars
  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Format date
  function formatDate(dateStr) {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  }

  // Handle keyboard navigation
  function handleSearchKeydown(e) {
    const results = searchResults.querySelectorAll('.search-result');
    
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
      updateSelection(results);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, -1);
      updateSelection(results);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && results[selectedIndex]) {
        window.location.href = results[selectedIndex].dataset.url;
      }
    }
  }

  // Update visual selection
  function updateSelection(results) {
    results.forEach((el, i) => {
      el.classList.toggle('selected', i === selectedIndex);
    });
    
    if (selectedIndex >= 0 && results[selectedIndex]) {
      results[selectedIndex].scrollIntoView({ block: 'nearest' });
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
