/*
 *   Runs on each action page
 */

// Alerts if the monitor size is from the 1960's
if (window.innerWidth < 800 || window.innerHeight < 600) {
  alert("This game is best played on a large screen window!")
}

// Disables back button functionality
function disableBack() { window.history.forward(); }
setTimeout("disableBack();", 0);
window.onunload = () => { null };