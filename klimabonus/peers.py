"""
Peer profiles for the T2 (Peer) treatment arm.

There are 6 peer firms in the pool. Each T2 participant is assigned a
peer_id (1-6) in the assignment CSV, based on offline matching by industry
and firm size (done in R/Stata at the time of label generation, NOT in
this app). The Landing template renders the matching peer's profile.

ALL CONTENT IN THIS FILE IS PLACEHOLDER ("Firma 1" through "Firma 6")
and must be replaced with the real peer firm content before fielding:
- name, firma, branche, size_label, photo, quote: real peer data
- time_minutes, amount_eur: each peer's actually reported numbers

The numbers below are PROXIES that bracket the T1 city averages
(20 Min, 8.500 €) with realistic spread, so the prototype renders
cleanly. They will be replaced with the real reported values before
fielding.
"""

PEERS = {
    1: dict(
        name='[Vorname Nachname Firma 1]',
        firma='Firma 1',
        branche='[Branche Firma 1]',
        size_label='[Mitarbeitendenzahl Firma 1]',
        photo=None,         # set to e.g. 'peer_1.jpg' when uploaded
        quote=(
            'Bei uns hat das Ausfüllen des Antrags rund 22 Minuten '
            'gedauert. Am Ende haben wir 8.400 Euro Förderung erhalten – '
            'unkompliziert, wie wir das nicht erwartet hätten.'
        ),
        time_minutes=22,
        amount_eur=8400,
    ),
    2: dict(
        name='[Vorname Nachname Firma 2]',
        firma='Firma 2',
        branche='[Branche Firma 2]',
        size_label='[Mitarbeitendenzahl Firma 2]',
        photo=None,
        quote=(
            'Wir haben für unsere PV-Anlage etwa eine halbe Stunde in den '
            'Antrag investiert. 11.200 Euro vom Klimabonus haben sich '
            'definitiv gelohnt.'
        ),
        time_minutes=28,
        amount_eur=11200,
    ),
    3: dict(
        name='[Vorname Nachname Firma 3]',
        firma='Firma 3',
        branche='[Branche Firma 3]',
        size_label='[Mitarbeitendenzahl Firma 3]',
        photo=None,
        quote=(
            'Den Antrag hatte ich in unter 20 Minuten online ausgefüllt. '
            'Nach wenigen Wochen kam der Bescheid – 12.800 Euro für '
            'unser Projekt.'
        ),
        time_minutes=19,
        amount_eur=12800,
    ),
    4: dict(
        name='[Vorname Nachname Firma 4]',
        firma='Firma 4',
        branche='[Branche Firma 4]',
        size_label='[Mitarbeitendenzahl Firma 4]',
        photo=None,
        quote=(
            'Wir haben rund 25 Minuten für den Antrag gebraucht und '
            '9.500 Euro Förderung bekommen. Hat genauso geklappt, wie '
            'es auf der Webseite beschrieben war.'
        ),
        time_minutes=25,
        amount_eur=9500,
    ),
    5: dict(
        name='[Vorname Nachname Firma 5]',
        firma='Firma 5',
        branche='[Branche Firma 5]',
        size_label='[Mitarbeitendenzahl Firma 5]',
        photo=None,
        quote=(
            'Mit etwa einer halben Stunde Aufwand für den Antrag haben '
            'wir 13.500 Euro für unser Vorhaben erhalten – ein klar '
            'kalkulierbarer Schritt für uns.'
        ),
        time_minutes=30,
        amount_eur=13500,
    ),
    6: dict(
        name='[Vorname Nachname Firma 6]',
        firma='Firma 6',
        branche='[Branche Firma 6]',
        size_label='[Mitarbeitendenzahl Firma 6]',
        photo=None,
        quote=(
            'Der Antrag war in gut 20 Minuten erledigt. 7.500 Euro '
            'Förderung – damit haben wir nicht gerechnet, dass es so '
            'einfach geht.'
        ),
        time_minutes=21,
        amount_eur=7500,
    ),
}


def get_peer(peer_id):
    """Return the peer dict for a peer_id (1-6), or None if invalid/unset."""
    try:
        pid = int(peer_id)
    except (TypeError, ValueError):
        return None
    return PEERS.get(pid)
