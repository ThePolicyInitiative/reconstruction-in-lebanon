"""Commit and push to GitHub once the working files are quiet and the checks pass.

Nothing is published while files are still changing or while any check fails.
History is never rewritten: a rejected push is reported, not forced.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

from . import stamp

QUIET = 5 * 60            # No file may change for this long before publishing.
HEADLINES_EVERY = 3 * 3600  # Headline-only changes are batched.
PUSH_RETRY = 10 * 60
HEADLINES = 'data/auto_collected.json'


class GitError(RuntimeError):
    pass


def git_executable():
    """Git from PATH, or from its standard Windows folders when the launcher's PATH omits it."""
    found = shutil.which('git')
    if found:
        return found
    for base in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)', 'LocalAppData'):
        folder = os.environ.get(base)
        for parts in (('Git', 'cmd', 'git.exe'), ('Programs', 'Git', 'cmd', 'git.exe')):
            if folder and Path(folder, *parts).is_file():
                return str(Path(folder, *parts))
    raise GitError('Git was not found on this computer, so changes cannot be published. Install Git or add it to PATH.')


def git(root, *args, timeout=120):
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never'}
    done = subprocess.run([git_executable(), '-c', 'core.quotepath=false', *args], cwd=root, env=env, timeout=timeout,
                          capture_output=True, text=True, encoding='utf-8', errors='replace',
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if done.returncode:
        raise GitError((done.stderr or done.stdout).strip()[-400:])
    return done.stdout


def changed_paths(root):
    paths = []
    for entry in git(root, 'status', '--porcelain', '-uall', '-z').split('\0'):
        if len(entry) > 3 and entry[2] == ' ':
            paths.append(entry[3:])
    return sorted(set(paths))


def fingerprint(root, paths):
    parts = []
    for path in paths:
        try:
            info = (Path(root) / path).stat()
            parts.append(f'{path}:{info.st_mtime_ns}:{info.st_size}')
        except OSError:
            parts.append(f'{path}:deleted')
    return hashlib.sha256('\n'.join(parts).encode()).hexdigest()


def run_checks(root):
    """The same test suite as the README, in a separate process."""
    env = {**os.environ, 'RECONSTRUCTION_AUTO_UPDATE': '0',
           'PYTHONPATH': os.pathsep.join(path for path in sys.path if path), 'PYTHONIOENCODING': 'utf-8'}
    done = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=root, env=env,
                          timeout=900, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    failures = [line for line in done.stderr.splitlines() if line.startswith(('FAIL:', 'ERROR:'))]
    return done.returncode == 0, '; '.join(failures)[:400] or done.stderr.strip()[-300:]


def summary(paths):
    folders = sorted({path.split('/')[0] if '/' in path else path for path in paths})
    return f"Auto-update: {len(paths)} file{'s' if len(paths) != 1 else ''} ({', '.join(folders[:6])}{'…' if len(folders) > 6 else ''})"


def push(root, state, now):
    try:
        git(root, 'push', 'origin', 'HEAD')
        state.update(pushed_at=stamp(now), commit=git(root, 'rev-parse', '--short', 'HEAD').strip(),
                     status='published', detail='')
        state.pop('push_retry', None)
    except (GitError, subprocess.TimeoutExpired) as exc:
        state.update(status='push_failed', detail=str(exc)[:400], push_retry=now + PUSH_RETRY)


_last_run = {}


def run(root, state, now, checks=run_checks, every=30):
    root = Path(root)
    if now - _last_run.get(root, float('-inf')) < every:
        return  # Git is consulted twice a minute, not on every five-second pass.
    _last_run[root] = now
    try:
        git_dir = root / '.git'
        if not git_dir.exists() or any((git_dir / name).exists() for name in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply')):
            return
        git(root, 'symbolic-ref', '-q', 'HEAD')  # Never publish from a detached checkout.
        paths = changed_paths(root)
    except (GitError, OSError, subprocess.TimeoutExpired) as exc:
        state.update(status='unavailable', detail=str(exc)[:300])
        return
    state.pop('error', None)
    if not paths:
        state.pop('seen', None)
        try:
            ahead = int(git(root, 'rev-list', '--count', '@{u}..HEAD').strip() or 0)
        except (GitError, ValueError, subprocess.TimeoutExpired):
            ahead = 0
        if ahead and now >= state.get('push_retry', 0):
            push(root, state, now)  # Also retries a push that failed earlier.
        elif not ahead and state.get('status') != 'published':
            state.update(status='idle', detail='')
        return
    current = fingerprint(root, paths)
    if current != state.get('seen'):
        state.update(seen=current, seen_at=now, status='waiting', detail=f'{len(paths)} changed files')
        return
    if now - state.get('seen_at', now) < QUIET or current == state.get('failed'):
        return
    if paths == [HEADLINES] and now - state.get('committed_at_seconds', 0) < HEADLINES_EVERY:
        return
    passed, detail = checks(root)
    if not passed:
        state.update(failed=current, status='checks_failed', detail=detail, checked_at=stamp(now))
        return
    paths = changed_paths(root)
    if fingerprint(root, paths) != current:
        return  # Files changed while the checks ran; wait for them to settle again.
    try:
        git(root, 'add', '-A')
        git(root, 'commit', '-m', summary(paths))
    except (GitError, subprocess.TimeoutExpired) as exc:
        state.update(status='commit_failed', detail=str(exc)[:400], failed=current)
        return
    state.update(committed_at=stamp(now), committed_at_seconds=now, files=len(paths))
    state.pop('failed', None)
    push(root, state, now)
