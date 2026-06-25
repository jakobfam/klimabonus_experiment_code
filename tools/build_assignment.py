#!/usr/bin/env python3
"""
build_assignment.py — turn Elisa's frakeys delivery into the app's
assignment.csv, with full validation.

Input  : frakeys file (.xlsx or .csv) with columns:
             frakey   — random participant key (the participant_label)
             strata   — integer 1-9 (size x industry-relevance bucket)
             treat    — one of: Control | Baseline | T1 | T2
Output : klimabonus/data/frakeys.csv (the file the app reads) with columns:
             participant_label, treatment, stratum, peer_id

Mapping rules (Direktive Jakob 2026-06-25):
  * treat='Control'  → PURE CONTROL. Gets no link, must NOT enter the app.
                       These rows are DROPPED here.
  * treat='Baseline' → app treatment 1 (contacted control, generic page)
  * treat='T1'       → app treatment 2
  * treat='T2'       → app treatment 3
  * peer_id is DERIVED from the stratum's size class (only for T2):
        strata 1,2,3 (kleinst) → peer 4  (Expertenspot, Kleinstunternehmen)
        strata 4,5,6 (klein)   → peer 3  (Wilhelm Roth, Kleinunternehmen)
        strata 7,8,9 (mittel)  → peer 2  (Carl Friederichs, Mittel)
        (groß → peer 1 Nassauische Heimstätte — no stratum codes yet)

Usage:
    python3 tools/build_assignment.py path/to/frakeys.xlsx
        → validiert und schreibt klimabonus/data/frakeys.csv (App liest das)
    python3 tools/build_assignment.py path/to/frakeys.xlsx --check
        → nur validieren, nichts schreiben

The script ALWAYS validates and refuses to write a broken file.
"""

import argparse
import csv
import os
import re
import sys
import zipfile
from collections import Counter

# ---- Strata codebook (1-9). For reference / sanity output. -----------
STRATA_LABELS = {
    1: 'kleinst hoch relevant (Bau/Energie/Immobilien)',
    2: 'kleinst mittel relevant (Industrie/Dienstleister)',
    3: 'kleinst niedrig relevant (sonstige)',
    4: 'klein hoch relevant (Bau/Energie/Immobilien)',
    5: 'klein mittel relevant (Industrie/Dienstleister)',
    6: 'klein niedrig relevant (sonstige)',
    7: 'mittel hoch relevant (Bau/Energie/Immobilien)',
    8: 'mittel mittel relevant (Industrie/Dienstleister)',
    9: 'mittel niedrig relevant (sonstige)',
}

# ---- Treatment string → app integer. 'Control' is intentionally absent
#      (pure control, dropped). ------------------------------------------
TREAT_MAP = {'Baseline': 1, 'T1': 2, 'T2': 3}
DROP_TREAT = {'Control'}  # pure control — no link, not in the app

# ---- Stratum → peer_id (size match). Only applied to T2 rows. ---------
STRATUM_TO_PEER = {
    1: 4, 2: 4, 3: 4,   # kleinst → Expertenspot
    4: 3, 5: 3, 6: 3,   # klein   → Roth
    7: 2, 8: 2, 9: 2,   # mittel  → Friederichs
    # groß would be peer 1 (Nassauische); no such stratum code yet.
}


