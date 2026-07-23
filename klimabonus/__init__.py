"""
Klimabonus Field Experiment — oTree 5.x
Goethe-Universität Frankfurt

Three-arm between-subject design:
  treatment 1 = Control (Grundinfo only)
  treatment 2 = T1 Stadt (Grundinfo + official statistics)
  treatment 3 = T2 Peer  (Grundinfo + peer testimonial)

Assignment is loaded at session creation from the first existing file in
klimabonus/data/ (C.ASSIGNMENT_FILES): frakeys.xlsx | frakeys.csv |
assignment.csv. The frakey delivery (columns frakey | strata | treat) can
be dropped in AS-IS — pure-control rows are ignored and the T2 peer_id is
derived from the stratum. See load_assignment() for the full mapping.
"""

import csv
import os
from otree.api import (
    BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Page, models, ExtraModel,
)

from .peers import PEERS, get_peer, VALID_PEER_IDS, STRATUM_TO_PEER


# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

class C(BaseConstants):
    NAME_IN_URL = 'klimabonus'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    # Treatment 1 = der KONTAKTIERTE Baseline-Arm (generische Landing-Page).
    # NICHT zu verwechseln mit der Pure Control (Elisas "Control"-Gruppe),
    # die gar keinen Link bekommt und NIE in dieser App auftaucht — die
    # lebt nur in den Admin-Daten. Daher Label 'Baseline', damit der
    # Export nicht mit der Pure Control kollidiert (Direktive 2026-06-25).
    TREATMENT_LABELS = {
        1: 'Baseline',
        2: 'T1_Stadt',
        3: 'T2_Peer',
    }

    # Zuteilungsdatei liegt in klimabonus/data/. NUR CSV — bewusst kein
    # xlsx in Produktion (Direktive 2026-06-25: möglichst fehlerarm; CSV
    # via stdlib ist bombensicher, xlsx-Parsing wäre fragil). Die
    # frakeys.xlsx-Lieferung wird LOKAL mit tools/build_assignment.py
    # validiert und nach frakeys.csv konvertiert — der Converter fängt
    # Datenfehler ab, bevor irgendetwas live geht.
    # Erste existierende Datei gewinnt.
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    ASSIGNMENT_FILES = ('frakeys.csv', 'assignment.csv')


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
    peer_id = models.IntegerField(blank=True)    # 1-4 for T2; None for C/T1
    label_valid = models.BooleanField(blank=True)
    stratum = models.StringField(blank=True)  # optional, copied from CSV

    # ---- Consent ----
    # consent_analytics / _ts: deprecated 2026-06-19. Cookie-Banner
    # entfernt; Consent erfolgt durch Link-Klick aus dem Anschreiben.
    # Felder bleiben aus Backward-Compat in der DB, werden aber nicht
    # mehr gesetzt.
    consent_analytics = models.BooleanField(blank=True)
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
    measure_battery = models.BooleanField(blank=True, initial=False)           # Batteriespeicher (mit neuer Solaranlage)
    measure_charging = models.BooleanField(blank=True, initial=False)          # Ladesäulen
    measure_greening = models.BooleanField(blank=True, initial=False)          # Dach-/Fassaden-/Hofbegrünung
    measure_rainwater = models.BooleanField(blank=True, initial=False)         # Regenwasserspeicher
    measure_drinking_fountain = models.BooleanField(blank=True, initial=False) # Trinkbrunnen
    measure_other = models.BooleanField(blank=True, initial=False)             # Sonstiges (mit Freitext)
    measure_other_text = models.StringField(blank=True)
    measure_none = models.BooleanField(blank=True, initial=False)

    # Randomized display order of measure checkboxes (comma-separated keys)
    measures_order = models.StringField(blank=True)

    # ---- Vorab-Screening (B-Cluster, pre-treatment) ----
    # "Hat Ihr Unternehmen bereits eine ähnliche Maßnahme umgesetzt?" — moved
    # out of the planned-measures checklist and into its own screening
    # question (was: measure_already_done, removed). Ja/Nein.
    screening_similar_done = models.BooleanField(
        blank=True,
        choices=[[True, 'Ja'], [False, 'Nein']],
    )

    # ---- Outcome 3: barriers ----
    barrier_time = models.BooleanField(blank=True, initial=False)
    barrier_complexity = models.BooleanField(blank=True, initial=False)
    barrier_uncertainty = models.BooleanField(blank=True, initial=False)
    barrier_amount = models.BooleanField(blank=True, initial=False)
    barrier_property = models.BooleanField(blank=True, initial=False)
    barrier_priority = models.BooleanField(blank=True, initial=False)
    barrier_already_applied = models.BooleanField(blank=True, initial=False)  # Fördermittel bereits beantragt / genutzt
    # New C2a-d barriers (Klimareferat / Madeline feedback):
    barrier_funding_liquidity = models.BooleanField(blank=True, initial=False)  # C2a Vorfinanzierung / Liquidität
    barrier_internal_capacity = models.BooleanField(blank=True, initial=False)  # C2b Personalkapazität intern
    barrier_owner_tenant      = models.BooleanField(blank=True, initial=False)  # C2c Eigentums-/Mietverhältnis verhindert Investition
    barrier_proof_uncertainty = models.BooleanField(blank=True, initial=False)  # C2d Unsicherheit, was für den Nachweis benötigt wird
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
    # Self-referential funding amount belief (free-text number input, EUR).
    belief_funding_amount = models.IntegerField(
        min=0, max=100000, blank=True,
        label='Erwartete Förderung für das eigene Unternehmen (€)',
    )
    # Self-referential perceived overall hassle / burden of the application
    # process. "Belastend" wording per coauthor request.
    belief_hassle = models.IntegerField(
        choices=[
            [1, 'Überhaupt nicht belastend'],
            [2, 'Wenig belastend'],
            [3, 'Mittel'],
            [4, 'Eher belastend'],
            [5, 'Sehr belastend'],
        ],
        label='Erwartete Gesamt-Belastung durch den Klimabonus-Antragsprozess',
    )
    # Posterior precision / belief confidence — meta-question at end of the
    # belief block. Replaces the earlier "credibility of shown info" item,
    # which was ill-defined for the Control arm (no specific info to rate).
    # 1 = sehr unsicher, 10 = sehr sicher. Treatment should narrow priors
    # → confidence should be higher in T1 and T2 than in Control.
    belief_confidence = models.IntegerField(
        min=1, max=10, blank=True,
        label='Sicherheit in den eigenen Belief-Einschätzungen (Bayesian posterior precision)',
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

    # ---- G1: Stated importance of climate protection for the firm ----
    # 5-point Likert. Captures heterogeneity of treatment effects by stated
    # green orientation (pre-registered moderator). Asked on Outcomes page.
    respondent_climate_importance = models.IntegerField(
        blank=True,
        choices=[
            [1, 'Überhaupt nicht wichtig'],
            [2, 'Eher unwichtig'],
            [3, 'Teils, teils'],
            [4, 'Eher wichtig'],
            [5, 'Sehr wichtig'],
        ],
        label='Wie wichtig ist Klimaschutz für Ihr Unternehmen?',
    )

    # ---- Commitment ladder (revealed actions) ----
    wants_email = models.BooleanField(
        choices=[[True, 'Ja, gerne'], [False, 'Nein, danke']],
    )
    email_address = models.StringField(blank=True)

    wants_event = models.BooleanField(
        choices=[[True, 'Ja, gerne'], [False, 'Nein, danke']],
    )

    wants_hotline = models.BooleanField(
        choices=[[True, 'Ja, gerne'], [False, 'Nein, danke']],
    )
    # phone_number is kept for backward compatibility with existing
    # session DBs but is no longer collected. D4 (Rückruf → Hotline):
    # the hotline is OUR phone, participants call us; we don't ask for
    # theirs. Stays blank for all new participants.
    phone_number = models.StringField(blank=True)

    # ---- Revealed action: click on Antragsportal ----
    # Drei separate Click-Tracker:
    #   1. Landing (fast path, vor Survey) — beobachtet User die schon
    #      vor der Befragung direkt zum Antrag springen.
    #   2. Abschluss (slow path, direkt nach Survey, auf der CTA-Card) —
    #      beobachtet User die nach kompletter Befragung konvertieren.
    #   3. EndPage (post-completed, beim Re-Read der Info-Seite) —
    #      beobachtet User die erst beim zweiten Durchblättern überzeugt
    #      sind. Wichtig weil EndPage = re-displayed Treatment-Info.
    # Alle drei laufen über live_method (sofort-Persistenz, unabhängig
    # vom Form-Submit; siehe Landing.live_method / Abschluss.live_method
    # / EndPage.live_method).
    clicked_portal_landing = models.BooleanField(blank=True, initial=False)
    clicked_portal_landing_ts = models.FloatField(blank=True)

    clicked_application_portal = models.BooleanField(blank=True, initial=False)
    clicked_application_portal_ts = models.FloatField(blank=True)

    clicked_portal_endpage = models.BooleanField(blank=True, initial=False)
    clicked_portal_endpage_ts = models.FloatField(blank=True)

    # Survey-Einstiegspunkt: welcher CTA hat die Befragung gestartet?
    # Werte: 'q1' (Weiter-Button unter Frage 1), 'sticky' (Sticky-Leiste),
    # 'bottom' (CTA-Sektion nach dem Process-Akkordeon), 'prompt' (Popup).
    # Leer, wenn kein Einstiegspunkt gesetzt wurde.
    entry_cta = models.StringField(blank=True)

    # ---- Final free-text feedback (Abschluss page) ----
    feedback_subsidies = models.LongStringField(blank=True)

    # ---- Verlosung: E-Mail-Adresse für die Gutschein-Verlosung ----
    # Freiwillige persönliche E-Mail-Adresse für die Amazon-Gutschein-
    # Verlosung (5× 100 €) unter allen, die die Befragung abschließen.
    # WICHTIG: personenbezogen → de-pseudonymisiert die Zeile. Vor der
    # wissenschaftlichen Auswertung getrennt exportieren, Verlosung
    # offline ziehen, dann diese Spalte aus dem Analyse-Datensatz löschen
    # (siehe Datenschutzhinweis-Ergänzung). Ausschließlich für die
    # Verlosung, nicht für die Analyse.
    raffle_email = models.StringField(blank=True)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

# Treatment-String (frakey-Lieferung) → App-Integer.
# 'control' fehlt absichtlich: das ist die PURE CONTROL, die keinen Link
# bekommt und hier still ignoriert wird (siehe _DROP_TREAT).
_TREAT_MAP = {'baseline': 1, 't1': 2, 't2': 3}
_DROP_TREAT = {'control'}


def _resolve_assignment_path():
    """Erste existierende Datei aus C.ASSIGNMENT_FILES, oder None."""
    for name in C.ASSIGNMENT_FILES:
        p = os.path.join(C.DATA_DIR, name)
        if os.path.exists(p):
            return p
    return None


def _read_rows(path):
    """CSV-Datei → Liste von dicts (Header→Wert). Nur CSV (stdlib,
    bombensicher). xlsx wird bewusst NICHT in Produktion geparst — siehe
    C.ASSIGNMENT_FILES."""
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def load_assignment():
    """Lade die Zuteilung → dict: label -> {treatment, stratum, peer_id}.

    Liest die CSV und akzeptiert ZWEI Spalten-Schemata:

      A) frakey-Lieferung: frakey | strata | treat
         - treat='Control'  → PURE CONTROL, wird IGNORIERT (kein Link).
         - treat='Baseline' → 1, 'T1' → 2, 'T2' → 3
         - peer_id wird aus dem Stratum abgeleitet (STRATUM_TO_PEER) —
           es ist KEINE peer_id-Spalte nötig.

      B) Converter-/Legacy-Output: participant_label | treatment(1/2/3) |
         stratum | peer_id

    Empfohlener Weg (möglichst fehlerarm): die gelieferte frakeys.xlsx
    lokal mit tools/build_assignment.py validieren und nach frakeys.csv
    konvertieren. Der Converter prüft Eindeutigkeit, treat-Werte und
    Peer-Ableitung und VERWEIGERT bei Fehlern — Probleme werden so
    LOKAL vor dem Deploy sichtbar, nicht erst bei der Session-Erstellung.

    Validierung auch hier: eine T2-Zeile ohne gültige peer_id (1-4) wird
    VERWORFEN (Label → InvalidLink) und im Server-Log gewarnt.
    """
    path = _resolve_assignment_path()
    if not path:
        return {}
    try:
        rows = _read_rows(path)
    except Exception as e:  # noqa: BLE001 — robust gegen kaputte Datei
        print(f'[klimabonus] FEHLER beim Lesen von {os.path.basename(path)}: '
              f'{e!r} — keine Zuteilung geladen (alle Labels → InvalidLink).')
        return {}

    out = {}
    bad_peer_rows = []
    dropped_control = 0
    for row in rows:
        d = {(k or '').strip().lower(): ('' if v is None else str(v))
             for k, v in row.items()}
        label = (d.get('frakey') or d.get('participant_label') or '').strip()
        if not label:
            continue
        stratum = (d.get('strata') or d.get('stratum') or '').strip()
        treat_raw = (d.get('treat') or d.get('control') or d.get('treatment') or '').strip()

        # Treatment-Integer bestimmen (String-Label ODER Zahl).
        low = treat_raw.lower()
        if low in _DROP_TREAT:
            dropped_control += 1
            continue
        if low in _TREAT_MAP:
            t = _TREAT_MAP[low]
        else:
            try:
                t = int(treat_raw)
            except (ValueError, TypeError):
                continue
        if t not in (1, 2, 3):
            continue

        # peer_id: explizite Spalte hat Vorrang, sonst aus Stratum ableiten.
        peer = None
        peer_explicit = (d.get('peer_id') or '').strip()
        if peer_explicit:
            try:
                peer = int(peer_explicit)
            except ValueError:
                peer = None
        if t == 3 and peer is None:
            try:
                peer = STRATUM_TO_PEER.get(int(stratum))
            except (ValueError, TypeError):
                peer = None

        if t == 3 and peer not in VALID_PEER_IDS:
            bad_peer_rows.append((label, stratum))
            continue

        out[label] = {'treatment': t, 'stratum': stratum, 'peer_id': peer}

    if bad_peer_rows:
        print(f'[klimabonus] WARNUNG: {len(bad_peer_rows)} T2-Zeile(n) in '
              f'{os.path.basename(path)} ohne gültige peer_id (Stratum nicht '
              f'1-9 / nicht ableitbar) — VERWORFEN. Auszug: '
              + ', '.join(f'{lbl}(strata:{s!r})' for lbl, s in bad_peer_rows[:10]))
    print(f'[klimabonus] Zuteilung geladen aus {os.path.basename(path)}: '
          f'{len(out)} Links aktiv, {dropped_control} Pure-Control ignoriert.')
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

    Frage 1 (application_likelihood, 0-10) sitzt direkt unter dem
    Treatment-Block (identisch in allen drei Armen, Treatment-Inhalte
    unverändert); die weiteren Fragen folgen auf den Folgeseiten.
    Zusätzliche Einstiege in die Befragung: Survey-Prompt-Popup und
    Sticky-Leiste "Zur Befragung". entry_cta protokolliert den genutzten
    Einstiegspunkt.
    """
    form_model = 'player'
    # NOTE: click / consent / accordion events go through live_method below
    # so they persist immediately even if the participant never submits
    # the Landing page (e.g. clicks "Direkt zum Antrag" and never comes
    # back). Putting them in form_fields would risk overwriting the
    # live-saved values with empty defaults on form submit.
    # application_likelihood ist serverseitig Pflicht (IntegerField ohne
    # blank=True) — ohne Antwort auf Frage 1 kommt niemand in die Befragung.
    preserve_unsubmitted_inputs = True  # Reload-/Validation-Survival (Frage 1)
    form_fields = [
        'application_likelihood',
        'entry_cta',
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
          - 'portal_click'       → clicked_portal_landing + ts
          - 'process_expand'     → expanded_process = True
          - 'prompt_shown'       → prompt_shown_ts (2-min survey-prompt
              modal appeared)
          - 'prompt_dismissed'   → prompt_dismissed_ts (user closed modal
              without clicking the CTA inside it)
          - 'prompt_used'        → prompt_used = True (user clicked the
              CTA inside the modal — fires just before form submit)

        NOTE: 'consent_analytics' wurde 2026-06-19 entfernt — Cookie-Banner
        existiert nicht mehr, Consent wird durch den Link-Klick aus dem
        Anschreiben gegeben (siehe Datenschutzhinweis).

        Returns empty dict (no client-side response needed).
        """
        event = (data or {}).get('event')
        ts = (data or {}).get('ts')
        try:
            ts = float(ts) if ts is not None else None
        except (TypeError, ValueError):
            ts = None
        if event == 'portal_click':
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
    # Back-Button erlaubt — Teilnehmer:innen können zur Landing zurück,
    # um die Treatment-Information erneut zu lesen. Bewusst NICHT für
    # Beliefs/Commitment aktiviert (Kontamination der Outcomes-Antworten
    # durch nachgelagerte Belief-Block-Inhalte).
    allow_back_button = True
    # Erhält bereits eingegebene Werte über Page-Reload, Back-Navigation
    # und nach Validation-Errors (oTree 6 Feature, browser-localStorage).
    preserve_unsubmitted_inputs = True
    form_fields = [
        'consent_research', 'consent_research_ts',
        # Vorab-Screening (B-Cluster, pre-treatment)
        'screening_similar_done',
        # G1 Klimaschutz-Wichtigkeit (covariate / moderator)
        'respondent_climate_importance',
        # application_likelihood ist Frage 1 auf der Landing Page
        # (siehe Landing.form_fields).
        'measure_solar', 'measure_solar_green_roof', 'measure_battery',
        'measure_greening',
        'measure_rainwater', 'measure_drinking_fountain',
        'measure_other', 'measure_other_text',
        'measure_none',
        'barrier_time', 'barrier_complexity', 'barrier_uncertainty',
        'barrier_amount', 'barrier_property', 'barrier_priority',
        'barrier_already_applied',
        # C2a-d new barriers
        'barrier_funding_liquidity', 'barrier_internal_capacity',
        'barrier_owner_tenant', 'barrier_proof_uncertainty',
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
    preserve_unsubmitted_inputs = True  # Reload-/Validation-Survival
    form_fields = [
        'belief_approval_rate', 'belief_funding_amount',
        'belief_effort', 'belief_processing_time', 'belief_payout_effort',
        'belief_hassle',
        'belief_confidence',
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
    preserve_unsubmitted_inputs = True  # Reload-/Validation-Survival
    form_fields = [
        'respondent_position', 'respondent_position_other',
        'wants_email', 'email_address',
        'wants_event',
        'wants_hotline',
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
        # D4 Hotline (no phone_number anymore — user calls our hotline):
        # we still need an email to send out the hotline number + Sprechzeiten.
        if values.get('wants_hotline') and not email:
            return ('Damit wir Ihnen die Hotline-Nummer und die Sprechzeiten '
                    'zusenden können, benötigen wir Ihre E-Mail-Adresse.')

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.page_reached = max(player.page_reached or 0, 4)


class Abschluss(Page):
    form_model = 'player'
    preserve_unsubmitted_inputs = True  # Reload-/Validation-Survival
    # clicked_application_portal + _ts laufen jetzt über live_method
    # (symmetrisch zu Landing), damit der Antrag-Click auch dann persistent
    # ist, wenn der/die Teilnehmer:in NACH dem Klick den Browser schließt
    # ohne "Abschließen" zu drücken. Daher NICHT mehr in form_fields.
    form_fields = [
        'feedback_subsidies',
        'raffle_email',
        'time_abschluss',
    ]

    @staticmethod
    def live_method(player: Player, data):
        """Receive fire-and-forget click events from the Abschluss page.

        Mirrors Landing.live_method's design but for the post-survey
        Antrag-CTA. Without this, clicks would only persist if the user
        also submits the form via 'Abschließen' — but the most converting
        path is exactly the opposite (klick → opens portal in new tab →
        user starts antrag, never returns to close Abschluss tab).
        """
        event = (data or {}).get('event')
        ts = (data or {}).get('ts')
        try:
            ts = float(ts) if ts is not None else None
        except (TypeError, ValueError):
            ts = None
        if event == 'application_portal_click':
            player.clicked_application_portal = True
            if ts is not None:
                player.clicked_application_portal_ts = ts
        return {}

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

    Kein Form-Submit, aber live_method ist da, um Antrag-Klicks auch
    HIER zu tracken. Ohne live_method würde der Re-Read-Antrag-Klick
    in der Datenanalyse fehlen — wichtig weil EndPage potenziell der
    Conversion-Trigger für überlegende User ist (Direktive Jakob
    2026-06-08)."""

    @staticmethod
    def is_displayed(player: Player):
        return player.field_maybe_none('label_valid') is True

    @staticmethod
    def live_method(player: Player, data):
        """Receive 'endpage_portal_click' events from the EndPage CTA.

        Symmetrisch zu Landing.live_method und Abschluss.live_method:
        sofortige Persistenz, unabhängig davon ob User danach noch
        irgendwo "Weiter" klickt (es gibt nichts mehr — EndPage ist
        die letzte Seite).
        """
        event = (data or {}).get('event')
        ts = (data or {}).get('ts')
        try:
            ts = float(ts) if ts is not None else None
        except (TypeError, ValueError):
            ts = None
        if event == 'endpage_portal_click':
            player.clicked_portal_endpage = True
            if ts is not None:
                player.clicked_portal_endpage_ts = ts
        return {}

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
        'entry_cta',
        'screening_similar_done',
        'respondent_climate_importance',
        'application_likelihood',
        'measure_solar', 'measure_solar_green_roof', 'measure_battery',
        'measure_greening',
        'measure_rainwater', 'measure_drinking_fountain',
        'measure_other', 'measure_other_text',
        'measure_none', 'measures_order',
        'barrier_time', 'barrier_complexity', 'barrier_uncertainty',
        'barrier_amount', 'barrier_property', 'barrier_priority',
        'barrier_already_applied',
        'barrier_funding_liquidity', 'barrier_internal_capacity',
        'barrier_owner_tenant', 'barrier_proof_uncertainty',
        'barrier_other', 'barrier_other_text', 'barriers_order',
        'belief_approval_rate', 'belief_funding_amount',
        'belief_effort', 'belief_processing_time', 'belief_payout_effort',
        'belief_hassle', 'belief_confidence',
        'respondent_position', 'respondent_position_other',
        'wants_email', 'email_address',
        'wants_event',
        'wants_hotline',
        'feedback_subsidies',
        'raffle_email',
        'clicked_portal_landing', 'clicked_portal_landing_ts',
        'clicked_application_portal', 'clicked_application_portal_ts',
        'clicked_portal_endpage', 'clicked_portal_endpage_ts',
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
            p.field_maybe_none('entry_cta') or '',
            p.field_maybe_none('screening_similar_done'),
            p.field_maybe_none('respondent_climate_importance'),
            p.field_maybe_none('application_likelihood'),
            p.measure_solar, p.measure_solar_green_roof, p.measure_battery,
            p.measure_greening,
            p.measure_rainwater, p.measure_drinking_fountain,
            p.measure_other,
            p.field_maybe_none('measure_other_text') or '',
            p.measure_none,
            p.field_maybe_none('measures_order') or '',
            p.barrier_time, p.barrier_complexity, p.barrier_uncertainty,
            p.barrier_amount, p.barrier_property, p.barrier_priority,
            p.barrier_already_applied,
            p.barrier_funding_liquidity, p.barrier_internal_capacity,
            p.barrier_owner_tenant, p.barrier_proof_uncertainty,
            p.barrier_other,
            p.field_maybe_none('barrier_other_text') or '',
            p.field_maybe_none('barriers_order') or '',
            p.field_maybe_none('belief_approval_rate'),
            p.field_maybe_none('belief_funding_amount'),
            p.field_maybe_none('belief_effort'),
            p.field_maybe_none('belief_processing_time'),
            p.field_maybe_none('belief_payout_effort'),
            p.field_maybe_none('belief_hassle'),
            p.field_maybe_none('belief_confidence'),
            p.field_maybe_none('respondent_position') or '',
            p.field_maybe_none('respondent_position_other') or '',
            p.field_maybe_none('wants_email'),
            p.field_maybe_none('email_address') or '',
            p.field_maybe_none('wants_event'),
            p.field_maybe_none('wants_hotline'),
            p.field_maybe_none('feedback_subsidies') or '',
            p.field_maybe_none('raffle_email') or '',
            p.clicked_portal_landing,
            p.field_maybe_none('clicked_portal_landing_ts'),
            p.clicked_application_portal,
            p.field_maybe_none('clicked_application_portal_ts'),
            p.clicked_portal_endpage,
            p.field_maybe_none('clicked_portal_endpage_ts'),
        ]


# ------------------------------------------------------------------ #
# live_method endpoints — receive JS beacons (consent click, portal click)
# ------------------------------------------------------------------ #

# We use Page.live_method below per page where needed. For consent and
# portal-click we'll POST via fetch() to a lightweight endpoint defined
# inline on each page that accepts these signals. Implementation detail
# kept in templates + before_next_page hooks.
