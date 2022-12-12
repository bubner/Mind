/*   
 *   Lucas Bubner, 2022
 *   Runs on every page
 */

function fadeIn() {
    if (!window.AnimationEvent) { return; }
    let fader = document.getElementById('fader');
    fader.classList.add('fade-out');
}

document.addEventListener('DOMContentLoaded', () => {
    if (!window.AnimationEvent) { return; }
    let anchors = document.getElementsByTagName('a');
    for (let i = 0; i < anchors.length; i++) {
        if (anchors[i].hostname !== window.location.hostname ||
            anchors[i].pathname === window.location.pathname) {
            continue;
        }
        anchors[i].addEventListener('click', (e) => {
            let fader = document.getElementById('fader'),
                anchor = e.currentTarget;

            let listener = () => {
                window.location = anchor.href;
                fader.removeEventListener('animationend', listener);
            };
            fader.addEventListener('animationend', listener);

            e.preventDefault();
            fader.classList.add('fade-in');
        });
    }
});

window.addEventListener('pageshow', (e) => {
    if (!e.persisted) {
        return;
    }
    let fader = document.getElementById('fader');
    fader.classList.remove('fade-in');
});
