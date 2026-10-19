"""Private Site service access, kept in the OS credential store or host secrets.

The credential is never included in source, snapshots, URLs or browser output.
Windows API contract: https://learn.microsoft.com/windows/win32/api/wincred/ns-wincred-credentialw
"""
import os

TARGET = 'TPI.Reconstruction.Gazette/lebanon-gazette-observatory.tpichatgpt.chatgpt.site'
ENV_NAME = 'GAZETTE_SITE_TOKEN'


def _windows_api():
    if os.name != 'nt':
        raise OSError('Windows credential storage is unavailable')
    import ctypes as c
    from ctypes import wintypes as w

    class Credential(c.Structure):
        _fields_ = [('Flags', w.DWORD), ('Type', w.DWORD), ('TargetName', w.LPWSTR),
                    ('Comment', w.LPWSTR), ('LastWritten', w.FILETIME),
                    ('CredentialBlobSize', w.DWORD), ('CredentialBlob', c.POINTER(c.c_ubyte)),
                    ('Persist', w.DWORD), ('AttributeCount', w.DWORD), ('Attributes', c.c_void_p),
                    ('TargetAlias', w.LPWSTR), ('UserName', w.LPWSTR)]

    api = c.WinDLL('advapi32', use_last_error=True)
    api.CredReadW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.POINTER(c.POINTER(Credential))]
    api.CredReadW.restype = w.BOOL
    api.CredWriteW.argtypes = [c.POINTER(Credential), w.DWORD]
    api.CredWriteW.restype = w.BOOL
    api.CredFree.argtypes = [c.c_void_p]
    api.CredFree.restype = None
    return c, api, Credential


def windows_token():
    if os.name != 'nt':
        return ''
    c, api, Credential = _windows_api()
    pointer = c.POINTER(Credential)()
    if not api.CredReadW(TARGET, 1, 0, c.byref(pointer)):
        return ''
    try:
        entry = pointer.contents
        return c.string_at(entry.CredentialBlob, entry.CredentialBlobSize).decode('utf-8')
    finally:
        api.CredFree(pointer)


def save_windows_token(token):
    """Called only by the explicit one-time connection setup, never by rendering."""
    raw = token.strip().encode('utf-8')
    if not raw or len(raw) > 2560:
        raise ValueError('Invalid Site service credential')
    c, api, Credential = _windows_api()
    buffer = (c.c_ubyte * len(raw)).from_buffer_copy(raw)
    entry = Credential()
    entry.Type = 1  # CRED_TYPE_GENERIC
    entry.TargetName = TARGET
    entry.Comment = 'Private Memo Gazette service access for Reconstruction in Lebanon'
    entry.CredentialBlobSize = len(raw)
    entry.CredentialBlob = c.cast(buffer, c.POINTER(c.c_ubyte))
    entry.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE: same Windows user, survives restart.
    entry.UserName = 'gazette-service'
    try:
        if not api.CredWriteW(c.byref(entry), 0):
            raise OSError('The Gazette connection could not be saved in Windows Credential Manager')
    finally:
        c.memset(buffer, 0, len(raw))


def site_token():
    value = os.environ.get(ENV_NAME, '').strip()
    if value:
        return value
    try:
        import streamlit as st
        value = str(st.secrets.get(ENV_NAME, '')).strip()
        if value:
            return value
    except (FileNotFoundError, KeyError):
        pass
    return windows_token()
