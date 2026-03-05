'use strict';

{
  var initSidebarQuickFilter = function initSidebarQuickFilter() {
    var options = [];
    var navSidebar = document.getElementById('nav-sidebar');

    if (!navSidebar) {
      return;
    }

    navSidebar.querySelectorAll('th[scope=row] a').forEach(function (container) {
      options.push({
        title: container.innerHTML,
        node: container
      });
    });

    function checkValue(event) {
      var filterValue = event.target.value;

      if (filterValue) {
        filterValue = filterValue.toLowerCase();
      }

      if (event.key === 'Escape') {
        filterValue = '';
        event.target.value = ''; // clear input
      }

      var matches = false;
      var _iteratorNormalCompletion = true;
      var _didIteratorError = false;
      var _iteratorError = undefined;

      try {
        for (var _iterator = options[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
          var o = _step.value;
          var displayValue = '';

          if (filterValue) {
            if (o.title.toLowerCase().indexOf(filterValue) === -1) {
              displayValue = 'none';
            } else {
              matches = true;
            }
          } // show/hide parent <TR>


          o.node.parentNode.parentNode.style.display = displayValue;
        }
      } catch (err) {
        _didIteratorError = true;
        _iteratorError = err;
      } finally {
        try {
          if (!_iteratorNormalCompletion && _iterator["return"] != null) {
            _iterator["return"]();
          }
        } finally {
          if (_didIteratorError) {
            throw _iteratorError;
          }
        }
      }

      if (!filterValue || matches) {
        event.target.classList.remove('no-results');
      } else {
        event.target.classList.add('no-results');
      }

      sessionStorage.setItem('django.admin.navSidebarFilterValue', filterValue);
    }

    var nav = document.getElementById('nav-filter');
    nav.addEventListener('change', checkValue, false);
    nav.addEventListener('input', checkValue, false);
    nav.addEventListener('keyup', checkValue, false);
    var storedValue = sessionStorage.getItem('django.admin.navSidebarFilterValue');

    if (storedValue) {
      nav.value = storedValue;
      checkValue({
        target: nav,
        key: ''
      });
    }
  };

  var toggleNavSidebar = document.getElementById('toggle-nav-sidebar');

  if (toggleNavSidebar !== null) {
    var navSidebar = document.getElementById('nav-sidebar');
    var main = document.getElementById('main');
    var navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen');

    if (navSidebarIsOpen === null) {
      navSidebarIsOpen = 'true';
    }

    main.classList.toggle('shifted', navSidebarIsOpen === 'true');
    navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
    toggleNavSidebar.addEventListener('click', function () {
      if (navSidebarIsOpen === 'true') {
        navSidebarIsOpen = 'false';
      } else {
        navSidebarIsOpen = 'true';
      }

      localStorage.setItem('django.admin.navSidebarIsOpen', navSidebarIsOpen);
      main.classList.toggle('shifted');
      navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
    });
  }

  window.initSidebarQuickFilter = initSidebarQuickFilter;
  initSidebarQuickFilter();
}