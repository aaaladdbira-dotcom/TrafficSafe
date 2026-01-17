/**
 * Accessibility Enhancements
 * ARIA labels, keyboard navigation, focus management, and screen reader support
 */

(function() {
  'use strict';

  // ============================================
  // KEYBOARD NAVIGATION
  // ============================================
  
  class KeyboardNavigation {
    constructor() {
      this.focusableSelectors = [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
        '[contenteditable]'
      ].join(', ');
      
      this.init();
    }

    init() {
      // Add keyboard navigation hints
      this.setupKeyboardShortcuts();
      
      // Enhance focus visibility
      this.setupFocusIndicators();
      
      // Add skip link
      this.addSkipLink();
      
      // Setup roving tabindex for menus
      this.setupRovingTabindex();
    }

    setupKeyboardShortcuts() {
      const shortcuts = new Map([
        ['/', () => this.focusSearch()],
        ['g+d', () => window.location.href = '/ui/dashboard'],
        ['g+a', () => window.location.href = '/ui/accidents'],
        ['g+s', () => window.location.href = '/ui/statistics'],
        ['g+i', () => window.location.href = '/ui/import-csv'],
        ['?', () => this.showShortcutsHelp()],
        ['Escape', () => this.closeModals()]
      ]);

      let keySequence = [];
      let keyTimeout;

      document.addEventListener('keydown', (e) => {
        // Don't trigger in inputs
        if (this.isInputElement(e.target)) return;
        
        clearTimeout(keyTimeout);
        keySequence.push(e.key.toLowerCase());
        
        // Check for compound shortcuts (like g+d)
        const compound = keySequence.slice(-2).join('+');
        const single = e.key.toLowerCase();
        
        if (shortcuts.has(compound)) {
          e.preventDefault();
          shortcuts.get(compound)();
          keySequence = [];
        } else if (shortcuts.has(single) && keySequence.length === 1) {
          if (e.key === '/' || e.key === '?') {
            e.preventDefault();
          }
          shortcuts.get(single)();
          keySequence = [];
        }
        
        // Clear sequence after delay
        keyTimeout = setTimeout(() => {
          keySequence = [];
        }, 1000);
      });
    }

    isInputElement(el) {
      return ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) ||
             el.isContentEditable;
    }

    focusSearch() {
      const searchInput = document.querySelector('[type="search"], .search-input, #search');
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    }

    showShortcutsHelp() {
      // Dispatch custom event for shortcuts modal
      document.dispatchEvent(new CustomEvent('show-shortcuts-help'));
    }

    closeModals() {
      // Close any open modals
      document.querySelectorAll('.modal.show').forEach(modal => {
        const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
        if (closeBtn) closeBtn.click();
      });
      
      // Close dropdowns
      document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
      });
    }

    setupFocusIndicators() {
      // Add visible focus state class
      document.addEventListener('focusin', (e) => {
        e.target.classList.add('keyboard-focus');
      });

      document.addEventListener('focusout', (e) => {
        e.target.classList.remove('keyboard-focus');
      });

      // Detect keyboard vs mouse navigation
      document.addEventListener('mousedown', () => {
        document.body.classList.add('using-mouse');
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          document.body.classList.remove('using-mouse');
        }
      });
    }

    addSkipLink() {
      if (document.getElementById('skip-link')) return;
      
      const skipLink = document.createElement('a');
      skipLink.id = 'skip-link';
      skipLink.href = '#main-content';
      skipLink.className = 'skip-link';
      skipLink.textContent = 'Skip to main content';
      
      document.body.insertBefore(skipLink, document.body.firstChild);
      
      // Add ID to main content if not present
      const main = document.querySelector('main, [role="main"], .main-content');
      if (main && !main.id) {
        main.id = 'main-content';
      }
    }

    setupRovingTabindex() {
      document.querySelectorAll('[role="menu"], [role="menubar"], [role="tablist"]').forEach(container => {
        const items = container.querySelectorAll('[role="menuitem"], [role="tab"]');
        if (items.length === 0) return;

        // Set initial tabindex
        items.forEach((item, index) => {
          item.setAttribute('tabindex', index === 0 ? '0' : '-1');
        });

        container.addEventListener('keydown', (e) => {
          const items = Array.from(container.querySelectorAll('[role="menuitem"], [role="tab"]'));
          const currentIndex = items.indexOf(e.target);

          let newIndex;
          switch (e.key) {
            case 'ArrowRight':
            case 'ArrowDown':
              e.preventDefault();
              newIndex = (currentIndex + 1) % items.length;
              break;
            case 'ArrowLeft':
            case 'ArrowUp':
              e.preventDefault();
              newIndex = (currentIndex - 1 + items.length) % items.length;
              break;
            case 'Home':
              e.preventDefault();
              newIndex = 0;
              break;
            case 'End':
              e.preventDefault();
              newIndex = items.length - 1;
              break;
            default:
              return;
          }

          items[currentIndex].setAttribute('tabindex', '-1');
          items[newIndex].setAttribute('tabindex', '0');
          items[newIndex].focus();
        });
      });
    }

    getFocusableElements(container = document) {
      return Array.from(container.querySelectorAll(this.focusableSelectors))
        .filter(el => {
          return el.offsetWidth > 0 && el.offsetHeight > 0;
        });
    }

    trapFocus(container) {
      const focusable = this.getFocusableElements(container);
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      const trapHandler = (e) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      };

      container.addEventListener('keydown', trapHandler);
      return () => container.removeEventListener('keydown', trapHandler);
    }
  }

  // ============================================
  // ARIA ENHANCEMENTS
  // ============================================
  
  class AriaEnhancements {
    constructor() {
      this.init();
    }

    init() {
      this.enhanceTables();
      this.enhanceButtons();
      this.enhanceForms();
      this.enhanceAlerts();
      this.enhanceNavigation();
      this.setupLiveRegions();
    }

    enhanceTables() {
      document.querySelectorAll('table').forEach(table => {
        if (!table.getAttribute('role')) {
          table.setAttribute('role', 'table');
        }
        
        // Add caption if missing
        if (!table.querySelector('caption') && !table.getAttribute('aria-label')) {
          const heading = table.closest('.card, .panel')?.querySelector('h1, h2, h3, h4, h5, h6');
          if (heading) {
            table.setAttribute('aria-label', heading.textContent.trim());
          }
        }

        // Enhance header cells
        table.querySelectorAll('th').forEach(th => {
          if (!th.getAttribute('scope')) {
            th.setAttribute('scope', th.closest('thead') ? 'col' : 'row');
          }
        });
      });
    }

    enhanceButtons() {
      document.querySelectorAll('button, [role="button"]').forEach(btn => {
        // Add aria-pressed for toggle buttons
        if (btn.classList.contains('toggle') || btn.dataset.toggle) {
          const isPressed = btn.classList.contains('active') || 
                           btn.getAttribute('aria-pressed') === 'true';
          btn.setAttribute('aria-pressed', isPressed);
        }

        // Add aria-expanded for dropdown triggers
        if (btn.dataset.bsToggle === 'dropdown' || btn.classList.contains('dropdown-toggle')) {
          btn.setAttribute('aria-expanded', 'false');
          btn.setAttribute('aria-haspopup', 'true');
        }

        // Ensure icon-only buttons have labels
        if (btn.textContent.trim() === '' && !btn.getAttribute('aria-label')) {
          const icon = btn.querySelector('svg, i, [class*="icon"]');
          if (icon) {
            const title = btn.title || icon.getAttribute('title') || 'Button';
            btn.setAttribute('aria-label', title);
          }
        }
      });
    }

    enhanceForms() {
      // Link labels and inputs
      document.querySelectorAll('label').forEach(label => {
        const forAttr = label.getAttribute('for');
        if (!forAttr) {
          const input = label.querySelector('input, select, textarea');
          if (input && !input.id) {
            input.id = `input-${Math.random().toString(36).substr(2, 9)}`;
            label.setAttribute('for', input.id);
          }
        }
      });

      // Mark required fields
      document.querySelectorAll('[required]').forEach(input => {
        input.setAttribute('aria-required', 'true');
        
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label && !label.querySelector('.required-indicator')) {
          const indicator = document.createElement('span');
          indicator.className = 'required-indicator';
          indicator.setAttribute('aria-hidden', 'true');
          indicator.textContent = ' *';
          label.appendChild(indicator);
        }
      });

      // Add descriptions for form fields with help text
      document.querySelectorAll('.form-text, .help-text').forEach(help => {
        const input = help.previousElementSibling?.querySelector('input, select, textarea') ||
                     help.parentElement?.querySelector('input, select, textarea');
        if (input) {
          if (!help.id) {
            help.id = `help-${Math.random().toString(36).substr(2, 9)}`;
          }
          input.setAttribute('aria-describedby', help.id);
        }
      });
    }

    enhanceAlerts() {
      document.querySelectorAll('.alert').forEach(alert => {
        if (!alert.getAttribute('role')) {
          alert.setAttribute('role', 'alert');
        }
        
        // Add aria-live for dynamic alerts
        if (!alert.getAttribute('aria-live')) {
          alert.setAttribute('aria-live', 'polite');
        }
      });
    }

    enhanceNavigation() {
      // Add navigation landmarks
      document.querySelectorAll('nav').forEach(nav => {
        if (!nav.getAttribute('aria-label')) {
          if (nav.classList.contains('navbar') || nav.classList.contains('topnav')) {
            nav.setAttribute('aria-label', 'Main navigation');
          } else if (nav.classList.contains('breadcrumb')) {
            nav.setAttribute('aria-label', 'Breadcrumb');
          } else if (nav.classList.contains('pagination')) {
            nav.setAttribute('aria-label', 'Pagination');
          }
        }
      });

      // Mark current page in navigation
      document.querySelectorAll('nav a').forEach(link => {
        if (link.href === window.location.href || 
            link.classList.contains('active')) {
          link.setAttribute('aria-current', 'page');
        }
      });
    }

    setupLiveRegions() {
      // Create live region for announcements
      if (!document.getElementById('aria-live-region')) {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'aria-live-region';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        document.body.appendChild(liveRegion);
      }
    }

    announce(message, priority = 'polite') {
      const liveRegion = document.getElementById('aria-live-region');
      if (liveRegion) {
        liveRegion.setAttribute('aria-live', priority);
        liveRegion.textContent = '';
        // Slight delay to ensure announcement
        setTimeout(() => {
          liveRegion.textContent = message;
        }, 50);
      }
    }
  }

  // ============================================
  // FOCUS MANAGEMENT
  // ============================================
  
  class FocusManager {
    constructor() {
      this.focusHistory = [];
      this.maxHistory = 10;
    }

    saveFocus() {
      if (document.activeElement && document.activeElement !== document.body) {
        this.focusHistory.push(document.activeElement);
        if (this.focusHistory.length > this.maxHistory) {
          this.focusHistory.shift();
        }
      }
    }

    restoreFocus() {
      const element = this.focusHistory.pop();
      if (element && document.body.contains(element)) {
        element.focus();
        return true;
      }
      return false;
    }

    focusFirst(container) {
      const focusable = Array.from(container.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);
      
      if (focusable[0]) {
        focusable[0].focus();
        return true;
      }
      return false;
    }

    focusHeading(level = 1) {
      const heading = document.querySelector(`h${level}, [role="heading"][aria-level="${level}"]`);
      if (heading) {
        heading.setAttribute('tabindex', '-1');
        heading.focus();
        return true;
      }
      return false;
    }
  }

  // ============================================
  // REDUCED MOTION SUPPORT
  // ============================================
  
  function setupReducedMotion() {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    function handleReducedMotion(e) {
      if (e.matches) {
        document.body.classList.add('reduce-motion');
        // Disable animations
        document.documentElement.style.setProperty('--animation-duration', '0.01ms');
        document.documentElement.style.setProperty('--transition-duration', '0.01ms');
      } else {
        document.body.classList.remove('reduce-motion');
        document.documentElement.style.removeProperty('--animation-duration');
        document.documentElement.style.removeProperty('--transition-duration');
      }
    }
    
    mediaQuery.addEventListener('change', handleReducedMotion);
    handleReducedMotion(mediaQuery);
  }

  // ============================================
  // HIGH CONTRAST SUPPORT
  // ============================================
  
  function setupHighContrast() {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    
    function handleHighContrast(e) {
      if (e.matches) {
        document.body.classList.add('high-contrast');
      } else {
        document.body.classList.remove('high-contrast');
      }
    }
    
    mediaQuery.addEventListener('change', handleHighContrast);
    handleHighContrast(mediaQuery);
  }

  // ============================================
  // ADD ACCESSIBILITY STYLES
  // ============================================
  
  function addA11yStyles() {
    const style = document.createElement('style');
    style.textContent = `
      /* Screen reader only */
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      }
      
      /* Skip link */
      .skip-link {
        position: absolute;
        top: -100%;
        left: 16px;
        background: var(--ui-primary, #3b82f6);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 99999;
        transition: top 200ms ease;
        text-decoration: none;
      }
      
      .skip-link:focus {
        top: 16px;
      }
      
      /* Focus visible styles */
      body:not(.using-mouse) *:focus {
        outline: 3px solid var(--ui-focus, rgba(59, 130, 246, 0.5));
        outline-offset: 2px;
      }
      
      body.using-mouse *:focus {
        outline: none;
      }
      
      /* Keyboard focus specific */
      .keyboard-focus {
        box-shadow: 0 0 0 3px var(--ui-focus, rgba(59, 130, 246, 0.5)) !important;
      }
      
      /* Required field indicator */
      .required-indicator {
        color: #ef4444;
        font-weight: 700;
      }
      
      /* High contrast mode adjustments */
      .high-contrast .card,
      .high-contrast .btn {
        border-width: 2px !important;
      }
      
      .high-contrast .btn-primary {
        background: #000 !important;
        color: #fff !important;
      }
      
      /* Reduced motion */
      .reduce-motion * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
      }
    `;
    document.head.appendChild(style);
  }

  // ============================================
  // INITIALIZE
  // ============================================
  
  document.addEventListener('DOMContentLoaded', () => {
    addA11yStyles();
    
    const keyboard = new KeyboardNavigation();
    const aria = new AriaEnhancements();
    const focus = new FocusManager();
    
    setupReducedMotion();
    setupHighContrast();
    
    // Export for use in other scripts
    window.Accessibility = {
      keyboard,
      aria,
      focus,
      announce: (msg, priority) => aria.announce(msg, priority)
    };
  });

  // Re-run enhancements on dynamic content
  const observer = new MutationObserver((mutations) => {
    let shouldEnhance = false;
    mutations.forEach(m => {
      if (m.addedNodes.length > 0) {
        shouldEnhance = true;
      }
    });
    
    if (shouldEnhance && window.Accessibility) {
      // Debounce enhancements
      clearTimeout(window._a11yEnhanceTimeout);
      window._a11yEnhanceTimeout = setTimeout(() => {
        const aria = new AriaEnhancements();
      }, 100);
    }
  });

  observer.observe(document.body, { 
    childList: true, 
    subtree: true 
  });

})();
