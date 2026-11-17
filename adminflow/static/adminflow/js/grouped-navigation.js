document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('admin-sidebar');
  const nav = sidebar?.querySelector('nav[data-af-grouped-nav="true"]');
  if (!sidebar || !nav) return;

  nav.setAttribute('aria-label', 'Administration categories');
  const groups = [...nav.querySelectorAll('details[data-nav-key]')];
  if (!groups.length) return;

  const remember = group => {
    try {
      sessionStorage.setItem(`af-admin-nav:${group.dataset.navKey}`, group.open ? 'open' : 'closed');
    } catch (_) {
      /* Storage may be unavailable in restricted browsing modes. */
    }
  };

  const siblings = group =>
    groups.filter(other => other !== group && other.parentElement === group.parentElement);

  groups.forEach(group => {
    const key = `af-admin-nav:${group.dataset.navKey}`;
    try {
      if (!group.hasAttribute('data-active')) {
        group.open = sessionStorage.getItem(key) === 'open';
      }
    } catch (_) {
      /* Keep server-rendered open state when sessionStorage is unavailable. */
    }
  });

  // Ensure at most one open group per level, preferring the active page's group.
  const parents = new Set(groups.map(group => group.parentElement));
  parents.forEach(parent => {
    const children = groups.filter(group => group.parentElement === parent);
    const selected =
      children.find(group => group.open && group.hasAttribute('data-active')) ||
      children.find(group => group.open);
    children.forEach(group => {
      group.open = group === selected;
      remember(group);
    });
  });

  groups.forEach(group => {
    group.addEventListener('toggle', () => {
      if (group.open) {
        siblings(group).forEach(other => {
          other.open = false;
          remember(other);
        });
      }
      remember(group);
    });
  });

  nav.querySelectorAll('.af-nav-group > summary').forEach(summary => {
    summary.addEventListener('click', () => {
      if (sidebar.classList.contains('sidebar-collapsed') && typeof toggleSidebar === 'function') {
        toggleSidebar();
      }
    });
  });
});

