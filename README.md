# Klimabonus Field Experiment — oTree App

oTree 5.x app for the Frankfurt Klimabonus information-portal field
experiment, run by the Goethe-Universität Frankfurt.

The app delivers one of three randomly-assigned variants of an information
website to ~20.000 Frankfurt firms and collects post-treatment beliefs and
behavioral outcomes (commitment ladder, click on the application portal).

## Design at a glance

- **3-arm between-subject design**, ratio 1:1:1
  - **Control** — basic Klimabonus information only
  - **T1 Stadt** — basic info + official Klimareferat statistics (approval
    rate, processing time, mean grant)
  - **T2 Peer** — basic info + peer testimonial + the same statistics
- **Treatment assignment** is loaded from `klimabonus/data/assignment.csv`
  at session creation; firms are mapped to arms by `participant_label`
  (stratified offline in R/Stata for reproducibility).
- **Order of pages** (intentional, see preregistration):
  1. Landing (with cookie-style analytics consent)
  2. Grundinfo (basic info, identical across arms)
  3. Treatment (variant by arm)
  4. Outcomes (application likelihood, relevant measures, barriers)
  5. Beliefs (post-treatment belief elicitation)
  6. Commitment ladder (email, event invite, callback)
  7. Abschluss (thank-you + Antragsportal CTA + final contact-consent)

## Project structure

```
klimabonus_experiment/
├── settings.py                    oTree project settings
├── requirements.txt
├── Procfile                       Heroku entry point
├── runtime.txt                    Python version pin
├── _templates/global/Page.html    Base template (no oTree chrome)
└── klimabonus/                    The single oTree app
    ├── __init__.py                Models, pages, custom_export
    ├── Landing.html               + cookie-banner consent
    ├── Grundinfo.html
    ├── Treatment.html             C / T1 / T2 in one file (conditional)
    ├── Outcomes.html
    ├── Beliefs.html
    ├── Commitment.html
    ├── Abschluss.html
    ├── InvalidLink.html           shown when label is unknown
    ├── data/
    │   ├── assignment.csv          ← live label→treatment map (gitignored)
    │   └── assignment.csv.example  ← template, committed
    └── static/klimabonus/style.css
```

## Local setup (devserver)

```bash
cd klimabonus_experiment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
otree devserver
```

Open http://localhost:8000/demo/klimabonus

For a participant flow with a real label (mirroring the production link):
```
http://localhost:8000/join/klimabonus?participant_label=DEMO_T1
```

## Treatment-assignment CSV

`klimabonus/data/assignment.csv` is **read at session creation** and maps
each `participant_label` to a treatment (and, for T2, to a peer firm).

Columns:
| column            | required | values                                              |
|-------------------|----------|-----------------------------------------------------|
| participant_label | yes      | unique string, matches the URL link                 |
| treatment         | yes      | 1 (Control), 2 (T1 Stadt), 3 (T2 Peer)              |
| stratum           | no       | free-text stratum label, copied to `Player.stratum` |
| peer_id           | only T2  | integer 1–6, selects which peer firm to show        |

The CSV must be UTF-8, comma-separated, with a header row. Unknown labels
are routed to `InvalidLink` and not assigned a treatment.

### Peer matching (T2 only)

T2 participants see one of 6 peer-firm profiles defined in
`klimabonus/peers.py`. Matching of recipient firm → peer firm happens
**offline** in R/Stata at the time of label generation, with the chosen
peer rolled into the `peer_id` column of `assignment.csv`. The app does
no matching of its own — it simply renders the peer assigned in the CSV.

To swap in real peer content, edit `klimabonus/peers.py` (one dict per
peer: name, firma, branche, size_label, photo, quote, time_minutes,
amount_eur). Drop peer photos into
`klimabonus/static/klimabonus/peer_<n>.jpg` and reference them from each
peer's `photo` field. Until photos are uploaded, the T2 quote card
renders a placeholder div.

⚠️ **The live file is gitignored.** Replace `assignment.csv` immediately
before launch with the stratified randomization from R/Stata. Never commit
the production file (it would let anyone deanonymize the experiment).

## Heroku deployment

```bash
heroku create klimabonus-frankfurt
heroku config:set OTREE_PRODUCTION=1
heroku config:set OTREE_AUTH_LEVEL=STUDY
heroku config:set OTREE_ADMIN_PASSWORD=…
heroku config:set OTREE_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini
git push heroku main
heroku run otree resetdb
```

Production participant URL pattern:
```
https://klimabonus-frankfurt.herokuapp.com/join/klimabonus?participant_label=FIRM_12345
```

## Data export

Two ways to get the data:

1. **Standard oTree admin**: `https://…/SessionData/<session_code>/` → CSV
   (one row per page event, plus per-participant data).
2. **Custom export** at `https://…/export` → choose `klimabonus`. Returns
   one row per participant with all outcomes, timing, and treatment fields
   already merged. Implemented in `custom_export()` in
   `klimabonus/__init__.py`.

## Outcome variables (one-row-per-firm export)

| Field                          | Source page  | Type             |
|--------------------------------|--------------|------------------|
| treatment / treatment_label    | assignment   | int / str        |
| peer_id                        | assignment   | int 1–6 (T2 only)|
| stratum                        | assignment   | str              |
| consent_analytics              | Landing      | bool (cookie)    |
| consent_contact                | Abschluss    | bool (final)     |
| time_landing … time_abschluss  | every page   | float (seconds)  |
| scroll_landing/grundinfo/treat | passive JS   | int (% scrolled) |
| application_likelihood         | Outcomes     | int 0–10         |
| measure_*                      | Outcomes     | bool ×10         |
| barrier_* + barrier_other_text | Outcomes     | bool + str       |
| belief_approval_rate           | Beliefs      | int 0–100        |
| belief_processing_time         | Beliefs      | int 1–5          |
| belief_effort                  | Beliefs      | int 1–5          |
| wants_email + email_address    | Commitment   | bool + str       |
| wants_event                    | Commitment   | bool             |
| wants_callback + phone_number  | Commitment   | bool + str       |
| clicked_application_portal     | Abschluss    | bool (JS event)  |
| page_reached                   | every page   | int 0–7 (drop-off)|
| completed                      | Abschluss    | bool             |

## Open placeholders before launch

- `[BEWILLIGUNGSQUOTE]`, `[BEARBEITUNGSZEIT]`, `[FÖRDERBETRAG]` in
  `Treatment.html` — official statistics from the Klimareferat.
- `[PEER_*]` in `Treatment.html` — peer testimonial text, name, firm,
  branch, photo (T2 only).
- `[PLATZHALTER: URL_ANTRAGSPORTAL]` in `Abschluss.html` — the actual
  Klimabonus online-application URL.
- `[PLATZHALTER: Teamfoto Klimareferat]` — replace with image asset in
  `klimabonus/static/klimabonus/`.

## Pre-registration & ethics

The design is intended for pre-registration on the AEA RCT registry / OSF
prior to fielding. The cookie-banner consent (analytics) and final-page
consent (contact) implement a two-tier consent model approved by the
Goethe ethics board (status: pending).
