"""Page parts for automatic updates: self-refresh, unreviewed headlines and status."""
from datetime import datetime
from html import escape
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import streamlit as st

from i18n import language

from . import ROOT, collect, get_process_updater, read_state

WATCHED = ['data', 'locales', 'assets', 'imported/parties', 'imported/countries', 'imported/evidence']
TEXT = {
    'en': {
        'headlines': 'Latest headlines — collected automatically, not reviewed',
        'headlines_note': 'Headlines from public news feeds that mention reconstruction and this page’s subject. '
                          'They are not reviewed and are not part of the research above.',
        'none': 'No matching headlines have been collected yet.',
        'mentions': 'Mentions',
        'status': 'Automatic updates',
        'files': 'Data files',
        'files_ok': 'Watched continuously. Saving a file rebuilds the affected pages, and open pages refresh by themselves.',
        'rebuilt': 'Last rebuild',
        'problem': 'could not be rebuilt; the previous version is still shown',
        'workbook_review': 'The new workbook changes reviewed figures, so it was not imported. Review it first',
        'workbook_failed': 'The new workbook could not be imported',
        'workbook_ok': 'Workbook imported',
        'news': 'Headlines',
        'news_checked': 'Last checked',
        'news_pending': 'First check in progress.',
        'news_saved': 'saved',
        'news_failed': 'Feeds unavailable at the last check',
        'publish': 'Publishing',
        'publish_off': 'Runs only when the website is started with run_website.py on this computer.',
        'idle': 'Everything is published to GitHub.',
        'waiting': 'Changes detected. They are published after five quiet minutes, once the checks pass.',
        'published': 'Published to GitHub',
        'checks_failed': 'Not published: the checks failed. Publishing resumes when the files change',
        'push_failed': 'Saved locally, but GitHub did not accept the upload. Retrying every ten minutes',
        'commit_failed': 'The changes could not be saved to Git',
        'unavailable': 'Git is unavailable',
    },
    'ar': {
        'headlines': 'آخر العناوين — تُجمع تلقائياً ولم تُراجع',
        'headlines_note': 'عناوين من خلاصات إخبارية عامة تذكر إعادة الإعمار وموضوع هذه الصفحة. '
                          'لم تُراجع وليست جزءاً من البحث أعلاه.',
        'none': 'لم تُجمع عناوين مطابقة بعد.',
        'mentions': 'يذكر',
        'status': 'التحديثات التلقائية',
        'files': 'ملفات البيانات',
        'files_ok': 'تُراقب باستمرار. حفظ أي ملف يعيد بناء الصفحات المعنية، والصفحات المفتوحة تتحدث تلقائياً.',
        'rebuilt': 'آخر إعادة بناء',
        'problem': 'تعذرت إعادة البناء؛ ما زالت النسخة السابقة معروضة',
        'workbook_review': 'الملف الجديد يغيّر أرقاماً مراجَعة، لذلك لم يُستورد. راجعه أولاً',
        'workbook_failed': 'تعذر استيراد الملف الجديد',
        'workbook_ok': 'تم استيراد الملف',
        'news': 'العناوين',
        'news_checked': 'آخر تحقق',
        'news_pending': 'التحقق الأول جارٍ.',
        'news_saved': 'محفوظة',
        'news_failed': 'خلاصات لم تكن متاحة في آخر تحقق',
        'publish': 'النشر',
        'publish_off': 'يعمل فقط عند تشغيل الموقع عبر run_website.py على هذا الحاسوب.',
        'idle': 'كل شيء منشور على GitHub.',
        'waiting': 'رُصدت تغييرات. تُنشر بعد خمس دقائق من الهدوء وبعد نجاح الفحوص.',
        'published': 'نُشر على GitHub',
        'checks_failed': 'لم يُنشر: فشلت الفحوص. يُستأنف النشر عند تغيّر الملفات',
        'push_failed': 'حُفظ محلياً، لكن GitHub لم يقبل الرفع. تُعاد المحاولة كل عشر دقائق',
        'commit_failed': 'تعذر حفظ التغييرات في Git',
        'unavailable': 'Git غير متاح',
    },
}
RULE_NAMES = {'political': 'What parties are saying', 'countries': 'What countries are saying', 'localization': 'Arabic'}


def tr(key):
    return TEXT[language() if language() in TEXT else 'en'][key]


def when(value):
    try:
        return datetime.fromisoformat(value).astimezone(ZoneInfo('Asia/Beirut')).strftime('%d %b %Y, %H:%M')
    except (TypeError, ValueError):
        return ''


@st.cache_resource
def start_updater():
    """Once per server process. The test runner never starts background work."""
    if 'streamlit.testing.v1' in sys.modules:
        return None
    return get_process_updater()


