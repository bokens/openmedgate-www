(function () {
  var root = document.documentElement;
  root.classList.add('js');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Mobile navigation.
  var navToggle = document.querySelector('[data-nav-toggle]');
  var nav = document.getElementById('nav');
  if (navToggle && nav) {
    var setNav = function (open) {
      nav.classList.toggle('is-open', open);
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    navToggle.addEventListener('click', function () { setNav(!nav.classList.contains('is-open')); });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) { setNav(false); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { setNav(false); } });
  }

  // Header hairline once the page is scrolled.
  var header = document.querySelector('[data-header]');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Reveal on scroll.
  var items = document.querySelectorAll('.reveal');
  var io = null;
  if ('IntersectionObserver' in window && !reduced) {
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add('is-in'); io.unobserve(entry.target); }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.06 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('is-in'); });
  }

  // Videos: play only while visible; never autoplay when the visitor prefers reduced motion.
  var videos = document.querySelectorAll('[data-video]');
  if (reduced) {
    videos.forEach(function (v) { v.removeAttribute('autoplay'); v.pause(); });
  } else if ('IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var v = entry.target;
        if (entry.isIntersecting) { var p = v.play(); if (p && p.catch) { p.catch(function () {}); } }
        else { v.pause(); }
      });
    }, { threshold: 0.1 });
    videos.forEach(function (v) { vio.observe(v); });
  }

  // Mechanism diagram: closed today, open by design. Cycles on its own until the visitor takes over.
  var mech = document.querySelector('[data-mech]');
  var toggle = document.querySelector('[data-mech-toggle]');
  if (mech && toggle) {
    var buttons = Array.prototype.slice.call(toggle.querySelectorAll('[data-state]'));
    var setState = function (state) {
      mech.setAttribute('data-state', state);
      buttons.forEach(function (b) { b.classList.toggle('is-active', b.getAttribute('data-state') === state); });
    };
    var timer = null;
    var cycle = function () {
      timer = setInterval(function () {
        setState(mech.getAttribute('data-state') === 'closed' ? 'open' : 'closed');
      }, 5000);
    };
    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        if (timer) { clearInterval(timer); timer = null; }
        setState(b.getAttribute('data-state'));
      });
    });
    if (!reduced && 'IntersectionObserver' in window) {
      var mio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !timer) {
            setTimeout(function () { setState('open'); }, 2200);
            cycle();
            mio.disconnect();
          }
        });
      }, { threshold: 0.4 });
      mio.observe(mech);
    }
  }

  // Dot matrix: fills to data-filled when a number exists; shimmers as a placeholder otherwise.
  var matrix = document.querySelector('[data-matrix]');
  if (matrix) {
    var filled = parseInt(matrix.getAttribute('data-filled'), 10);
    var dots = matrix.querySelectorAll('i');
    if (isNaN(filled)) {
      matrix.classList.add('is-ph');
    } else {
      var fill = function () {
        for (var i = 0; i < Math.min(filled, dots.length); i++) {
          (function (dot, n) { setTimeout(function () { dot.classList.add('on'); }, reduced ? 0 : n * 18); })(dots[i], i);
        }
      };
      if ('IntersectionObserver' in window) {
        var dio = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) { if (entry.isIntersecting) { fill(); dio.disconnect(); } });
        }, { threshold: 0.3 });
        dio.observe(matrix);
      } else { fill(); }
    }
  }

  // Copy link on posts.
  document.querySelectorAll('[data-copy-link]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var url = btn.getAttribute('data-copy-link');
      var label = btn.textContent;
      var done = function () {
        btn.textContent = btn.getAttribute('data-copied');
        setTimeout(function () { btn.textContent = label; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, done);
      } else {
        var t = document.createElement('textarea');
        t.value = url; document.body.appendChild(t); t.select();
        try { document.execCommand('copy'); } catch (e) { /* ignore */ }
        document.body.removeChild(t); done();
      }
    });
  });
})();
