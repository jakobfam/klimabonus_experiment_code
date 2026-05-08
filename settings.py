"""
oTree project settings — Klimabonus Field Experiment
Goethe-Universität Frankfurt
"""

from os import environ


# ------------------------------------------------------------------ #
# Sessions
# ------------------------------------------------------------------ #

SESSION_CONFIGS = [
    dict(
        name='klimabonus',
        display_name='Klimabonus Informationsportal',
        app_sequence=['klimabonus'],
        num_demo_participants=3,
        # Cookie-banner / consent text variants, treatment numbers etc.
        # can be overridden per session via SessionVars below.
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc=(
        "Informationsseite zum Klimabonus-Förderprogramm der Stadt Frankfurt. "
        "Drei-armiges Feldexperiment (Control, T1 Stadt, T2 Peer). "
        "Treatment-Zuweisung über participant.label-Lookup gegen "
        "klimabonus/data/assignment.csv."
    ),
)


# ------------------------------------------------------------------ #
# Localisation
# ------------------------------------------------------------------ #

LANGUAGE_CODE = 'de'
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False


# ------------------------------------------------------------------ #
# Participant & session-level extra fields
# ------------------------------------------------------------------ #

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []


# ------------------------------------------------------------------ #
# Rooms — participants enter via:
#   /room/klimabonus?participant_label=FIRM_12345
# The room must exist for participant_label URLs to work in oTree.
# ------------------------------------------------------------------ #

ROOMS = [
    dict(
        name='klimabonus',
        display_name='Klimabonus Field Experiment',
        # Custom welcome page auto-submits so participants don't see a
        # "Click to start" gate — they go straight from email link to
        # Landing.html.
        welcome_page='_welcome_pages/RoomWelcomePage.html',
        # No participant_label_file: any label is accepted, validity is
        # checked against assignment.csv inside the app (InvalidLink page
        # for unknown labels).
    ),
]


# ------------------------------------------------------------------ #
# Admin
# ------------------------------------------------------------------ #

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', '')

DEMO_PAGE_INTRO_HTML = """
<p>
Demo-Modus für die Klimabonus-Informationsseite der Goethe-Universität.
Im Live-Betrieb erreichen Teilnehmende die Seite über einen personalisierten
Link mit <code>?participant_label=...</code>.
</p>
"""


# ------------------------------------------------------------------ #
# Security / deployment
# ------------------------------------------------------------------ #

SECRET_KEY = environ.get(
    'OTREE_SECRET_KEY',
    'change-this-in-production-only-for-local-dev',
)

# Heroku sets this; locally falls back to STUDY for dev convenience.
OTREE_PRODUCTION = environ.get('OTREE_PRODUCTION', '0') == '1'
OTREE_AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL', '')  # '', 'STUDY', or 'DEMO'

DEBUG = not OTREE_PRODUCTION


# ------------------------------------------------------------------ #
# Apps
# ------------------------------------------------------------------ #

INSTALLED_APPS = ['otree']
