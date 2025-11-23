// Facebook Watch 2025-Style Video Section Logic
// Autoplay/pause on viewport, like animation, comments expand, smooth scroll

document.addEventListener('DOMContentLoaded', function() {
  // Autoplay/Pause logic
  const videos = document.querySelectorAll('.fbw-video-player');
  const options = { threshold: 0.6 };
  const playVideo = vid => { if (vid.paused) vid.play(); };
  const pauseVideo = vid => { if (!vid.paused) vid.pause(); };
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) playVideo(entry.target);
      else pauseVideo(entry.target);
    });
  }, options);
  videos.forEach(v => observer.observe(v));

  // Like button animation
  document.querySelectorAll('.fbw-like-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      this.classList.toggle('liked');
      this.classList.add('active');
      setTimeout(() => this.classList.remove('active'), 400);
    });
  });

  // Expand/collapse comments
  document.querySelectorAll('.fbw-expand-comments').forEach(btn => {
    btn.addEventListener('click', function() {
      const list = this.parentElement.querySelector('.fbw-comments-list');
      if (list) {
        if (list.style.display === 'none' || !list.style.display) {
          list.style.display = 'block';
          this.textContent = 'Hide Comments';
        } else {
          list.style.display = 'none';
          this.textContent = 'View Comments';
        }
      }
    });
  });

  // Smooth scroll for feed
  document.getElementById('fbwVideoFeed').style.scrollBehavior = 'smooth';
});
