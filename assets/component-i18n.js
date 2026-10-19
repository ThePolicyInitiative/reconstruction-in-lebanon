/* Local presentation only: IDs, source records, links and image pixels are unchanged. */
(() => {
  const originalText = new WeakMap();
  const originalAttributes = new WeakMap();
  let language = 'en', words = {}, pattern, ready = false, scheduled = false;
  const escaped = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const translate = text => {
    if (language !== 'ar' || !text || /^https?:\/\//.test(text)) return text;
    const key = text.replace(/\s+/g, ' ').trim();
    if (Object.prototype.hasOwnProperty.call(words, key))
      return text.slice(0, text.length-text.trimStart().length) + words[key] + text.slice(text.trimEnd().length);
    return text.replace(pattern, match => words[match])
      .replace(/(\$[\d,.]+)\s*[mM]\b/g, '$1 مليون')
      .replace(/(\$[\d,.]+)\s*[kK]\b/g, '$1 ألف');
  };
  const observer = new MutationObserver(() => schedule());
  function apply() {
    scheduled = false;
    if (!ready) return;
    observer.disconnect();
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: node => node.parentElement?.closest('script,style,svg,code') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    while (walker.nextNode()) {
      const node = walker.currentNode;
      let saved = originalText.get(node);
      if (!saved || node.textContent !== saved.last) saved = {source:node.textContent};
      saved.last = translate(saved.source);
      if (node.textContent !== saved.last) node.textContent = saved.last;
      originalText.set(node, saved);
    }
    for (const element of document.querySelectorAll('[aria-label],[title],[alt],[placeholder]')) {
      if (element.closest('svg,script,style')) continue;
      let values = originalAttributes.get(element) || {};
      for (const attribute of ['aria-label','title','alt','placeholder']) {
        if (!element.hasAttribute(attribute)) continue;
        const value = element.getAttribute(attribute);
        let saved = values[attribute];
        if (!saved || value !== saved.last) saved = {source:value};
        saved.last = translate(saved.source);
        if (value !== saved.last) element.setAttribute(attribute,saved.last);
        values[attribute] = saved;
      }
      originalAttributes.set(element,values);
    }
    for (const quote of document.querySelectorAll('blockquote')) {
      if (!quote.dataset.originalLanguage) quote.dataset.originalLanguage = quote.lang || 'en';
      const translated = language === 'ar' && quote.dataset.originalLanguage !== 'ar';
      quote.dataset.translated = String(translated);
      quote.lang = translated ? 'ar' : quote.dataset.originalLanguage;
      quote.dir = quote.lang === 'ar' ? 'rtl' : 'ltr';
    }
    document.title = translate(document.title);
    observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['aria-label','title','alt','placeholder']});
  }
  function schedule() {
    if (!scheduled) { scheduled = true; requestAnimationFrame(apply); }
  }
  addEventListener('message', event => {
    if (event.source === window.parent && event.data?.type === 'streamlit:render') {
      language = event.data.args?.language === 'ar' ? 'ar' : 'en';
      schedule();
    }
  });
  fetch('./ar.json').then(response => {
    if (!response.ok) throw Error('Arabic catalog unavailable');
    return response.json();
  }).then(catalog => {
    words = catalog;
    pattern = new RegExp('(?<![A-Za-z])(?:'+Object.keys(words).sort((a,b)=>b.length-a.length).map(escaped).join('|')+')(?![A-Za-z])','g');
    ready = true;
    apply();
  }).catch(error => console.error(error.message));
})();
