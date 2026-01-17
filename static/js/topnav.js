// topnav.js: Discord-like desktop top navigation with intelligent dropdown panels.
// - Hover and keyboard friendly
// - No layout shift (panels are absolutely positioned)
// - Closes on outside click / Escape
(function () {
  function normalizePath(pathname) {
    try {
      const p = String(pathname || '/');
      const cleaned = p.replace(/\/+$/, '');
      return cleaned === '' ? '/' : cleaned;
    } catch (e) {
      return '/';
    }
  }

  function initTopnav(root) {
    if (!root || root.dataset.topnavInit === '1') return;
    root.dataset.topnavInit = '1';

    const dropdownItems = Array.from(root.querySelectorAll('[data-topnav-dropdown]'));

    function getTrigger(item) {
      return item.querySelector('[data-topnav-trigger]');
    }

    function setExpanded(item, expanded) {
      const trigger = getTrigger(item);
      if (trigger) trigger.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    }

    function closeItem(item) {
      if (!item) return;
      item.classList.remove('is-open');
      setExpanded(item, false);
    }

    function openItem(item) {
      if (!item) return;
      dropdownItems.forEach((it) => {
        if (it !== item) closeItem(it);
      });
      item.classList.add('is-open');
      setExpanded(item, true);
    }

    function closeAll() {
      dropdownItems.forEach(closeItem);
    }

    // Active link highlighting (stable + predictable)
    try {
      const current = normalizePath(window.location.pathname);
      const links = Array.from(root.querySelectorAll('a[href]'));
      links.forEach((a) => {
        try {
          const u = new URL(a.getAttribute('href'), window.location.origin);
          if (u.origin !== window.location.origin) return;
          const p = normalizePath(u.pathname);
          if (p === current) a.classList.add('is-active');
        } catch (e) {
          /* ignore */
        }
      });
      dropdownItems.forEach((item) => {
        const trigger = getTrigger(item);
        const activeChild = item.querySelector('.topnav__panel a.is-active');
        if (trigger && activeChild) trigger.classList.add('is-active');
      });
    } catch (e) {
      /* ignore */
    }

    // Hover open/close with small delays to prevent flicker
    const leaveTimers = new WeakMap();

    dropdownItems.forEach((item) => {
      const trigger = getTrigger(item);
      const panel = item.querySelector('.topnav__panel');
      if (!trigger || !panel) return;

      function clearLeaveTimer() {
        const t = leaveTimers.get(item);
        if (t) {
          window.clearTimeout(t);
          leaveTimers.delete(item);
        }
      }

      function scheduleClose() {
        clearLeaveTimer();
        const t = window.setTimeout(() => closeItem(item), 110);
        leaveTimers.set(item, t);
      }

      item.addEventListener('mouseenter', () => {
        clearLeaveTimer();
        openItem(item);
      });
      item.addEventListener('mouseleave', scheduleClose);

      // Keyboard/focus behavior
      trigger.addEventListener('click', (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const willOpen = !item.classList.contains('is-open');
        if (willOpen) openItem(item);
        else closeItem(item);
      });

      trigger.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowDown') {
          ev.preventDefault();
          openItem(item);
          const first = panel.querySelector('a[href]');
          if (first) first.focus();
        } else if (ev.key === 'Escape') {
          ev.preventDefault();
          closeItem(item);
          trigger.focus();
        }
      });

      panel.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape') {
          ev.preventDefault();
          closeItem(item);
          trigger.focus();
        }
      });

      // Keep open while focus is within item; close once focus leaves
      item.addEventListener('focusin', () => {
        clearLeaveTimer();
        openItem(item);
      });
      item.addEventListener('focusout', () => {
        window.setTimeout(() => {
          if (!item.contains(document.activeElement)) closeItem(item);
        }, 0);
      });
    });

    // Close when clicking outside
    document.addEventListener('click', (ev) => {
      if (!root.contains(ev.target)) closeAll();
    });

    // Close on Escape (global)
    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') closeAll();
    });
  }

  function boot() {
    const root = document.querySelector('.topnav');
    if (!root) return;
    initTopnav(root);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.addEventListener('pageshow', boot);
})();