# ---------------------------------------------------------------------- #
# Input readers
# ---------------------------------------------------------------------- #
def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def read_xlsx(path):
    """Minimal single-sheet xlsx reader (stdlib only, no openpyxl)."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss = z.read('xl/sharedStrings.xml').decode('utf-8', 'ignore')
            for si in re.findall(r'<si>(.*?)</si>', ss, re.DOTALL):
                shared.append(''.join(re.findall(r'<t[^>]*>(.*?)</t>', si, re.DOTALL)))
        sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8', 'ignore')

    def cell_value(c):
        t = re.search(r't="([^"]+)"', c)
        v = re.search(r'<v>(.*?)</v>', c)
        if t and t.group(1) == 's' and v:
            return shared[int(v.group(1))]
        return v.group(1) if v else ''

    def col_letter(c):
        m = re.search(r'r="([A-Z]+)\d', c)
        return m.group(1) if m else '?'

    rows = re.findall(r'<row[^>]*>(.*?)</row>', sheet, re.DOTALL)
    parsed = []
    for r in rows:
        cells = re.findall(r'<c[^>]*/>|<c[^>]*>.*?</c>', r, re.DOTALL)
        parsed.append({col_letter(c): cell_value(c) for c in cells})
    if not parsed:
        return []
    # Build header from first row by column letter, then map subsequent rows.
    header = {col: (val or '').strip() for col, val in parsed[0].items()}
    out = []
    for row in parsed[1:]:
        out.append({header.get(col, col): val for col, val in row.items()})
    return out


def load(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':
        return read_csv(path)
    if ext in ('.xlsx', '.xlsm'):
        return read_xlsx(path)
    sys.exit(f'Unbekannte Dateiendung: {ext} (erwartet .csv oder .xlsx)')


# ---------------------------------------------------------------------- #
# Convert + validate
# ---------------------------------------------------------------------- #
def build(rows):
    errors, warnings = [], []
    out = []
    seen = set()
    dropped_control = 0
    treat_counts = Counter()
    stratum_counts = Counter()

    # Tolerate either column name for the key.
    def get(d, *names):
        for n in names:
            if n in d and d[n] not in (None, ''):
                return d[n]
        return ''

    for i, d in enumerate(rows, start=2):  # row 2 = first data row in xlsx
        key = str(get(d, 'frakey', 'participant_label')).strip()
        strata_raw = str(get(d, 'strata', 'stratum')).strip()
        treat = str(get(d, 'treat', 'control', 'treatment')).strip()

        if not key:
            errors.append(f'Zeile {i}: leerer frakey')
            continue
        if key in seen:
            errors.append(f'Zeile {i}: doppelter frakey {key!r}')
            continue
        seen.add(key)

        treat_counts[treat] += 1

        # Pure control → drop (no link).
        if treat in DROP_TREAT:
            dropped_control += 1
            continue

        if treat not in TREAT_MAP:
            errors.append(f'Zeile {i} ({key}): unbekanntes treat {treat!r} '
                          f'(erlaubt: Control, Baseline, T1, T2)')
            continue
        t = TREAT_MAP[treat]

        # Stratum
        try:
            stratum = int(strata_raw)
        except ValueError:
            errors.append(f'Zeile {i} ({key}): strata {strata_raw!r} ist kein Integer')
            continue
        if stratum not in STRATA_LABELS:
            warnings.append(f'Zeile {i} ({key}): strata {stratum} nicht im Codebook 1-9')
        stratum_counts[stratum] += 1

        # peer_id: derive for T2 only.
        peer_id = ''
        if t == 3:
            peer_id = STRATUM_TO_PEER.get(stratum)
            if peer_id is None:
                errors.append(f'Zeile {i} ({key}): T2 mit strata {stratum} '
                              f'→ keine Peer-Zuordnung (nur 1-9 / kleinst-klein-mittel). '
                              f'Groß-Firmen bräuchten Peer 1, aktuell kein Stratum-Code dafür.')
                continue

        out.append({
            'participant_label': key,
            'treatment': t,
            'stratum': str(stratum),
            'peer_id': str(peer_id) if peer_id != '' else '',
        })

    return out, errors, warnings, treat_counts, stratum_counts, dropped_control


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='frakeys .xlsx oder .csv')
    ap.add_argument('--out', default='klimabonus/data/frakeys.csv',
                    help='Ziel-CSV (Default: klimabonus/data/frakeys.csv — '
                         'genau die Datei, die die App liest)')
    ap.add_argument('--check', action='store_true',
                    help='nur validieren, nichts schreiben')
    args = ap.parse_args()

    rows = load(args.input)
    out, errors, warnings, treat_counts, stratum_counts, dropped = build(rows)

    print(f'Gelesen: {len(rows)} Zeilen aus {args.input}')
    print()
    print('Treatment-Verteilung (roh):')
    for k, v in sorted(treat_counts.items()):
        tag = ' → DROP (Pure Control, kein Link)' if k in DROP_TREAT else ''
        print(f'  {k:<10} {v:>5}{tag}')
    print(f'\nPure-Control-Zeilen verworfen: {dropped}')
    print(f'In die Ausgabe-CSV: {len(out)} Zeilen (Baseline/T1/T2)')
    print()
    print('Stratum-Verteilung (nur kontaktierte):')
    for k in sorted(stratum_counts):
        print(f'  {k} ({STRATA_LABELS.get(k,"?")}): {stratum_counts[k]}')
    missing = [s for s in STRATA_LABELS if s not in stratum_counts]
    if missing:
        print(f'  Hinweis: keine Firmen in Stratum {missing} in dieser Datei.')
    print()
    # Peer distribution among T2
    peer_dist = Counter(r['peer_id'] for r in out if r['treatment'] == 3)
    if peer_dist:
        print('Peer-Zuordnung (T2):')
        names = {'1':'Nassauische (groß)','2':'Friederichs (mittel)',
                 '3':'Roth (klein)','4':'Expertenspot (kleinst)'}
        for k in sorted(peer_dist):
            print(f'  peer {k} {names.get(k,"")}: {peer_dist[k]}')
        print()

    if warnings:
        print('WARNUNGEN:')
        for w in warnings:
            print('  ⚠️ ', w)
        print()
    if errors:
        print('FEHLER (Datei wird NICHT geschrieben):')
        for e in errors[:30]:
            print('  ✗ ', e)
        if len(errors) > 30:
            print(f'  … und {len(errors)-30} weitere')
        sys.exit(1)

    print('✓ Validierung bestanden.')
    if args.check:
        print('(--check: nichts geschrieben)')
        return
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['participant_label', 'treatment',
                                          'stratum', 'peer_id'])
        w.writeheader()
        w.writerows(out)
    print(f'✓ geschrieben: {args.out} ({len(out)} Zeilen)')


if __name__ == '__main__':
    main()
