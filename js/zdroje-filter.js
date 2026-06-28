;(function () {
  function initZdrojeFilter() {
    var h1 = document.querySelector('.md-content__inner > h1');
    if (!h1 || h1.textContent.trim() !== 'Zdroje') return;

    var content = document.querySelector('.md-content__inner');
    if (!content) return;

    var h2s = Array.from(content.querySelectorAll('h2'));
    if (!h2s.length) return;

    // person name → [h2, ...]
    var personMap = new Map();
    h2s.forEach(function (h2) {
      var text = h2.textContent.trim();
      var dashIdx = text.indexOf('—'); // em dash —
      var person = dashIdx >= 0 ? text.substring(0, dashIdx).trim() : text;
      if (!personMap.has(person)) personMap.set(person, []);
      personMap.get(person).push(h2);
    });

    var tocInner = document.querySelector('.md-sidebar--secondary .md-sidebar__inner');
    if (!tocInner) return;

    // Build nav using Material's TOC classes for consistent styling
    var nav = document.createElement('nav');
    nav.className = 'md-nav md-nav--secondary';
    nav.setAttribute('aria-label', 'Filtr kanálů');

    var headingEl = document.createElement('span');
    headingEl.className = 'md-nav__title';
    headingEl.textContent = 'Kanály';
    nav.appendChild(headingEl);

    var ul = document.createElement('ul');
    ul.className = 'md-nav__list';

    function makeItem(label, person, active) {
      var li = document.createElement('li');
      li.className = 'md-nav__item';
      var a = document.createElement('a');
      a.href = '#';
      a.className = 'md-nav__link' + (active ? ' md-nav__link--active' : '');
      a.dataset.person = person;
      a.textContent = label;
      li.appendChild(a);
      return li;
    }

    ul.appendChild(makeItem('Vše (' + h2s.length + ')', '', true));
    personMap.forEach(function (entries, name) {
      ul.appendChild(makeItem(name + ' (' + entries.length + ')', name, false));
    });

    nav.appendChild(ul);
    tocInner.innerHTML = '';
    tocInner.appendChild(nav);

    // All DOM nodes belonging to one section (h2 + siblings until next h2)
    function sectionEls(h2) {
      var els = [h2];
      var el = h2.nextElementSibling;
      while (el && el.tagName !== 'H2') {
        els.push(el);
        el = el.nextElementSibling;
      }
      return els;
    }

    function applyFilter(activePerson) {
      h2s.forEach(function (h2) {
        var text = h2.textContent.trim();
        var dashIdx = text.indexOf('—');
        var person = dashIdx >= 0 ? text.substring(0, dashIdx).trim() : text;
        var show = !activePerson || person === activePerson;
        sectionEls(h2).forEach(function (el) {
          el.style.display = show ? '' : 'none';
        });
      });
    }

    nav.addEventListener('click', function (e) {
      e.preventDefault();
      var a = e.target.closest('a.md-nav__link');
      if (!a || !('person' in a.dataset)) return;
      nav.querySelectorAll('a.md-nav__link').forEach(function (el) {
        el.classList.toggle('md-nav__link--active', el === a);
      });
      applyFilter(a.dataset.person);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initZdrojeFilter);
  } else {
    initZdrojeFilter();
  }
})();
