"""Per-session Arabic presentation. Source data, widget values and URLs stay intact."""
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import streamlit as native
from streamlit.delta_generator import DeltaGenerator

ROOT = Path(__file__).resolve().parent
TAB_LABELS = ['Government response', 'Budget', 'Restrictions & funding gaps', 'Tenders', 'Gazette', 'What parties are saying', 'What countries are saying', 'Evidence of destruction']


def language():
    return native.session_state.get('language', 'en')


def catalog():
    path = ROOT/'locales/ar.json'
    return _catalog(path.stat().st_mtime_ns) if path.exists() else {}


@lru_cache(maxsize=1)
def _catalog(version):
    return json.loads((ROOT/'locales/ar.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def _phrase_pattern(version):
    words = _catalog(version)
    keys = [key for key in sorted(words, key=len, reverse=True)
            if key and '<' not in key and not key.startswith('http')]
    return re.compile(r'(?<![A-Za-z])(?:' + '|'.join(map(re.escape, keys)) + r')(?![A-Za-z])')


def translate(text, lang=None):
    if not isinstance(text, str) or (lang or language()) != 'ar' or text.startswith(('http://', 'https://')):
        return text
    key = re.sub(r'\s+', ' ', text).strip()
    words = catalog()
    if key in words:
        return text[:len(text)-len(text.lstrip())] + words[key] + text[len(text.rstrip()):]
    if '\n' in text:
        return '\n'.join(translate(line, 'ar') for line in text.split('\n'))
    text = re.sub(r'(\$[\d,.]+)\s*[mM]\b', r'\1 مليون', text)
    text = re.sub(r'(\$[\d,.]+)\s*[kK]\b', r'\1 ألف', text)
    # Compound labels and changing counts reuse catalog phrases. Longest
    # matches win, without modifying URLs, identifiers, or numeric values.
    if words and re.search('[A-Za-z]', text):
        text = _phrase_pattern((ROOT/'locales/ar.json').stat().st_mtime_ns).sub(lambda match: words[match[0]], text)
    return text


class ArabicHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.result = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script', 'svg'):
            self.skip += 1
        if not self.skip and tag in ('article','section','header') and not any(key == 'lang' for key, _ in attrs):
            attrs = [*attrs, ('lang', 'ar')]
        attrs = [(key, translate(value) if key in ('aria-label', 'title', 'alt', 'placeholder') and not self.skip else value) for key, value in attrs]
        self.result.append('<' + tag + ''.join(' '+key if value is None else f' {key}="{escape(value, quote=True)}"' for key, value in attrs) + '>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.result[-1] = self.result[-1][:-1] + '/>'
        if tag in ('style', 'script', 'svg'):
            self.skip -= 1
    def handle_endtag(self, tag):
        self.result.append(f'</{tag}>')
        if tag in ('style', 'script', 'svg') and self.skip:
            self.skip -= 1
    def handle_data(self, text):
        self.result.append(text if self.skip else escape(translate(text), quote=False))
    def handle_entityref(self, name):
        self.result.append(f'&{name};')
    def handle_charref(self, name):
        self.result.append(f'&#{name};')
    def handle_comment(self, text):
        self.result.append(f'<!--{text}-->')


def translate_html(text):
    if language() != 'ar' or not isinstance(text, str):
        return text
    # Decode text entities before translation but keep attribute values safe.
    parser = ArabicHTML()
    parser.convert_charrefs = True
    parser.feed(text)
    return ''.join(parser.result)


def initialize_language():
    if 'language' not in native.session_state:
        native.session_state['language'] = 'ar' if native.query_params.get('lang') == 'ar' else 'en'


def toggle_language():
    old = language()
    new = 'en' if old == 'ar' else 'ar'
    selected = native.session_state.get('reconstruction_section', TAB_LABELS[0])
    canonical = next((label for label in TAB_LABELS if selected in (label, translate(label, 'ar'))), TAB_LABELS[0])
    native.session_state['language'] = new
    native.session_state['reconstruction_section'] = translate(canonical, new)
    native.query_params['lang'] = new


class LocalizedStreamlit:
    """Translate only presentation arguments; callbacks and stored values stay original."""
    def __init__(self, target):
        self.target = target
    def __enter__(self):
        self.target.__enter__()
        return self
    def __exit__(self, *args):
        return self.target.__exit__(*args)
    def __getattr__(self, name):
        method = getattr(self.target, name)
        supported = {'html','markdown','write','text','caption','title','header','subheader','info','warning','error','success','expander','button','link_button','download_button','spinner','metric','text_input','checkbox','selectbox','multiselect','tabs','columns','container','dataframe','table','altair_chart'}
        if name not in supported:
            return method
        def call(*args, **kwargs):
            args = list(args)
            choice_key = kwargs.get('key') if name in ('selectbox','multiselect') else None
            if choice_key:
                # Streamlit can retain the old formatted selected label when
                # only format_func changes. Remount per language, retaining the
                # underlying value in state independent of widget cleanup.
                choices = native.session_state.setdefault('_localized_choices', {})
                widget_key = choice_key if language() == 'en' else choice_key + '__ar'
                saved = choices.get(choice_key)
                if saved and (saved['language'] != language() or widget_key not in native.session_state):
                    native.session_state[widget_key] = saved['value']
                kwargs['key'] = widget_key
            if language() == 'ar':
                for field in ('label', 'help', 'placeholder'):
                    if field in kwargs:
                        kwargs[field] = translate(kwargs[field])
                if name in ('selectbox', 'multiselect'):
                    original_format = kwargs.get('format_func', str)
                    kwargs['format_func'] = lambda value: translate(original_format(value), 'ar')
                    if name == 'multiselect' and 'placeholder' not in kwargs:
                        kwargs['placeholder'] = 'اختر خيارات'
                if name == 'tabs' and args:
                    args[0] = [translate(label) for label in args[0]]
                elif name in ('html', 'markdown') and args and isinstance(args[0], str):
                    args[0] = translate_html(args[0]) if name == 'html' or kwargs.get('unsafe_allow_html') else translate(args[0])
                elif name not in ('columns','container','dataframe','table','altair_chart') and args:
                    args[0] = translate(args[0])
                if name in ('dataframe','table') and args:
                    import pandas as pd
                    if isinstance(args[0], pd.DataFrame):
                        frame = args[0].copy()
                        for column in frame.select_dtypes(include=['object','string']).columns:
                            frame[column] = frame[column].map(lambda value: translate(value) if isinstance(value, str) else value)
                        args[0] = frame
                        if name == 'dataframe':
                            config = dict(kwargs.get('column_config') or {})
                            for column in frame.columns:
                                setting = config.get(column)
                                setting = dict(setting) if isinstance(setting, dict) else {'label':setting or column}
                                setting['label'] = translate(setting.get('label') or column)
                                if setting.get('help'):
                                    setting['help'] = translate(setting['help'])
                                if isinstance(setting.get('type_config'), dict):
                                    setting['type_config'] = dict(setting['type_config'])
                                    if isinstance(setting['type_config'].get('display_text'), str):
                                        setting['type_config']['display_text'] = translate(setting['type_config']['display_text'])
                                config[column] = setting
                            kwargs['column_config'] = config
                        else:
                            args[0] = frame.rename(columns=translate)
                if name == 'altair_chart' and args:
                    import altair as alt
                    spec = args[0].to_dict()
                    def localize_chart(value):
                        if isinstance(value, dict):
                            return {key: translate(item) if key in ('title','label') and isinstance(item,str) else localize_chart(item) for key,item in value.items()}
                        if isinstance(value, list):
                            return [localize_chart(item) for item in value]
                        return value
                    spec = localize_chart(spec)
                    for rows in spec.get('datasets',{}).values():
                        for row in rows:
                            for key, value in row.items():
                                if isinstance(value,str):
                                    row[key] = translate(value)
                    for tooltip in spec.get('encoding',{}).get('tooltip',[]):
                        tooltip['title'] = translate(tooltip.get('title',tooltip.get('field','')))
                    args[0] = alt.Chart.from_dict(spec)
            result = method(*args, **kwargs)
            if choice_key:
                choices[choice_key] = {'language':language(), 'value':result}
            if isinstance(result, DeltaGenerator):
                return LocalizedStreamlit(result)
            if isinstance(result, (list,tuple)) and result and all(isinstance(item, DeltaGenerator) for item in result):
                return [LocalizedStreamlit(item) for item in result]
            return result
        return call


st = LocalizedStreamlit(native)
