"""
Klimabonus Field Experiment — oTree 5.x
Goethe-Universität Frankfurt

Three-arm between-subject design:
  treatment 1 = Control (Grundinfo only)
  treatment 2 = T1 Stadt (Grundinfo + official statistics)
  treatment 3 = T2 Peer  (Grundinfo + peer testimonial)

Assignment is loaded from klimabonus/data/assignment.csv at session creation.
Each row: participant_label, treatment[, stratum, ...optional columns...]
"""

import csv
import os
from otree.api import (
    BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Page, models, ExtraModel,
)

from .peers import PEERS, get_peer


# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

class C(BaseConstants):
    NAME_IN_URL = 'klimabonus'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    TREATMENT_LABELS = {
        1: 'Control',
        2: 'T1_Stadt',
        3: 'T2_Peer',
    }

    ASSIGNMENT_CSV = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'assignment.csv',
    )


# ------------------------------------------------------------------ #
# Models
# ------------------------------------------------------------------ #

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # ---- Treatment & validity ----
    treatment = models.IntegerField(blank=True)  # 1=C, 2=T1, 3=T2
    peer_id = models.IntegerField(blank=True)    # 1-6 for T2; None for C/T1
    label_valid = models.BooleanField(blank=True)
    stratum = models.StringField(blank=True)  # optional, copied from CSV

    # ---- Consent ----
    consent_analytics = models.BooleanField(blank=True)        # cookie-banner click
    consent_analytics_ts = models.FloatField(blank=True)
    consent_research = models.BooleanField(blank=True)         # research participation, before survey
    consent_research_ts = models.FloatField(blank=True)
    consent_contact = models.BooleanField(blank=True)          # final-page contact consent
    consent_contact_ts = models.FloatField(blank=True)

    # ---- Page-level engagement (passive, JS) ----
    # Landing is the merged information+treatment page; remaining pages
    # are the post-treatment outcome/belief/commitment/finish flow.
    time_landing = models.FloatField(blank=True)
    time_outcomes = models.FloatField(blank=True)
    time_beliefs = models.FloatField(blank=True)
    time_commitment = models.FloatField(blank=True)
    time_abschluss = models.FloatField(blank=True)

    scroll_landing = models.IntegerField(blank=True)

    # Did the user expand the "So läuft der Antrag" accordion? (JS-tracked)
    expanded_process = models.BooleanField(blank=True, initial=False)

    # 2-min survey-prompt modal on Landing (shows after long passive read).
    prompt_shown_ts = models.FloatField(blank=True)
    prompt_used = models.BooleanField(blank=True, initial=False)
    prompt_dismissed_ts = models.FloatField(blank=True)

    # ---- Drop-off tracking ----
    page_reached = models.IntegerField(initial=0)
    completed = models.BooleanField(initial=False)

    # ---- Outcome 1: stated application likelihood ----
    application_likelihood = models.IntegerField(min=0, max=10)

    # ---- Outcome 2: relevant measures ----
    # Categories mirror the 7 funding-table rows on Landing exactly.
    measure_solar = models.BooleanField(blank=True, initial=False)             # PV / Solarthermie
    measure_solar_green_roof = models.BooleanField(blank=True, initial=False)  # Solar-Gründächer
    measure_battery = models.BooleanField(blank=True, initial=False)           # Batteriespeicher (mit neuer PV)
    measure_charging = models.BooleanField(blank=True, initial=False)          # Ladesäulen
    measure_greening = models.BooleanField(blank=True, initial=False)          # Dach-/Fassaden-/Hofbegrünung
    measure_rainwater = models.BooleanField(blank=True, initial=False)         # Regenwasserspeicher
    measure_drinking_fountain = models.BooleanField(blank=True, initial=False) # Trinkbrunnen
    measure_already_done = models.BooleanField(blank=True, initial=False)      # bereits ähnliche Maßnahmen umgesetzt
    measure_other = models.BooleanField(blank=True, initial=False)             # Sonstiges (mit Freitext)
    measure_other_text = models.StringField(blank=True)
    measure_none = models.BooleanField(blank=True, initial=False)

    # Randomized display order of measure checkboxes (comma-separated keys)
    measures_order = models.StringField(blank=True)

    # ---- Outcome 3: barriers ----
    barrier_time = models.BooleanField(blank=True, initial=False)
    barrier_complexity = models.BooleanField(blank=True, initial=False)
    barrier_uncertainty = models.BooleanField(blank=True, initial=False)
    barrier_amount = models.BooleanField(blank=True, initial=False)
    barrier_property = models.BooleanField(blank=True, initial=False)
    barrier_priority = models.BooleanField(blank=True, initial=False)
    barrier_already_applied = models.BooleanField(blank=True, initial=False)  # Fördermittel bereits beantragt / genutzt
    barrier_other = models.BooleanField(blank=True, initial=False)
    barrier_other_text = models.StringField(blank=True)
    barriers_order = models.StringField(blank=True)

    # ---- Beliefs (post-treatment) ----
    belief_approval_rate = models.IntegerField(min=0, max=100)
    belief_processing_time = models.IntegerField(
        choices=[
            [1, 'Weniger als 2 Wochen'],
            [2, '2–4 Wochen'],
            [3, '1–3 Monate'],
            [4, '3–6 Monate'],
            [5, 'Mehr als 6 Monate'],
        ],
    )
    belief_effort = models.IntegerField(
        choices=[
            [1, 'Weniger als 30 Minuten'],
            [2, '30 Minuten bis 1 Stunde'],
            [3, '1–3 Stunden'],
            [4, '3–8 Stunden'],
            [5, 'Mehr als 1 Arbeitstag'],
        ],
    )
    belief_payout_effort = models.IntegerField(
        choices=[
            [1, 'Weniger als 30 Minuten'],
            [2, '30 Minuten bis 1 Stunde'],
            [3, '1–3 Stunden'],
            [4, '3–8 Stunden'],
            [5, 'Mehr als 1 Arbeitstag'],
        ],
        label='Bürokratischer Aufwand nach Bewilligung (Nachweise, Auszahlungsantrag)',
    )

    # ---- Respondent role (covariate) ----
    respondent_position = models.StringField(
        blank=True,
        choices=[
            ['gf',          'Geschäftsführung / Inhaber:in'],
            ['leitung',     'Bereichs- / Abteilungsleitung'],
            ['kfm',         'Kaufmännische Leitung / Verwaltung'],
            ['tech',        'Technische Leitung / Energiebeauftragte:r'],
            ['mitarbeiter', 'Mitarbeiter:in'],
            ['sonstiges',   'Sonstige Position'],
        ],
    )
    respondent_position_other = models.StringField(blank=True)

    # ---- Commitment ladder (revealed actions) ----
    wants_email = models.BooleanField(
        choices=[[True, 'Ja, gerne'], [False, 'Nein, danke']],
    )
    email_address = models.StringField(blank=True)

    wants_event = models.BooleanField(
        choices=[[True, 'Ja, gerne'], [False, 'Nein, danke']],
    )

    wants_callback = models.BooleanField(
        choices=[[True, 'Ja, gerne'], [False, 'Nein, danke']],
    )
    phone_number = models.StringField(blank=True)

    # ---- Revealed action: click on Antragsportal ----
    # Two separate trackers: the direct-CTA on Landing (fast path, before
    # survey) vs. the post-survey CTA on Abschluss (slow path).
    clicked_portal_landing = models.BooleanField(blank=True, initial=False)
    clicked_portal_landing_ts = models.FloatField(blank=True)

    clicked_application_portal = models.BooleanField(blank=True, initial=False)
    clicked_application_portal_ts = models.FloatField(blank=True)

    # ---- Final free-text feedback (Abschluss page) ----
    feedback_subsidies = models.LongStringField(blank=True)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def load_assignment():
    """Read assignment.csv into a dict: label -> {treatment, stratum, peer_id}.

    Required columns: participant_label, treatment.
    Optional columns: stratum, peer_id.
    peer_id (1-6) is only meaningful for treatment=3 (T2 Peer arm) and is
    determined offline by industry/size matching at letter generation time.
    """
    if not os.path.exists(C.ASSIGNMENT_CSV):
        return {}
    out = {}
    with open(C.ASSIGNMENT_CSV, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get('participant_label') or '').strip()
            if not label:
                continue
            try:
                t = int(row.get('treatment', '').strip())
            except (ValueError, AttributeError):
                continue
            if t not in (1, 2, 3):
                continue
            peer_raw = (row.get('peer_id') or '').strip()
            try:
                peer = int(peer_raw) if peer_raw else None
            except ValueError:
                peer = None
            out[label] = {
                'treatment': t,
                'stratum': (row.get('stratum') or '').strip(),
                'peer_id': peer,
            }
    return out