def content_revision(root=ROOT):
    """Changes whenever a displayed data, translation, style or page file is saved."""
    latest, count = 0, 0
    for folder in WATCHED:
        try:
            for path in (Path(root) / folder).iterdir():
                if path.is_file():
                    latest, count = max(latest, path.stat().st_mtime_ns), count + 1
        except OSError:
            continue
    return f'{latest}:{count}'


@st.cache_data(show_spinner=False, max_entries=2)
def _headlines(modified_ns):
    return collect.load(ROOT)


def headlines(topic):
    path = ROOT / collect.OUTPUT
    items = _headlines(path.stat().st_mtime_ns) if path.exists() else []
    return [item for item in items if topic in item['topics']]


def headlines_html(items):
    rows = []
    for item in items:
        mentions = f' · {escape(tr("mentions"))}: {escape("، ".join(item["mentions"]) if language() == "ar" else ", ".join(item["mentions"]))}' if item.get('mentions') else ''
        rows.append(
            f'<li><a href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer" dir="auto">{escape(item["title"])}</a>'
            f'<small><bdi>{escape(item["publisher"])}</bdi> · <bdi>{escape((item.get("published") or item["first_seen"])[:10])}</bdi>{mentions}</small></li>')
    direction = 'rtl' if language() == 'ar' else 'ltr'
    return (f'<div class="auto-headlines" dir="{direction}"><p>{escape(tr("headlines_note"))}</p>'
            + (f'<ul>{"".join(rows)}</ul>' if rows else f'<p>{escape(tr("none"))}</p>') + '</div>')


def show_headlines(topic, limit=12):
    with st.expander(tr('headlines')):
        st.html(headlines_html(headlines(topic)[:limit]))


def status_lines(state):
    """(kind, text) rows; kind is 'ok' or 'warn'."""
    rows = []
    rebuild, news, publish = state['rebuild'], state['collect'], state['publish']
    rows.append(('ok', f'**{tr("files")}:** {tr("files_ok")}'))
    for name, label in RULE_NAMES.items():
        result = rebuild.get(name)
        if result and not result['ok']:
            rows.append(('warn', f'**{label}** {tr("problem")} ({when(result["at"])}): {result["message"]}'))
        elif result:
            rows.append(('ok', f'{tr("rebuilt")} — {label}: {when(result["at"])}'))
    workbook = rebuild.get('workbook')
    if workbook:
        key = 'workbook_ok' if workbook['ok'] else 'workbook_review' if workbook.get('review') else 'workbook_failed'
        detail = '' if workbook['ok'] else f': {workbook["message"]}'
        rows.append(('ok' if workbook['ok'] else 'warn', f'{tr(key)} — {workbook["file"]} ({when(workbook["at"])}){detail}'))
    if rebuild.get('error'):
        rows.append(('warn', f'**{tr("files")}:** {rebuild["error"]}'))
    if news.get('checked_at'):
        rows.append(('ok', f'**{tr("news")}:** {tr("news_checked")} {when(news["checked_at"])} · {len(collect.load(ROOT))} {tr("news_saved")}'))
        if news.get('failures'):
            # One feed missing a check is routine; only a complete outage is a warning.
            outage = len(news['failures']) > len(collect.FEEDS)
            rows.append(('warn' if outage else 'ok', f'{tr("news_failed")}: {", ".join(news["failures"])}'))
    else:
        rows.append(('ok', f'**{tr("news")}:** {tr("news_pending")}'))
    status = publish.get('status')
    if not publish.get('enabled'):
        rows.append(('ok', f'**{tr("publish")}:** {tr("publish_off")}'))
    elif status == 'published':
        rows.append(('ok', f'**{tr("publish")}:** {tr("published")} {when(publish.get("pushed_at"))} ({publish.get("commit", "")})'))
    elif status in ('checks_failed', 'push_failed', 'commit_failed', 'unavailable'):
        rows.append(('warn', f'**{tr("publish")}:** {tr(status)}: {publish.get("detail", "")}'))
    else:
        rows.append(('ok', f'**{tr("publish")}:** {tr("waiting" if status == "waiting" else "idle")}'))
    return rows


@st.fragment(run_every='20s')
def auto_update_footer():
    """Reload the whole page when saved content changes, and report what the updater did."""
    revision = content_revision()
    if st.session_state.setdefault('_content_revision', revision) != revision:
        st.session_state['_content_revision'] = revision
        st.rerun()
    rows = status_lines(read_state())
    problems = sum(kind == 'warn' for kind, _ in rows)
    with st.expander(tr('status') + (f' · ⚠ {problems}' if problems else '')):
        for kind, text in rows:
            (st.warning if kind == 'warn' else st.markdown)(text)
