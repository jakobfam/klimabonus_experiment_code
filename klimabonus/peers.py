"""
Peer profiles for the T2 (Peer) treatment arm.

There are 6 peer firms in the pool. Each T2 participant is assigned a
peer_id (1-6) in the assignment CSV, based on offline matching by industry
and firm size (done in R/Stata at the time of label generation, NOT in
this app). The Landing template renders the matching peer's profile.

Design note (post-2026-05-16 review): the T2 arm shows the SAME official
Stadt-Frankfurt averages as T1 (96 % / 15 Min / 8.776,97 €). The peer's
role is to ADD a personal testimonial — a face + a short qualitative
experience report — that humanises the same numerical facts. The peer
quotes should therefore NOT contradict the city averages with their own
numbers; they should add colour, context, or narrative.

ALL CONTENT IN THIS FILE IS PLACEHOLDER ("Firma 1" through "Firma 6")
and must be replaced with real peer content before fielding:
- name, firma, branche, size_label, photo: real peer firm data
- quote: real peer testimonial (qualitative, ideally in the peer's own
  words). Each peer should have a slightly different angle so the
  within-T2 variation is natural.
"""

PEERS = {
    1: dict(
        # Nassauische Heimstätte — eines der größten Wohnungsunternehmen
        # in Hessen. Direktive Jakob 2026-06-08: Zitat wird NICHT einer
        # Person zugeordnet, nur dem Unternehmen. name + position daher
        # explizit None → Template rendert sie konditional aus.
        name=None,
        position=None,
        firma='Nassauische Heimstätte',
        branche='Wohnungswirtschaft',
        size_label='Großunternehmen',
        photo='klimabonus/peer_1.png',  # Logo (PNG mit transparentem Hintergrund)
        photo_fit='contain',  # Logo nicht croppen
        quote=(
            'Es war eine gute Entscheidung, den Antrag für den '
            'Klimabonus einzureichen. Es war weniger aufwendig und hat '
            'uns mehr gebracht als gedacht. Der Prozess war direkt, '
            'unkompliziert und ohne Frust.'
        ),
    ),
    2: dict(
        # Carl Friederichs GmbH — Karosseriebau / Lackierzentrum,
        # Standort Frankfurt. Real-content befüllt 2026-06-08.
        name='Christian Tuscher',
        position='CFO',
        firma='Carl Friederichs GmbH',
        branche='Fahrzeugbau',
        size_label='Mittelständisches Unternehmen',  # Direktive Jakob 2026-06-08: "Mittel"
        photo='klimabonus/peer_2.jpg',  # Luftaufnahme Standort Frankfurt (230408_FRIEDERICHS_LA)
        quote=(
            'Es war eine gute Entscheidung, den Antrag für den '
            'Klimabonus einzureichen. Es war weniger aufwendig und hat '
            'uns mehr gebracht als gedacht. Der Prozess war direkt, '
            'unkompliziert und reibungslos. Kann ich jedem Unternehmen '
            'nur empfehlen.'
        ),
    ),
    3: dict(
        name='[Vorname Nachname Firma 3]',
        position='Geschäftsführung',
        firma='Firma 3',
        branche='[Branche Firma 3]',
        size_label='[Mitarbeitendenzahl Firma 3]',
        # WICHTIG: photo muss den 'klimabonus/'-Prefix enthalten, z.B.
        # 'klimabonus/peer_3.jpg' — oTree 6 {% static %} validiert
        # strict, daher Pfad als-Ganzes übergeben, nicht im Template
        # concat'en.
        photo=None,
        quote=(
            'Was uns überrascht hat: Das Klimareferat war bei '
            'Rückfragen schnell erreichbar und hat uns unkompliziert '
            'weitergeholfen. Klare Empfehlung.'
        ),
    ),
    4: dict(
        name='[Vorname Nachname Firma 4]',
        position='Geschäftsführung',
        firma='Firma 4',
        branche='[Branche Firma 4]',
        size_label='[Mitarbeitendenzahl Firma 4]',
        photo=None,
        quote=(
            'Wir hatten die Förderung gar nicht auf dem Schirm. Mit dem '
            'Klimabonus konnten wir unsere Maßnahme deutlich schneller '
            'umsetzen als ursprünglich geplant.'
        ),
    ),
    5: dict(
        name='[Vorname Nachname Firma 5]',
        position='Geschäftsführung',
        firma='Firma 5',
        branche='[Branche Firma 5]',
        size_label='[Mitarbeitendenzahl Firma 5]',
        photo=None,
        quote=(
            'Die Förderung hat für uns den entscheidenden Anstoß '
            'gegeben, mit der Maßnahme jetzt zu starten – und nicht '
            'erst in ein paar Jahren.'
        ),
    ),
    6: dict(
        name='[Vorname Nachname Firma 6]',
        position='Geschäftsführung',
        firma='Firma 6',
        branche='[Branche Firma 6]',
        size_label='[Mitarbeitendenzahl Firma 6]',
        photo=None,
        quote=(
            'Was uns positiv überrascht hat: Der gesamte Ablauf läuft '
            'online und ist klar strukturiert. Wer den Antrag einmal '
            'beim Mittagessen ausfüllt, ist fertig.'
        ),
    ),
}


_PEER_DEFAULTS = {
    'position': 'Geschäftsführung',
    # Wie das Foto in den 240×160-Slot eingepasst wird:
    #   'cover'   = füllt frame, croppt überschüssiges (gut für
    #               Building-Wide-Shots, Porträts)
    #   'contain' = passt komplett rein, evtl. mit Whitespace
    #               (gut für Logos mit Transparenz)
    'photo_fit': 'cover',
}


def get_peer(peer_id):
    """Return the peer dict for a peer_id (1-6), or None if invalid/unset.

    Merges _PEER_DEFAULTS so the Landing/EndPage templates can render
    {{ peer.position }} unconditionally even if a peer dict in PEERS
    forgot to set it. oTree's template engine doesn't accept the
    `default:"..."` filter argument syntax, so we resolve defaults here
    on the Python side.
    """
    try:
        pid = int(peer_id)
    except (TypeError, ValueError):
        return None
    raw = PEERS.get(pid)
    if raw is None:
        return None
    return {**_PEER_DEFAULTS, **raw}
