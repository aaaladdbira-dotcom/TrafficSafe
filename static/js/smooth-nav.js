// smooth-nav.js: smoother full-page navigation with graceful fallbacks.
// - Prefers native cross-document View Transitions when available.
// - Otherwise, keeps a quick fade-out without slowing down navigation.
// - Light prefetching on hover/focus to warm the cache for nav links.
(function () {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const containerSelectors = ['main.main-content', '.container.mt-4', '.container'];
  const animDuration = 140;
  const prefetchCache = new Set();

  function getContainer(root) {
    for (const sel of containerSelectors) {
      const el = (root || document).querySelector(sel);
      if (el) return el;
    }
    return null;
  }

  function samePageIgnoringHash(url) {
    try {
      const u = new URL(url, window.location.href);
      const here = new URL(window.location.href);
      u.hash = '';
      here.hash = '';
      return u.href === here.href;
    } catch (e) {
      return false;
    }
  }

  function shouldHandleLink(a, clickEvent) {
    if (!a || !a.href) return false;

    if (clickEvent) {
      if (clickEvent.defaultPrevented) return false;
      if (clickEvent.button !== 0) return false;
      if (clickEvent.metaKey || clickEvent.ctrlKey || clickEvent.shiftKey || clickEvent.altKey) return false;
    }

    if (a.target && a.target.toLowerCase() === '_blank') return false;
    if (a.hasAttribute('download')) return false;
    if (a.getAttribute('rel') && a.getAttribute('rel').includes('external')) return false;
    if (a.dataset && (a.dataset.noSmoothNav === '1' || a.dataset.noPjax === '1')) return false;

    const href = a.getAttribute('href') || '';
    if (href.startsWith('#')) return false;
    if (href.startsWith('mailto:') || href.startsWith('tel:')) return false;

    let url;
    try {
      url = new URL(a.href, window.location.href);
    } catch (e) {
      return false;
    }

    if (url.origin !== window.location.origin) return false;
    if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/api/')) return false;
    if (url.pathname === '/ui/logout') return false;
    if (samePageIgnoringHash(url.href)) return false;

    return true;
  }

  function useNativeViewTransition(url) {
    if (!document.startViewTransition) return false;
    // Keep old content visible while the next page streams in.
    document.startViewTransition(() => {
      window.location.href = url;
      return new Promise(() => {});
    });
    return true;
  }

  function fadeOut(el) {
    return new Promise((resolve) => {
      if (!el) return resolve();
      el.style.transition = `opacity ${animDuration}ms cubic-bezier(0.22,1,0.36,1), transform ${animDuration}ms cubic-bezier(0.22,1,0.36,1)`;
      el.style.opacity = 0;
      el.style.transform = 'translateY(12px)';
      window.setTimeout(resolve, animDuration);
    });
  }

  async function animatedNavigateTo(url) {
    if (useNativeViewTransition(url)) return;

    const container = getContainer(document);
    if (!container) {
      window.location.href = url;
      return;
    }

    document.body && document.body.classList.add('is-navigating');
    fadeOut(container);
    // Do not wait for the fade to finish; kick off navigation immediately.
    window.requestAnimationFrame(() => {
      window.location.href = url;
    });
  }

  function prefetch(url) {
    try {
      const parsed = new URL(url, window.location.href);
      if (parsed.origin !== window.location.origin) return;
      if (prefetchCache.has(parsed.href)) return;
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = parsed.href;
      document.head.appendChild(link);
      prefetchCache.add(parsed.href);
    } catch (e) {
      /* ignore */
    }
  }

  document.addEventListener('click', function (e) {
    const a = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!shouldHandleLink(a, e)) return;
    e.preventDefault();
    animatedNavigateTo(a.href);
  });

  document.addEventListener('mouseover', function (e) {
    const a = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!shouldHandleLink(a)) return;
    prefetch(a.href);
  });

  document.addEventListener('focusin', function (e) {
    const a = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!shouldHandleLink(a)) return;
    prefetch(a.href);
  });
})();
