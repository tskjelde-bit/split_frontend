/* ============================================
   SNYTEKLUT — Landing Page Scripts
   ============================================ */

(function () {
  'use strict';

  // --- Scroll-triggered fade-in animations ---
  const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -40px 0px'
  };

  const fadeObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        fadeObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-up').forEach(function (el) {
    fadeObserver.observe(el);
  });


  // --- Navigation scroll state ---
  var nav = document.getElementById('nav');
  var lastScroll = 0;

  function handleNavScroll() {
    var scrollY = window.scrollY;
    if (scrollY > 60) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
    lastScroll = scrollY;
  }

  window.addEventListener('scroll', handleNavScroll, { passive: true });
  handleNavScroll();


  // --- Mobile menu toggle ---
  var navToggle = document.getElementById('navToggle');
  var navLinks = document.querySelector('.nav-links');

  navToggle.addEventListener('click', function () {
    navToggle.classList.toggle('active');
    navLinks.classList.toggle('open');
    document.body.style.overflow = navLinks.classList.contains('open') ? 'hidden' : '';
  });

  // Close mobile menu when clicking a link
  navLinks.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      navToggle.classList.remove('active');
      navLinks.classList.remove('open');
      document.body.style.overflow = '';
    });
  });


  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var targetId = this.getAttribute('href');
      if (targetId === '#') return;

      var target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        var navHeight = nav.offsetHeight;
        var targetPosition = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });


  // --- Contact form handling ---
  var contactForm = document.getElementById('contactForm');
  var formSuccess = document.getElementById('formSuccess');

  contactForm.addEventListener('submit', function (e) {
    e.preventDefault();

    // Collect form data (ready for future backend integration)
    var formData = {
      institution: contactForm.querySelector('#institution').value,
      contact: contactForm.querySelector('#contact').value,
      email: contactForm.querySelector('#email').value,
      quantity: contactForm.querySelector('#quantity').value,
      model: contactForm.querySelector('#model').value,
      message: contactForm.querySelector('#message').value
    };

    // Log for development
    console.log('Form submitted:', formData);

    // Show success message
    contactForm.style.display = 'none';
    formSuccess.classList.add('visible');

    // Scroll to success message
    formSuccess.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });


  // --- Stat counter animation ---
  var statObserverOptions = {
    threshold: 0.5
  };

  var statObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        var numberEl = entry.target.querySelector('.stat-number');
        if (numberEl && !numberEl.dataset.animated) {
          animateStatNumber(numberEl);
          numberEl.dataset.animated = 'true';
        }
      }
    });
  }, statObserverOptions);

  document.querySelectorAll('.stat-card').forEach(function (card) {
    statObserver.observe(card);
  });

  function animateStatNumber(el) {
    var text = el.textContent.trim();
    // Extract the numeric part
    var match = text.match(/^(\d+)/);
    if (!match) return;

    var target = parseInt(match[1], 10);
    var suffix = text.replace(match[1], '');
    var duration = 1200;
    var startTime = null;

    // Preserve any child elements (like .stat-unit span)
    var unitSpan = el.querySelector('.stat-unit');
    var unitHTML = unitSpan ? unitSpan.outerHTML : '';
    var textSuffix = suffix.replace(unitSpan ? unitSpan.textContent : '', '');

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);

      // Ease out cubic
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(eased * target);

      el.innerHTML = current + unitHTML + textSuffix;

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.innerHTML = target + unitHTML + textSuffix;
      }
    }

    requestAnimationFrame(step);
  }

})();
