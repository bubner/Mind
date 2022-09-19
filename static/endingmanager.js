// Runs on the 'endings.html' page from the '/endings' approute
// unlocked variable declared in HTML

// Extract the endings unlocked from the unlocked array
// Removes HTML formatting that was escaped
let endings = unlocked.split(";");
endings = endings.toString().split("&");
endings = endings.toString().split(",");
let unlockedendings = [];

// Extract the proper strings
for (let i = 0; i < endings.length; i++) {
    if (endings[i].startsWith("ENDING")) {
        unlockedendings.push(endings[i]);
    }
}

// Get the names of each HTML page ending and link them together
const endinglist = document.querySelectorAll("#endinglist li");
let endingnames = [];
for (let i = 0; i < endinglist.length; i++) {
    endingnames.push(endinglist[i].getAttribute('html'));
}

// Check if an ending has been unlocked and allow it to display if it has
for (let i = 0; i < endinglist.length; i++) {
    for (let j = 0; j < unlockedendings.length; j++) {
        if (unlockedendings[j] !== endingnames[i]) {
            endinglist[i].innerHTML = "???";
        }
    }
}