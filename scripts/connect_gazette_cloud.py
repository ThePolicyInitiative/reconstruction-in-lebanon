"""One-time private Gazette connection setup, using hidden stdin and OS storage.

Use the existing service credential returned by Sites get_site. Never put the
credential in arguments, source, URLs, logs, environment files or data exports.
"""
import getpass
import json
from integrated_gazette.credentials import save_windows_token, windows_token
from integrated_gazette.live_data import CloudGazetteFeed, SiteReader


def main():
    print('Ready for the existing Gazette Site credential on hidden stdin.', flush=True)
    token = getpass.getpass('')
    feed = CloudGazetteFeed(reader=SiteReader(lambda: token))
    result = feed.refresh(force=True)
    if not result['live']:
        raise SystemExit(result['error'])
    save_windows_token(token)
    if windows_token() != token:
        raise SystemExit('The saved Gazette credential could not be verified.')
    print(json.dumps({'connected': True, 'credential_saved': True,
                      'records_2024_2026': len(result['snapshot']['records']),
                      'all_records': result['records'], 'latest_publication': result['latest_publication'],
                      'revision': result['revision'], 'connected_at': result['connected_at']}))


if __name__ == '__main__':
    main()
