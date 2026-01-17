/**
 * Onboarding Tour
 * First-time user walkthrough
 */

(function() {
  'use strict';

  const TOUR_KEY = 'onboarding_completed';
  
  // Tour steps configuration
  const tourSteps = [
    {
      element: '.sidebar, .topnav',
      title: 'Welcome to Traffic Accident System! 👋',
      description: 'Let us give you a quick tour of the main features.',
      position: 'center'
    },
    {
      element: '[href*="dashboard"], .nav-item:first-child',
      title: 'Dashboard',
      description: 'Your home base. See key statistics and recent activity at a glance.',
      position: 'right'
    },
    {
      element: '[href*="accidents"], [href*="accident"]',
      title: 'Accidents Database',
      description: 'Browse, search, and filter all accident records. Export data in various formats.',
      position: 'right'
    },
    {
      element: '[href*="statistics"], [href*="stats"]',
      title: 'Statistics & Analytics',
      description: 'Visualize accident data with interactive charts and maps.',
      position: 'right'
    },
    {
      element: '[href*="report"]',
      title: 'Report an Accident',
      description: 'Citizens can report accidents directly through this form.',
      position: 'right'
    },
    {
      element: '[href*="import"]',
      title: 'Import Data',
      description: 'Admins can bulk import accident data from CSV files.',
      position: 'right'
    },
    {
      element: '.global-search-item, #globalSearchInput, [data-search]',
      title: 'Quick Search (Ctrl+K)',
      description: 'Press Ctrl+K anytime to quickly search and navigate. Press ? for all keyboard shortcuts.',
      position: 'bottom'
    },
    {
      element: '.user-menu, .profile-dropdown, [href*="account"]',
      title: 'Your Profile',
      description: 'Access your account settings, toggle dark mode, and manage preferences.',
      position: 'left'
    },
    {
      element: 'body',
      title: "You're All Set! 🎉",
      description: 'Start exploring the system. Press ? anytime for keyboard shortcuts help.',
      position: 'center'
    }
  ];

  // Check if tour should show
  function shouldShowTour() {
    return !localStorage.getItem(TOUR_KEY);
  }

  // Mark tour as completed
  function completeTour() {
    localStorage.setItem(TOUR_KEY, 'true');
  }

  // Reset tour (for testing)
  function resetTour() {
    localStorage.removeItem(TOUR_KEY);
  }

  // Create tour overlay
  function createOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'tour-overlay';
    overlay.innerHTML = `
      <div class="tour-backdrop"></div>
      <div class="tour-spotlight"></div>
      <div class="tour-popover">
        <div class="tour-popover-arrow"></div>
        <div class="tour-popover-content">
          <h4 class="tour-title"></h4>
          <p class="tour-description"></p>
        </div>
        <div class="tour-popover-footer">
          <div class="tour-progress">
            <span class="tour-step-current">1</span> / <span class="tour-step-total">9</span>
          </div>
          <div class="tour-buttons">
            <button class="tour-btn tour-btn-skip">Skip</button>
            <button class="tour-btn tour-btn-prev">Previous</button>
            <button class="tour-btn tour-btn-next tour-btn-primary">Next</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    return overlay;
  }

  // Position the spotlight and popover
  function positionStep(overlay, step) {
    const spotlight = overlay.querySelector('.tour-spotlight');
    const popover = overlay.querySelector('.tour-popover');
    
    let targetElement = null;
    
    // Try to find element
    if (step.element && step.element !== 'body') {
      targetElement = document.querySelector(step.element);
    }
    
    if (targetElement && step.position !== 'center') {
      const rect = targetElement.getBoundingClientRect();
      const padding = 8;
      
      // Position spotlight
      spotlight.style.cssText = `
        display: block;
        top: ${rect.top - padding + window.scrollY}px;
        left: ${rect.left - padding}px;
        width: ${rect.width + padding * 2}px;
        height: ${rect.height + padding * 2}px;
      `;
      
      // Scroll element into view if needed
      if (rect.top < 0 || rect.bottom > window.innerHeight) {
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      
      // Position popover
      const popoverRect = popover.getBoundingClientRect();
      let top, left;
      
      switch (step.position) {
        case 'right':
          top = rect.top + rect.height / 2 - popoverRect.height / 2 + window.scrollY;
          left = rect.right + 16;
          break;
        case 'left':
          top = rect.top + rect.height / 2 - popoverRect.height / 2 + window.scrollY;
          left = rect.left - popoverRect.width - 16;
          break;
        case 'bottom':
          top = rect.bottom + 16 + window.scrollY;
          left = rect.left + rect.width / 2 - popoverRect.width / 2;
          break;
        case 'top':
          top = rect.top - popoverRect.height - 16 + window.scrollY;
          left = rect.left + rect.width / 2 - popoverRect.width / 2;
          break;
        default:
          top = rect.bottom + 16 + window.scrollY;
          left = rect.left + rect.width / 2 - popoverRect.width / 2;
      }
      
      // Keep popover in viewport
      left = Math.max(16, Math.min(left, window.innerWidth - popoverRect.width - 16));
      top = Math.max(16, top);
      
      popover.style.top = `${top}px`;
      popover.style.left = `${left}px`;
      popover.setAttribute('data-position', step.position);
      
    } else {
      // Center position (for welcome/end screens)
      spotlight.style.display = 'none';
      popover.style.top = '50%';
      popover.style.left = '50%';
      popover.style.transform = 'translate(-50%, -50%)';
      popover.setAttribute('data-position', 'center');
    }
  }

  // Update step content
  function updateStep(overlay, step, index, total) {
    overlay.querySelector('.tour-title').textContent = step.title;
    overlay.querySelector('.tour-description').textContent = step.description;
    overlay.querySelector('.tour-step-current').textContent = index + 1;
    overlay.querySelector('.tour-step-total').textContent = total;
    
    // Update button visibility
    const prevBtn = overlay.querySelector('.tour-btn-prev');
    const nextBtn = overlay.querySelector('.tour-btn-next');
    
    prevBtn.style.display = index === 0 ? 'none' : 'block';
    nextBtn.textContent = index === total - 1 ? 'Finish' : 'Next';
    
    // Position after content update
    setTimeout(() => positionStep(overlay, step), 50);
  }

  // Start the tour
  function startTour() {
    let currentStep = 0;
    const overlay = createOverlay();
    
    // Update initial step
    updateStep(overlay, tourSteps[currentStep], currentStep, tourSteps.length);
    
    // Event handlers
    const skipBtn = overlay.querySelector('.tour-btn-skip');
    const prevBtn = overlay.querySelector('.tour-btn-prev');
    const nextBtn = overlay.querySelector('.tour-btn-next');
    
    skipBtn.addEventListener('click', () => {
      completeTour();
      overlay.remove();
    });
    
    prevBtn.addEventListener('click', () => {
      if (currentStep > 0) {
        currentStep--;
        updateStep(overlay, tourSteps[currentStep], currentStep, tourSteps.length);
      }
    });
    
    nextBtn.addEventListener('click', () => {
      if (currentStep < tourSteps.length - 1) {
        currentStep++;
        updateStep(overlay, tourSteps[currentStep], currentStep, tourSteps.length);
      } else {
        completeTour();
        overlay.remove();
        if (window.Toast) {
          Toast.success('Tour completed! Press ? for keyboard shortcuts.', 'Welcome!');
        }
      }
    });
    
    // ESC to skip
    document.addEventListener('keydown', function escHandler(e) {
      if (e.key === 'Escape') {
        completeTour();
        overlay.remove();
        document.removeEventListener('keydown', escHandler);
      }
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
      positionStep(overlay, tourSteps[currentStep]);
    });
  }

  // Initialize on page load
  document.addEventListener('DOMContentLoaded', () => {
    // Only show on dashboard
    if (shouldShowTour() && window.location.pathname.includes('dashboard')) {
      setTimeout(startTour, 1000);
    }
  });

  // Expose API
  window.OnboardingTour = {
    start: startTour,
    reset: resetTour,
    isCompleted: () => !shouldShowTour()
  };

})();
