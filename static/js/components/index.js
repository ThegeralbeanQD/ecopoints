// Score bar animation
const animateScoreBar = () => {
  document.querySelectorAll('.score_bar__progress-bar').forEach(bar => {
    const score = parseFloat(bar.getAttribute('data-score-total')) || 0;
    const percent = (score / 50) * 100;  // 50 is the daily recommended score
    setTimeout(() => {
      bar.style.width = percent + '%';
    }, 1000);  // slight delay so it is seen before the bar animates
  });
};


// Run the function when the DOM is ready
document.addEventListener('DOMContentLoaded', function () {

  // for the score bar
  if (document.querySelector('.score_bar')) {
    animateScoreBar();
  }

  // add more if there are other components that need to be initialised when the DOM is ready
});
