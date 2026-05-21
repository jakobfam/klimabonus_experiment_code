"""
Peer profiles for the T2 (Peer) treatment arm.

There are 6 peer firms in the pool. Each T2 participant is assigned a
peer_id (1-6) in the assignment CSV, based on offline matching by industry
and firm size (done in R/Stata at the time of label generation, NOT in
this app). The Landing template renders the matching peer's profile.

Design note (post-2026-05-16 review): the T2 arm shows the SAME official
Stadt-Frankfurt averages as T1 (96 % / 15 Min / 7.883,75 €). The peer's
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
        name='[Vorname Nachname Firma 1]',
        firma='Firma 1',
        branche='[Branche Firma 1]',
        size_label='[Mitarbeitendenzahl Firma 1]',
        photo=None,         # set to e.g. 'peer_1.jpg' when uploaded
        quote=(
            'Wir hatten den Aufwand über- und den wirtschaftlichen Effekt '
            'unterschätzt. Es war eine gute Entscheidung, den Antrag im '
            'Rahmen des Klimabonus einzureichen. Der Prozess war absolut '
            'frustfrei, direkt und unkompliziert. Kann ich jedem '
            'Unternehmen nur empfehlen.'
        ),
    ),
    2: dict(
        name='[Vorname Nachname Firma 2]',
        firma='Firma 2',
        branche='[Branche Firma 2]',
        size_label='[Mitarbeitendenzahl Firma 2]',
        photo=None,
        quote=(
            'Wir hatten Bedenken wegen der Bürokratie. Im Nachhinein war '
            'der Klimabonus für uns einer der unkompliziertesten '
            'Förderprozesse, mit denen wir bisher zu tun hatten.'
        ),
    ),
    3: dict(
        name='[Vorname Nachname Firma 3]',
        firma='Firma 3',
        branche='[Branche Firma 3]',
        size_label='[Mitarbeitendenzahl Firma 3]',
        photo=None,
        quote=(
            'Was uns überrascht hat: Das Klimareferat war bei '
            'Rückfragen schnell erreichbar und hat uns unkompliziert '
            'weitergeholfen. Klare Empfehlung.'
        ),
    ),
    4: dict(
        name='[Vorname Nachname Firma 4]',
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


def get_peer(peer_id):
    """Return the peer dict for a peer_id (1-6), or None if invalid/unset."""
    try:
        pid = int(peer_id)
    except (TypeError, ValueError):
        return None
    return PEERS.get(pid)
