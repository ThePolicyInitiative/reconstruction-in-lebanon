(() => {
  'use strict';
  const M=window.PoliticalGraphModel, root=document.getElementById('political-graphs');
  let data, lang=new URLSearchParams(location.search).get('lang')==='ar'?'ar':'en';
  let layer='parties', view='compare', query='', coverage='documented', topic='', page=0, selected=null;
  const pins=new Set(), pageSize=12;
  let pinnedOnly=false, returnFocus=null, filtersOpen=false;
  const W={
    title:['Political positions on reconstruction','المواقف السياسية من الإعمار'],
    intro:['Compare dated statements on rebuilding, arms and funding. Each actor can have several documented positions.','قارن التصريحات المؤرخة حول الإعمار والسلاح والتمويل. يمكن لكل جهة أن تتبنى عدة مواقف موثقة.'],
    parties:['Parties','الأحزاب'],deputies:['MPs','النواب'],ministers:['Cabinet','الحكومة'],
    compare:['Compare positions','مقارنة المواقف'],charts:['Topic charts','رسوم المواضيع'],
    reconstruction:['Reconstruction','الإعمار'],arms:['Arms','السلاح'],financing:['Financing','التمويل'],
    roster:['Names in directory','الأسماء في الدليل'],documented:['With coded evidence','لديهم أدلة مصنفة'],missing:['Without coded evidence','دون أدلة مصنفة'],
    evidence:['Read evidence','قراءة الأدلة'],unknown:['Not yet coded','لم يُصنّف بعد'],
    search:['Find a party or person','ابحث عن حزب أو شخص'],placeholder:['Name in English or Arabic','الاسم بالعربية أو الإنكليزية'],
    searchFilters:['Search & filters','البحث والتصفية'],filtered:['Filters applied','تصفية مفعلة'],
    show:['Evidence coverage','تغطية الأدلة'],all:['Every name','كل الأسماء'],documentedOnly:['With documented positions','بمواقف موثقة'],incomplete:['At least one topic not coded','موضوع واحد على الأقل غير مصنف'],
    topic:['Filter by position','تصفية حسب الموقف'],allTopics:['All positions','كل المواقف'],
    reset:['Reset filters','إلغاء التصفية'],matches:['matching names','أسماء مطابقة'],
    download:['Download comparison · CSV','تنزيل المقارنة · CSV'],
    source:['Source','المصدر'],sources:['sources','مصادر'],latest:['Latest cited','أحدث استشهاد'],
    pin:['Select to compare','اختيار للمقارنة'],selected:['Selected','المختار'],clear:['Clear selection','إلغاء الاختيار'],selectionLimit:['Select up to four names.','اختر أربعة أسماء كحد أقصى.'],
    previous:['Previous','السابق'],next:['Next','التالي'],noMatches:['No matches. Clear a filter or try another name.','لا توجد نتائج. ألغِ أحد المرشحات أو جرّب اسماً آخر.'],
    coverageNote:['An uncoded entry is a research gap, not evidence of silence. Personal positions are never inferred from party membership.','الاسم غير المصنف يعكس نقصاً بحثياً ولا يثبت غياب التصريحات. لا يُستنتج موقف الفرد من انتمائه الحزبي.'],
    method:['Scope & coding','النطاق وطريقة التصنيف'],
    methodText:['Topics overlap. Categories describe the cited statements, not scores, rankings or verified current policy. A person is counted once per category and may appear in several categories; do not add the bars. The three subjects are shown separately because security conditions can overlap with reconstruction positions.','تتداخل المواضيع. تصف الفئات التصريحات المستشهد بها، وليست درجات أو ترتيباً أو سياسة حالية متحققاً منها. يُحتسب الشخص مرة واحدة في كل فئة وقد يظهر في عدة فئات؛ لا تُجمع الأشرطة. تُعرض المواضيع الثلاثة منفصلة لأن الشروط الأمنية قد تتداخل مع مواقف الإعمار.'],
    dated:['Statements retain their original dates. Funding proposals and announcements do not establish payments.','تحتفظ التصريحات بتواريخها الأصلية. لا تثبت المقترحات وإعلانات التمويل حصول مدفوعات.'],
    baseline:['Baseline review','المراجعة الأساسية'],additional:['Additional evidence & topic review','مراجعة الأدلة والمواضيع الإضافية'],rosterDate:['Roster checked','مراجعة اللوائح'],
    chartNote:['Bars count distinct names in the filtered results. Select a category to compare its members.','تعدّ الأشرطة الأسماء غير المكررة ضمن النتائج المصفاة. اختر فئة لمقارنة أعضائها.'],
    chartOverlap:['Categories overlap; bars cannot be added. Missing coding is shown separately.','تتداخل الفئات؛ لا تُجمع الأشرطة. يُعرض غياب التصنيف بشكل منفصل.'],
    chartMissing:['No coding on this subject','دون تصنيف في هذا الموضوع'],
    profile:['Profile / roster source','مصدر التعريف أو اللائحة'],close:['Close evidence','إغلاق الأدلة'],
    timeline:['Collected statements · newest first','التصريحات المجمعة · الأحدث أولاً'],
    topicEvidence:['Evidence behind the topic labels','أدلة تصنيف المواضيع'],
    archive:['Earlier statement archive','أرشيف التصريحات السابق'],json:['Download all research · JSON','تنزيل كامل البحث · JSON'],
    noEvidence:['No statements have been coded for this entry yet. This does not establish that no relevant statements exist.','لم تُصنّف تصريحات لهذا الاسم بعد. لا يثبت ذلك عدم وجود تصريحات ذات صلة.'],
    expand:['Read summaries','قراءة الملخصات'],allResearch:['Directory includes parties and movements; it is not an exhaustive register of active parties. MPs and cabinet use the dated saved rosters.','يشمل الدليل أحزاباً وحركات ولا يمثل سجلاً شاملاً للأحزاب الناشطة. تستند لوائح النواب والحكومة إلى النسخ المحفوظة المؤرخة.'],
    imageSource:['Image source','مصدر الصورة'],error:['Could not load the comparison. Reload to retry.','تعذر تحميل المقارنة. أعد تحميل الصفحة.'],
    pinHint:['Select up to four names for a focused comparison.','اختر حتى أربعة أسماء لمقارنة مركزة.'],
    scopeHint:['The filter selects actors; all their coded positions remain visible.','يختار المرشح الجهات؛ وتبقى كل مواقفها المصنفة ظاهرة.'],
  };
  const t=k=>W[k]?.[lang==='ar'?1:0]||k;
  const local=v=>typeof v==='string'?v:v?.[lang]||v?.en||'';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const url=v=>{try{const u=new URL(v);return u.protocol==='https:'?u.href:'#';}catch{return '#';}};
  const date=v=>new Intl.DateTimeFormat(lang==='ar'?'ar-LB':'en-GB',{day:'numeric',month:'short',year:'numeric'}).format(new Date(v+'T12:00:00Z'));
  const cat=(axis,id)=>data.categories[axis].find(c=>c.id===id);
  const list=()=>data.entities.filter(e=>e.layer===layer);
  const result=()=>M.topicFilter(data.entities,{layer,query,coverage,topic}).filter(e=>!pinnedOnly||pins.has(e.id));
  const refs=e=>[...new Set(M.axes.flatMap(a=>M.stances(e,a).flatMap(p=>p.sources)))];
  const latest=e=>refs(e).map(id=>data.sources[id].date).sort().at(-1);
  const portrait=e=>{
    const im=e.layer==='parties'?e.symbol:e.portrait;
    return /^(symbols|portraits)\/[a-z0-9-]+\.(png|jpg|webp|svg)$/.test(im?.path||'')?`<img class="identity-image ${e.layer==='parties'?'':'portrait'}" src="${esc(im.path)}" alt="" loading="lazy">`:'<span class="identity-placeholder" aria-hidden="true">—</span>';
  };
  function sourceLink(id){const s=data.sources[id];return `<a href="${url(s.url)}" target="_blank" rel="noopener noreferrer">${esc(local(s.publisher))} · <bdi>${date(s.date)}</bdi> ↗</a>`;}
  function positionCell(e,axis){
    const ps=M.stances(e,axis),cats=[...new Set(ps.map(p=>p.category))];
    if(!ps.length)return `<span class="unknown">${t('unknown')}</span>`;
    return `<div class="position-tags">${cats.map(id=>`<span class="position-tag">${esc(local(cat(axis,id).label))}</span>`).join('')}</div><details class="summaries"><summary>${t('expand')}</summary>${ps.map(p=>`<p>${esc(local(p.reason))}</p><div class="inline-sources">${p.sources.map(sourceLink).join('')}</div>`).join('')}</details>`;
  }
  function comparison(rows){
    page=Math.min(page,Math.max(0,Math.ceil(rows.length/pageSize)-1));
    return `<div class="comparison-table" role="table" aria-label="${t('compare')}"><div class="comparison-head" role="row"><span role="columnheader">${t(layer)}</span>${M.axes.map(a=>`<span role="columnheader">${t(a)}</span>`).join('')}</div>${rows.slice(page*pageSize,(page+1)*pageSize).map(e=>`<article class="comparison-row" role="row" data-entity="${e.id}"><div role="cell" class="identity"><div class="identity-top">${portrait(e)}<button class="name-button" data-evidence="${e.id}">${esc(local(e.name))}</button></div><small>${esc(local(e.role))}</small><label class="pin"><input type="checkbox" data-pin="${e.id}" ${pins.has(e.id)?'checked':''}>${t('pin')}</label><button class="evidence-button" data-evidence="${e.id}">${t('evidence')} · ${refs(e).length}</button>${latest(e)?`<small>${t('latest')}: <bdi>${date(latest(e))}</bdi></small>`:''}</div>${M.axes.map(axis=>`<div role="cell" class="position-cell" data-label="${t(axis)}">${positionCell(e,axis)}</div>`).join('')}</article>`).join('')}</div>${rows.length>pageSize?`<nav class="pagination" aria-label="Pagination"><button data-page="-1" ${page===0?'disabled':''}>${t('previous')}</button><span>${page+1} / ${Math.ceil(rows.length/pageSize)}</span><button data-page="1" ${(page+1)*pageSize>=rows.length?'disabled':''}>${t('next')}</button></nav>`:''}`;
  }
  function charts(rows){
    return `<p class="chart-note">${t('chartNote')} ${t('chartOverlap')}</p><div class="topic-charts">${M.axes.map(axis=>{const groups=M.topicCounts(rows,axis,data.categories);return `<section class="topic-chart"><h2>${t(axis)}</h2><p>${rows.length} ${t('matches')}</p>${groups.map(c=>`<button class="topic-bar" data-topic="${axis}:${c.id}" ${c.entities.length?'':'disabled'}><span class="bar-name">${esc(local(c.label))}</span><span class="bar-track"><i style="width:${rows.length?100*c.entities.length/rows.length:0}%"></i></span><b>${c.entities.length}</b></button>`).join('')}<p class="chart-unknown">${t('chartMissing')}: <b>${rows.filter(e=>!M.stances(e,axis).length).length}</b> / ${rows.length}</p></section>`;}).join('')}</div>`;
  }
  function exportCSV(){
    const rows=[['Name','Layer','Subject','Category','Summary','Earliest source','Latest source','Source URLs']];
    for(const e of result()) for(const axis of M.axes){const ps=M.stances(e,axis);if(!ps.length)rows.push([local(e.name),layer,t(axis),t('unknown'),'','','','']);for(const p of ps){const ss=p.sources.map(id=>data.sources[id]),dates=ss.map(s=>s.date).sort();rows.push([local(e.name),layer,t(axis),local(cat(axis,p.category).label),local(p.reason),dates[0],dates.at(-1),ss.map(s=>s.url).join(' | ')]);}}
    download('\ufeff'+rows.map(row=>row.map(v=>'"'+String(v).replace(/^([=+@-])/,'\'$1').replace(/"/g,'""')+'"').join(',')).join('\r\n'),'text/csv;charset=utf-8',`political-comparison-${layer}-${lang}.csv`);
  }
  function download(text,type,name){const u=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  function renderResults(){
    const rows=result();
    document.getElementById('match-count').textContent=`${rows.length} ${t('matches')} · ${t('scopeHint')}`;
    document.getElementById('results').innerHTML=rows.length?(view==='compare'?comparison(rows):charts(rows)):`<p class="empty">${t('noMatches')}</p>`;
    document.getElementById('pin-count').textContent=`${t('selected')} (${pins.size})`;
    document.getElementById('pin-count').setAttribute('aria-pressed',String(pinnedOnly));
    document.getElementById('pin-count').disabled=!pins.size;
    document.getElementById('filter-label').textContent=t('searchFilters')+((query||topic||coverage!=='documented')?' · '+t('filtered'):'');
  }
  function render(){
    if(!data)return;
    document.documentElement.lang=lang;document.documentElement.dir=lang==='ar'?'rtl':'ltr';
    document.title=t('title');
    const es=list(),known=es.filter(e=>refs(e).length).length;
    root.innerHTML=`<main class="political-page" data-mode="${view}"><header class="political-intro"><p class="eyebrow">${lang==='ar'?'مواقف الأحزاب والنواب والحكومة':'PARTIES · PARLIAMENT · CABINET'}</p><h1>${t('title')}</h1><p>${t('intro')}</p></header>
      <div class="roster-overview"><nav class="layer-tabs" aria-label="${t('roster')}">${['parties','deputies','ministers'].map(l=>`<button data-layer="${l}" aria-pressed="${l===layer}">${t(l)} <b>${data.entities.filter(e=>e.layer===l).length}</b></button>`).join('')}</nav>
      <section class="coverage-strip" aria-label="${t('show')}"><div><b><bdi>${known} / ${es.length}</bdi></b><span>${t('documented')}</span></div><div><b>${es.length-known}</b><span>${t('missing')}</span></div></section></div><p class="coverage-note">${t('coverageNote')}</p>
      <div class="view-tabs"><button data-view="compare" aria-pressed="${view==='compare'}">${t('compare')}</button><button data-view="charts" aria-pressed="${view==='charts'}">${t('charts')}</button></div>
      <details class="filter-panel" id="filter-panel" ${filtersOpen?'open':''}><summary id="filter-label">${t('searchFilters')}</summary><div class="comparison-filters"><label>${t('search')}<input id="name-search" type="search" placeholder="${t('placeholder')}" value="${esc(query)}"></label><label>${t('show')}<select id="coverage">${[['documented','documentedOnly'],['all','all'],['missing','incomplete']].map(([v,k])=>`<option value="${v}" ${v===coverage?'selected':''}>${t(k)}</option>`).join('')}</select></label><label>${t('topic')}<select id="topic"><option value="">${t('allTopics')}</option>${M.axes.map(a=>`<optgroup label="${t(a)}">${data.categories[a].map(c=>`<option value="${a}:${c.id}" ${topic===a+':'+c.id?'selected':''}>${esc(local(c.label))}</option>`).join('')}</optgroup>`).join('')}</select></label></div></details>
      <div class="actions"><button id="pin-count" aria-pressed="${pinnedOnly}"></button><button data-action="clear-pins">${t('clear')}</button><button data-action="reset">${t('reset')}</button><button data-action="csv">${t('download')}</button></div><p class="hint">${t('pinHint')}</p><p id="match-count" class="result-count" role="status" aria-live="polite"></p><p id="selection-message" role="status" aria-live="polite"></p><div id="results"></div>
      <details class="method"><summary>${t('method')}</summary><p>${t('methodText')}</p><p>${t('dated')}</p><p>${t('allResearch')}</p><p>${t('baseline')}: ${date(data.statementsReviewed)} · ${t('additional')}: ${date(data.topicReview)} · ${t('rosterDate')}: ${date(data.rosterReviewed)}</p><div class="method-actions"><a href="archive.html?lang=${lang}">${t('archive')}</a><button data-action="json">${t('json')}</button></div></details>
      <dialog id="evidence-dialog" aria-labelledby="evidence-name"></dialog></main>`;
    renderResults();
  }
  function showEvidence(id,trigger){
    selected=id;returnFocus=trigger;const e=data.entities.find(e=>e.id===id),dialog=document.getElementById('evidence-dialog');
    const statements=[...new Set([...(e.statementIds||[]),...refs(e)])].map(ref=>data.sources[ref]).filter(Boolean).sort((a,b)=>b.date.localeCompare(a.date));
    const im=e.symbol||e.portrait;
    dialog.innerHTML=`<header class="dialog-heading"><div>${portrait(e)}<h2 id="evidence-name">${esc(local(e.name))}</h2></div><button data-close aria-label="${t('close')}">×</button></header><div class="dialog-body"><p>${esc(local(e.role))}</p>${e.scope?`<p class="scope">${esc(local(e.scope))}</p>`:''}<p class="hint">${t('dated')}</p><p><a href="${url(e.rosterUrl)}" target="_blank" rel="noopener noreferrer">${t('profile')} ↗</a>${im?.sourceUrl?` · <a href="${url(im.sourceUrl)}" target="_blank" rel="noopener noreferrer">${t('imageSource')} ↗</a>`:''}</p><h3>${t('topicEvidence')}</h3><div class="evidence-topics">${M.axes.map(a=>`<section><h4>${t(a)}</h4>${positionCell(e,a)}</section>`).join('')}</div><h3>${t('timeline')} · ${statements.length}</h3><ol class="statement-timeline">${statements.map(s=>`<li><time datetime="${s.date}">${date(s.date)}</time><strong>${esc(local(s.speaker))}</strong><p>${esc(local(s.summary))}</p>${s.attribution?`<p class="scope">${esc(local(s.attribution))}</p>`:''}${sourceLink(s.id)}</li>`).join('')}</ol>${statements.length?'':`<p>${t('noEvidence')}</p>`}</div>`;
    dialog.showModal();dialog.querySelector('[data-close]').focus();
    dialog.addEventListener('close',()=>{selected=null;returnFocus?.focus({preventScroll:true});},{once:true});
  }
  root.addEventListener('input',e=>{if(e.target.id==='name-search'){query=e.target.value;page=0;renderResults();}});
  root.addEventListener('toggle',e=>{if(e.target.id==='filter-panel')filtersOpen=e.target.open;},true);
  root.addEventListener('change',e=>{
    if(e.target.id==='coverage'){coverage=e.target.value;page=0;renderResults();}
    if(e.target.id==='topic'){topic=e.target.value;page=0;renderResults();}
    if(e.target.matches('[data-pin]')){const id=e.target.dataset.pin;if(e.target.checked&&pins.size>=4){e.target.checked=false;document.getElementById('selection-message').textContent=t('selectionLimit');return;}e.target.checked?pins.add(id):pins.delete(id);document.getElementById('selection-message').textContent='';if(!pins.size)pinnedOnly=false;renderResults();root.querySelector(`[data-pin="${id}"]`)?.focus({preventScroll:true});}
  });
  root.addEventListener('click',e=>{
    const b=e.target.closest('button');if(!b)return;
    if(b.dataset.layer){layer=b.dataset.layer;page=0;pins.clear();pinnedOnly=false;query='';topic='';coverage='documented';render();root.querySelector(`[data-layer="${layer}"]`).focus();}
    if(b.dataset.view){view=b.dataset.view;page=0;render();root.querySelector(`[data-view="${view}"]`).focus();}
    if(b.dataset.evidence)showEvidence(b.dataset.evidence,b);
    if(b.hasAttribute('data-close'))document.getElementById('evidence-dialog').close();
    if(b.dataset.topic){topic=b.dataset.topic;view='compare';page=0;render();document.getElementById('filter-label').focus();}
    if(b.dataset.page){page+=Number(b.dataset.page);renderResults();document.getElementById('results').scrollIntoView({block:'start'});}
    if(b.id==='pin-count'){pinnedOnly=!pinnedOnly;query='';topic='';coverage='all';page=0;render();document.getElementById('pin-count').focus({preventScroll:true});}
    if(b.dataset.action==='clear-pins'){pins.clear();pinnedOnly=false;renderResults();}
    if(b.dataset.action==='reset'){query='';coverage='documented';topic='';pinnedOnly=false;page=0;render();}
    if(b.dataset.action==='csv')exportCSV();
    if(b.dataset.action==='json')download(JSON.stringify(data,null,2),'application/json','lebanon-political-positions.json');
  });
  addEventListener('message',e=>{if(e.source===window.parent&&e.data?.type==='streamlit:render'){const next=e.data.args?.language;if(['en','ar'].includes(next)&&next!==lang){lang=next;render();}}});
  fetch('positions.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(value=>{data=value;M.validate(data);render();}).catch(()=>{root.textContent=t('error');});
})();
