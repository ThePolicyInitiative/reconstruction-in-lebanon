"""Offline app fixtures; live connection behaviour is tested independently."""
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

DATA = Path(__file__).resolve().parents[1] / 'integrated_tenders' / 'data'


class OfflineFeed:
    def refresh(self, force=False):
        sources = {}
        for source, folder in [('ppa', DATA), ('cdr', DATA / 'cdr')]:
            sources[source] = tuple(json.loads((folder / filename).read_text(encoding='utf-8'))
                                    for filename in ('dashboard.json', 'status.json'))
        return {'sources': sources, 'revision': None, 'live': False, 'error': None, 'connected_at': None}

    def detail(self, source, identifier, revision):
        folder = DATA / ('cdr' if source == 'cdr' else '')
        return json.loads((folder / 'tenders' / f'{identifier}.json').read_text(encoding='utf-8'))


@contextmanager
def offline_tender_feed():
    with patch('integrated_tenders.get_feed', return_value=OfflineFeed()), patch('integrated_tenders.get_monitor'):
        yield
