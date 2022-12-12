/*
 *   Lucas Bubner, 2022
 *   Runs on each action page
 */

// Alerts if the monitor size is from the 1960's (or on mobile)
if (window.innerWidth < 800 || window.innerHeight < 600) {
  alert("This game is best played on a large screen window!");
}

// Disables back button functionality
setTimeout("window.history.forward();", 0);
window.onunload = () => { null };