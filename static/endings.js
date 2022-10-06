/*
 *   Runs on the 'endings.html' page from the '/endings' approute
 *   unlocked and total variables declared in HTML
 */

// Extract the endings unlocked from the unlocked array
// Removes HTML formatting that did not get escaped
let endings = unlocked.split(";");
endings = endings.toString().split("&");
endings = endings.toString().split(",");
let unlockedendings = [];
totalendings = parseInt(totalendings);

// Extract the proper strings
for (let i = 0; i < endings.length; i++) {
    if (endings[i].startsWith("ENDING")) {
        unlockedendings.push(endings[i]);
    }
}

// Display number of unlocked endings
let temp = "";
document.getElementById("endingcount").innerHTML = temp;
document.getElementById("endingcount").innerHTML = "You have unlocked " + unlockedendings.length + "/" + totalendings + " endings. " + temp;

// Get the names of each HTML page ending and link them together
const endinglist = document.querySelectorAll("#endinglist li");
let endingnames = [];
for (let i = 0; i < endinglist.length; i++) {
    endingnames.push(endinglist[i].getAttribute('html'));
}

// Save ending content and clear all of them
let endingcontent = [];
for (let i = 0; i < totalendings; i++) {
    endingcontent[i] = endinglist[i].innerHTML;
    endinglist[i].innerHTML = "???"
}

// Check if an ending has been unlocked and allow it to display if it has
for (let j = 0; j < unlockedendings.length; j++) {
    for (let i = 0; i < totalendings; i++) {
        if (endingnames[i] === unlockedendings[j]) {
            endinglist[i].innerHTML = endingcontent[i];
        }
    }
}
