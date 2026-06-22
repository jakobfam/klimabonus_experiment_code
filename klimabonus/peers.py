"""
Peer profiles for the T2 (Peer) treatment arm.

There are exactly 4 peer firms in the pool — one per firm-size class.
Each T2 participant is assigned a peer_id (1-4) in the assignment CSV,
based on offline size matching (done in R/Stata at the time of label
generation, NOT in this app):

    peer_id 1 → Nassauische Heimstätte (Wohnungswirtschaft, GROSS)
    peer_id 2 → Carl Friederichs GmbH  (Fahrzeugbau,        MITTEL)
    peer_id 3 → Wilhelm Roth GmbH      (Handwerk,           KLEIN)
    peer_id 4 → Expertenspot GmbH      (Dienstleister,      KLEINST, <10 MA)

The Landing template renders the matching peer's profile.

Design note (post-2026-05-16 review): the T2 arm shows the SAME official
Stadt-Frankfurt averages as T1 (96 % / ca. 25 Min / 8.776,97 €). The peer's
role is to ADD a personal testimonial — a face + a short qualitative
experience report — that humanises the same numerical facts. The peer
quotes should therefore NOT contradict the city averages with their own
numbers; they should add colour, context, or narrative.

IMPORTANT: the assignment CSV must only ever use peer_id in {1, 2, 3, 4}.
Any other value is rejected at load time (see load_assignment in
__init__.py) so a mis-coded T2 row can never silently degrade to a
control-like page.
"""

# Single source of truth for how many peers exist. Used for validation
# in __init__.load_assignment().
VALID_PEER_IDS = (1, 2, 3, 4)

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
        # Wilhelm Roth GmbH (Handwerk, klein). Real-content befüllt
        # 2026-06-08. Logo: roth.jpg liegt im static folder.
        name='Jens Hackbarth',
        position='Geschäftsführer',
        firma='Wilhelm Roth GmbH',
        branche='Handwerk',
        size_label='Kleinunternehmen',
        photo='klimabonus/roth.jpeg',
        photo_fit='contain',  # Logo nicht croppen (Roth Dachdecker)
        quote=(
            'Es war eine gute Entscheidung, den Antrag für den '
            'Klimabonus einzureichen. Es war weniger aufwendig und hat '
            'uns mehr gebracht als gedacht. Der Prozess war direkt, '
            'unkompliziert und ohne Frust. Kann ich jedem Unternehmen '
            'nur empfehlen.'
        ),
    ),
    4: dict(
        # Expertenspot GmbH (Dienstleister, KLEINST <10 MA).
        # Real-content befüllt 2026-06-22.
        name='Olaf Peukert',
        position='Geschäftsführer',
        firma='Expertenspot GmbH',
        branche='Dienstleister',
        size_label='Kleinstunternehmen',
        photo='klimabonus/peer_4.jpg',
        photo_fit='contain',  # Logo nicht croppen (Expertenspot)
        quote=(
            'Es war eine gute Entscheidung, den Antrag für den '
            'Klimabonus einzureichen. Es war weniger aufwendig und hat '
            'uns mehr gebracht als gedacht. Der Prozess war direkt, '
            'unkompliziert und ohne Frust. Kann ich jedem Unternehmen '
            'nur empfehlen.'
        ),
    ),
    # NOTE: Falls später weitere Peers dazukommen: hier ergänzen UND
    # peers.VALID_PEER_IDS oben erweitern.
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
    """Return the peer dict for a peer_id (1-4), or None if invalid/unset.

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
