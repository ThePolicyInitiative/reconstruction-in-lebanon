"""Re-run the import/build scripts when the files they read are saved.

Reviewed figures are never changed silently: a workbook whose reviewed cells
differ is reported as needing review and the displayed data stays as it was.
"""
import hashlib
import json
from pathlib import Path
import shutil
import time

from . import stamp

SETTLE = 3  # Seconds a file must be unchanged, so half-saved files are not read.

POLITICAL_INPUTS = [
    'scripts/build_political_graphs.py', 'imported/parties/reconstruction-statements.json', 'locales/ar.json',
    'data/political_positions_additions.json', 'data/political_party_register.tsv', 'data/political_mp_names.tsv',
    'data/political_mp_roster.json', 'data/political_ministers.tsv', 'data/political_specific_categories.json',
    'data/political_party_symbols.json', 'data/political_person_photos.json', 'data/political_topic_review.json',
]
LOCALIZATION_INPUTS = ['locales/ar.json', 'assets/component-i18n.js', 'assets/component-arabic.css', 'assets/component-frame.js']


def build_political(root):
    from scripts import build_political_graphs
    build_political_graphs.build()


def build_countries(root):
    from scripts import country_content, install_localization
    country_content.update_saved_page()
    install_localization.install()


def install_localization(root):
    from scripts import install_localization as script
    script.install()


RULES = [
    ('political', POLITICAL_INPUTS, build_political),
    ('countries', ['data/country_additions.json'], build_countries),
    ('localization', LOCALIZATION_INPUTS, install_localization),
]


def signature(root, names):
    """Changes whenever an input is saved; None while a file is still being written."""
    parts = []
    for name in names:
        try:
            info = (Path(root) / name).stat()
        except OSError:
            parts.append((name, None))
            continue
        if time.time() - info.st_mtime < SETTLE:
            return None
        parts.append((name, info.st_mtime_ns, info.st_size))
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def import_workbook(root, state, now, importer=None):
    """Import a new or re-saved Excel workbook dropped in data/."""
    root = Path(root)
    data_path = root / 'data' / 'economic_losses.json'
    current = json.loads(data_path.read_text(encoding='utf-8')).get('source_sha256')
    for path in sorted((root / 'data').glob('*.xlsx')):
        if path.name.startswith('~$'):
            continue  # Excel's lock file while the workbook is open.
        try:
            if time.time() - path.stat().st_mtime < SETTLE:
                continue
            digest = sha256(path)
        except OSError:
            continue  # Still open in Excel; try again on the next pass.
        if digest == current or digest == state.get('workbook', {}).get('sha256'):
            continue
        result = {'sha256': digest, 'file': path.name, 'at': stamp(now)}
        try:
            # Work from a copy: the importer replaces the saved workbook itself.
            incoming = root / '.cache' / 'auto-update' / 'incoming' / path.name
            incoming.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, incoming)
            if importer is None:
                from scripts.import_economic_losses import main as importer
            importer(incoming)
            result.update(ok=True, message='Imported.')
        except ValueError as exc:
            result.update(ok=False, review=True, message=str(exc)[:400])
        except Exception as exc:
            result.update(ok=False, message=f'{type(exc).__name__}: {exc}'[:400])
        state['workbook'] = result
        return


def run(root, state, now, rules=RULES):
    signatures = state.setdefault('signatures', {})
    for name, inputs, action in rules:
        current = signature(root, inputs)
        if current is None or current == signatures.get(name):
            continue
        if name not in signatures:
            signatures[name] = current  # First sight: the saved outputs are the baseline.
            continue
        try:
            action(root)
            state[name] = {'ok': True, 'at': stamp(now), 'message': 'Rebuilt.'}
        except Exception as exc:
            # Keep the previous output and say why, rather than publish a partial build.
            state[name] = {'ok': False, 'at': stamp(now), 'message': f'{type(exc).__name__}: {exc}'[:400]}
        # Outputs can also be inputs (translations are copied into the pages).
        signatures[name] = signature(root, inputs) or current
    import_workbook(root, state, now)
    state.pop('error', None)