def assign_player_from_label(player: Player):
    """Look up participant.label in the assignment CSV. Set treatment + peer + validity."""
    if player.field_maybe_none('label_valid') is not None:
        return  # already assigned
    label = player.participant.label
    assignment = player.session.vars.get('assignment', {})
    if label and label in assignment:
        row = assignment[label]
        player.treatment = row['treatment']
        player.stratum = row.get('stratum', '')
        if row['treatment'] == 3 and row.get('peer_id') in PEERS:
            player.peer_id = row['peer_id']
        player.label_valid = True
    else:
        player.label_valid = False


def creating_session(subsession: Subsession):
    subsession.session.vars['assignment'] = load_assignment()


# ------------------------------------------------------------------ #
# Pages
# ------------------------------------------------------------------ #

class InvalidLink(Page):
    """Shown only when participant.label is missing or unknown."""
    @staticmethod
    def is_displayed(player: Player):
        assign_player_from_label(player)
        return player.field_maybe_none('label_valid') is False


class Landing(Page):
    """
    Merged information + treatment page. The treatment variation is shown
    immediately on the visitor's first content page (above-the-fold), so
    the manipulation gets maximum salience and pre-treatment exposure is
    minimised.
    """
    form_model = 'player'
    # NOTE: only the two passive fields are saved via form submit.
    # All click / consent / accordion events go through live_method below
    # so they persist immediately even if the participant never submits
    # the Landing page (e.g. clicks "Direkt zum Antrag" and never comes
    # back). Putting them in form_fields would risk overwriting the
    # live-saved values with empty defaults on form submit.
    form_fields = [
        'time_landing', 'scroll_landing',
    ]

    @staticmethod
    def is_displayed(player: Player):
        assign_player_from_label(player)
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def live_method(player: Player, data):
        """Receive fire-and-forget click events from the Landing page.

        Expected payload from JS liveSend(): { event: <str>, ts: <float>,
        value?: <bool> }. Events handled:
          - 'consent_analytics'  → consent_analytics + ts
              (data.value carries True for accept, False for decline)
          - 'portal_click'       → clicked_portal_landing + ts
          - 'process_expand'     → expanded_process = True
          - 'prompt_shown'       → prompt_shown_ts (2-min survey-prompt
              modal appeared)
          - 'prompt_dismissed'   → prompt_dismissed_ts (user closed modal
              without clicking the CTA inside it)
          - 'prompt_used'        → prompt_used = True (user clicked the
              CTA inside the modal — fires just before form submit)
        Returns empty dict (no client-side response needed).
        """
        event = (data or {}).get('event')
        ts = (data or {}).get('ts')
        try:
            ts = float(ts) if ts is not None else None
        except (TypeError, ValueError):
            ts = None

        if event == 'consent_analytics':
            player.consent_analytics = bool(data.get('value'))
            if ts is not None:
                player.consent_analytics_ts = ts
        elif event == 'portal_click':
            player.clicked_portal_landing = True
            if ts is not None:
                player.clicked_portal_landing_ts = ts
        elif event == 'process_expand':
            player.expanded_process = True
        elif event == 'prompt_shown':
            if ts is not None:
                player.prompt_shown_ts = ts
        elif event == 'prompt_dismissed':
            if ts is not None:
                player.prompt_dismissed_ts = ts
        elif event == 'prompt_used':
            player.prompt_used = True
        return {}

    @staticmethod
    def vars_for_template(player: Player):
        t = player.field_maybe_none('treatment')
        peer = get_peer(player.field_maybe_none('peer_id')) if t == 3 else None
        return dict(
            participant_label=player.participant.label or '',
            treatment=t,
            is_control=(t == 1),
            is_t1=(t == 2),
            is_t2=(t == 3),
            peer=peer,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.page_reached = max(player.page_reached or 0, 1)


class Outcomes(Page):
    form_model = 'player'
    form_fields = [
        'consent_research', 'consent_research_ts',
        'application_likelihood',
        'measure_solar', 'measure_solar_green_roof', 'measure_battery',
        'measure_greening',
        'measure_rainwater', 'measure_drinking_fountain',
        'measure_already_done',
        'measure_other', 'measure_other_text',
        'measure_none',
        'barrier_time', 'barrier_complexity', 'barrier_uncertainty',
        'barrier_amount', 'barrier_property', 'barrier_priority',
        'barrier_already_applied',
        'barrier_other', 'barrier_other_text',
        'measures_order', 'barriers_order',
        'time_outcomes',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('consent_research'):
            return ('Bitte bestätigen Sie Ihre Einwilligung zur '
                    'Teilnahme an der Studie, um fortzufahren.')

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.page_reached = max(player.page_reached or 0, 2)


class Beliefs(Page):
    form_model = 'player'
    form_fields = [
        'belief_approval_rate', 'belief_processing_time',
        'belief_effort', 'belief_payout_effort',
        'time_beliefs',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.page_reached = max(player.page_reached or 0, 3)


class Commitment(Page):
    form_model = 'player'
    form_fields = [
        'respondent_position', 'respondent_position_other',
        'wants_email', 'email_address',
        'wants_event',
        'wants_callback', 'phone_number',
        'consent_contact', 'consent_contact_ts',
        'time_commitment',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def error_message(player: Player, values):
        email = (values.get('email_address') or '').strip()
        if values.get('wants_email') and not email:
            return 'Bitte geben Sie eine E-Mail-Adresse an oder wählen Sie "Nein, danke".'
        # Event invitation also requires an email address — independent of
        # whether the participant said "Ja" to the email summary above.
        if values.get('wants_event') and not email:
            return ('Damit wir Sie zur Informationsveranstaltung einladen '
                    'können, benötigen wir Ihre E-Mail-Adresse.')
        if values.get('wants_callback') and not (values.get('phone_number') or '').strip():
            return 'Bitte geben Sie eine Telefonnummer an oder wählen Sie "Nein, danke".'

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.page_reached = max(player.page_reached or 0, 4)


class Abschluss(Page):
    form_model = 'player'
    form_fields = [
        'feedback_subsidies',
        'clicked_application_portal', 'clicked_application_portal_ts',
        'time_abschluss',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.page_reached = max(player.page_reached or 0, 5)
        player.completed = True


class EndPage(Page):
    """Final page after Abschluss: re-displays the same information as
    Landing (treatment block included), but without the survey CTA, the
    cookie banner, or the Vorab-Hinweis. Lets participants re-read the
    treatment-relevant information for as long as they want.
    No form, no further submission."""

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def vars_for_template(player: Player):
        t = player.field_maybe_none('treatment')
        peer = get_peer(player.field_maybe_none('peer_id')) if t == 3 else None
        return dict(
            treatment=t,
            is_control=(t == 1),
            is_t1=(t == 2),
            is_t2=(t == 3),
            peer=peer,
        )


page_sequence = [
    InvalidLink,
    Landing,
    Outcomes,
    Beliefs,
    Commitment,
    Abschluss,
    EndPage,
]


# ------------------------------------------------------------------ #
# Custom export — flat one-row-per-player CSV with everything
# ------------------------------------------------------------------ #

def custom_export(players):
    yield [
        'session_code', 'participant_code', 'participant_label',
        'treatment', 'treatment_label', 'peer_id', 'stratum', 'label_valid',
        'consent_analytics', 'consent_analytics_ts',
        'consent_research', 'consent_research_ts',
        'consent_contact', 'consent_contact_ts',
        'page_reached', 'completed',
        'time_landing', 'time_outcomes', 'time_beliefs',
        'time_commitment', 'time_abschluss',
        'scroll_landing', 'expanded_process',
        'prompt_shown_ts', 'prompt_used', 'prompt_dismissed_ts',
        'application_likelihood',
        'measure_solar', 'measure_solar_green_roof', 'measure_battery',
        'measure_greening',
        'measure_rainwater', 'measure_drinking_fountain',
        'measure_already_done', 'measure_other', 'measure_other_text',
        'measure_none', 'measures_order',
        'barrier_time', 'barrier_complexity', 'barrier_uncertainty',
        'barrier_amount', 'barrier_property', 'barrier_priority',
        'barrier_already_applied',
        'barrier_other', 'barrier_other_text', 'barriers_order',
        'belief_approval_rate', 'belief_processing_time',
        'belief_effort', 'belief_payout_effort',
        'respondent_position', 'respondent_position_other',
        'wants_email', 'email_address',
        'wants_event',
        'wants_callback', 'phone_number',
        'feedback_subsidies',
        'clicked_portal_landing', 'clicked_portal_landing_ts',
        'clicked_application_portal', 'clicked_application_portal_ts',
    ]
    for p in players:
        t = p.field_maybe_none('treatment')
        yield [
            p.session.code, p.participant.code, p.participant.label or '',
            t, C.TREATMENT_LABELS.get(t, ''),
            p.field_maybe_none('peer_id') or '',
            p.field_maybe_none('stratum') or '',
            p.field_maybe_none('label_valid'),
            p.field_maybe_none('consent_analytics'),
            p.field_maybe_none('consent_analytics_ts'),
            p.field_maybe_none('consent_research'),
            p.field_maybe_none('consent_research_ts'),
            p.field_maybe_none('consent_contact'),
            p.field_maybe_none('consent_contact_ts'),
            p.page_reached, p.completed,
            p.field_maybe_none('time_landing'),
            p.field_maybe_none('time_outcomes'),
            p.field_maybe_none('time_beliefs'),
            p.field_maybe_none('time_commitment'),
            p.field_maybe_none('time_abschluss'),
            p.field_maybe_none('scroll_landing'),
            p.field_maybe_none('expanded_process'),
            p.field_maybe_none('prompt_shown_ts'),
            p.field_maybe_none('prompt_used'),
            p.field_maybe_none('prompt_dismissed_ts'),
            p.field_maybe_none('application_likelihood'),
            p.measure_solar, p.measure_solar_green_roof, p.measure_battery,
            p.measure_greening,
            p.measure_rainwater, p.measure_drinking_fountain,
            p.measure_already_done, p.measure_other,
            p.field_maybe_none('measure_other_text') or '',
            p.measure_none,
            p.field_maybe_none('measures_order') or '',
            p.barrier_time, p.barrier_complexity, p.barrier_uncertainty,
            p.barrier_amount, p.barrier_property, p.barrier_priority,
            p.barrier_already_applied,
            p.barrier_other,
            p.field_maybe_none('barrier_other_text') or '',
            p.field_maybe_none('barriers_order') or '',
            p.field_maybe_none('belief_approval_rate'),
            p.field_maybe_none('belief_processing_time'),
            p.field_maybe_none('belief_effort'),
            p.field_maybe_none('belief_payout_effort'),
            p.field_maybe_none('respondent_position') or '',
            p.field_maybe_none('respondent_position_other') or '',
            p.field_maybe_none('wants_email'),
            p.field_maybe_none('email_address') or '',
            p.field_maybe_none('wants_event'),
            p.field_maybe_none('wants_callback'),
            p.field_maybe_none('phone_number') or '',
            p.field_maybe_none('feedback_subsidies') or '',
            p.clicked_portal_landing,
            p.field_maybe_none('clicked_portal_landing_ts'),
            p.clicked_application_portal,
            p.field_maybe_none('clicked_application_portal_ts'),
        ]


# ------------------------------------------------------------------ #
# live_method endpoints — receive JS beacons (consent click, portal click)
# ------------------------------------------------------------------ #

# We use Page.live_method below per page where needed. For consent and
# portal-click we'll POST via fetch() to a lightweight endpoint defined
# inline on each page that accepts these signals. Implementation detail
# kept in templates + before_next_page hooks.
