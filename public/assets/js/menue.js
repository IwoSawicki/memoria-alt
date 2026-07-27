/* Klapp-Menue der Mobilfassung.
   Im Original uebernimmt das Wix' eigenes JavaScript. Hier reicht das
   Noetigste: Schalter umlegen, Flaeche ein- und ausblenden, Seite darunter
   festhalten. Ohne Bibliothek. */
(function () {
    var knopf = document.querySelector('.menue-knopf');
    var menue = document.getElementById('menue');
    if (!knopf || !menue) return;

    function setzen(offen) {
        knopf.setAttribute('aria-expanded', offen ? 'true' : 'false');
        knopf.setAttribute('aria-label',
            offen ? 'Navigationsmenü schließen' : 'Navigationsmenü öffnen');
        menue.hidden = !offen;
        document.body.classList.toggle('menue-offen', offen);
    }

    knopf.addEventListener('click', function () {
        setzen(menue.hidden);
    });

    // Tippen auf die abgedunkelte Flaeche neben dem Menue schliesst es
    menue.addEventListener('click', function (e) {
        if (e.target === menue) setzen(false);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !menue.hidden) setzen(false);
    });
})();
