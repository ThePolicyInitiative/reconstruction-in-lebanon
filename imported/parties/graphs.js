(() => {
  'use strict';
  const M = window.PoliticalGraphModel;
  let data, lang = new URLSearchParams(location.search).get('lang') === 'ar' ? 'ar' : 'en';
  let layer = 'parties', selected = null, query = '', coverage = 'all', page = 0;
  const activeCells = {arms:null, financing:null};
  const columnFocus = {arms:'all', financing:'all'};
  const pageSize = 18;
  const root = document.getElementById('political-graphs');
  const W = {
    title:['Reconstruction & political positions','الإعمار والمواقف السياسية'],
    kicker:['WHAT PARTIES ARE SAYING','مواقف الأحزاب'],
    intro:['Two graphs. Three layers. Explore stated positions on reconstruction, arms and financing.','رسمان وثلاث طبقات لاستكشاف المواقف المعلنة من الإعمار والسلاح والتمويل.'],
    rosterDate:['Parliament & cabinet checked','مراجعة لوائح النواب والوزراء'],
    statementDate:['Statements reviewed','مراجعة التصريحات'],
    parties:['Parties','الأحزاب'],deputies:['Deputies','النواب'],ministers:['Ministers','الوزراء'],
    partiesSub:['Inside & outside Parliament','داخل البرلمان وخارجه'],
    deputiesSub:['All 128 MPs','جميع النواب الـ١٢٨'],ministersSub:['Full cabinet, including PM','كامل الحكومة، بما فيها رئيسها'],
    armsTitle:['Arms × reconstruction','السلاح × الإعمار'],financeTitle:['Financing × reconstruction','التمويل × الإعمار'],
    armsIntro:['Y: position on state control of arms','المحور العمودي: الموقف من حصر السلاح بالدولة'],
    financeIntro:['Y: reconstruction financing approach','المحور العمودي: مقاربة تمويل الإعمار'],
    reconstruction:['Reconstruction','الإعمار'],arms:['Arms','السلاح'],financing:['Financing','التمويل'],
    reconstructionAxis:['Reconstruction approach · categories, not scores','مقاربة الإعمار · فئات وليست درجات'],
    categoryGuide:['What the categories mean','ماذا تعني الفئات؟'],
    categoryExamples:['Examples','أمثلة'],
    reconstructionGuide:['X · What approach to reconstruction does the statement emphasise?','المحور الأفقي · ما مقاربة الإعمار التي يركز عليها التصريح؟'],
    armsGuide:['Y · Who should control arms, and through what process?','المحور العمودي · من يملك السلاح، وبأي مسار؟'],
    financingGuide:['Y · Which funding channels does the statement advocate?','المحور العمودي · ما مصادر التمويل التي يطرحها التصريح؟'],
    placed:['placed','مصنّف'],unplaced:['not yet placed','غير مصنّف بعد'],
    keyTitle:['Select a marker or a name to see its evidence','اختر علامة أو اسماً لعرض الأدلة'],
    categoryNote:['Categories, not numerical scores. Marker numbers identify names; small offsets separate overlapping markers.','فئات وصفية وليست درجات رقمية. أرقام العلامات لتعريف الأسماء، والإزاحة البسيطة تفصل العلامات المتداخلة.'],
    partyCategoryNote:['Party flags and emblems identify the markers; a short name is used when a current emblem is awaiting verification. Select a marker for its name and evidence. Small offsets separate parties in the same category.','تُعرّف الأعلام والشعارات علامات الأحزاب، ويُستخدم اسم مختصر حين يكون الشعار الحالي قيد التحقق. اختر علامة لعرض الاسم والأدلة. تفصل الإزاحة البسيطة الأحزاب الواقعة في الفئة نفسها.'],
    symbolCredits:['Flag & emblem credits','مصادر الأعلام والشعارات'],
    portraitSource:['Portrait source ↗','مصدر الصورة الشخصية ↗'],
    portraitNote:['Portraits identify each person. Select a photo for their name and dated evidence. Positions are never inferred from party membership.','تُعرّف الصور كل شخص. اختر صورة لعرض الاسم والأدلة المؤرخة. لا يُستنتج الموقف من الانتماء الحزبي.'],
    unknownArms:['Arms not yet coded','السلاح لم يُصنّف بعد'],
    unknownFinancing:['Financing not yet coded','التمويل لم يُصنّف بعد'],
    partial:['reconstruction only','الإعمار فقط'],
    bothAxes:['both axes documented','موثّق على المحورين'],
    railNote:['The separate dashed row shows a documented reconstruction position with no classified position on the other axis. It is not a fourth stance or a neutral score.','يعرض الصف المنفصل ذو الحدود المتقطعة موقفاً موثقاً من الإعمار دون تصنيف على المحور الآخر. وهو ليس موقفاً رابعاً ولا درجة حياد.'],
    noPoints:['No reconstruction positions coded in this layer yet.','لم تُصنّف مواقف الإعمار في هذه الطبقة بعد.'],
    noSelection:['Select a name to explore the evidence','اختر اسماً لاستكشاف الأدلة'],
    noSelectionText:['Every name remains in the directory, including entries that cannot yet be placed on a graph.','يبقى كل اسم في الدليل، بما في ذلك الأسماء التي لا تكفي الأدلة لتصنيفها على الرسم.'],
    rosterLink:['Profile / directory source ↗','مصدر التعريف أو الدليل ↗'],unknown:['Not yet coded','لم يُصنّف بعد'],
    unknownDetail:['This dataset has not yet coded a statement for this axis. Relevant statements may exist and still need review.','لم تُصنّف قاعدة البيانات تصريحاً لهذا المحور بعد. قد توجد تصريحات ذات صلة لا تزال بحاجة إلى مراجعة.'],
    researchPending:['Evidence review pending','مراجعة الأدلة غير مكتملة'],
    coverageNote:['“Not yet coded” describes a gap in this dataset. It does not mean that a party or person has said nothing.','«لم يُصنّف بعد» تعني وجود نقص في قاعدة البيانات، ولا تعني أن الحزب أو الشخص لم يدلِ بأي موقف.'],
    affiliationSource:['Speaker’s affiliation ↗','انتماء المتحدث ↗'],
    evidenceHeading:['Why this position? Read the dated statements','لماذا هذا التصنيف؟ راجع التصريحات المؤرخة'],
    personalRule:['An individual’s position is never filled in from their party or cabinet membership.','لا يُستنتج موقف الفرد من انتمائه الحزبي أو عضويته في الحكومة.'],
    emptyEvidence:['Evidence review is incomplete for this entry. Relevant statements have not yet been added and coded here. This is not a finding that no statements exist.','مراجعة الأدلة لهذا الاسم غير مكتملة. لم تُضف التصريحات ذات الصلة وتُصنّف هنا بعد. هذا لا يثبت عدم وجود تصريحات.'],
    datedNote:['Placements describe the cited statements at their dates, not a verified current position. Financing categories show advocated channels, not money received.','يصف التصنيف التصريحات في تواريخها، ولا يثبت الموقف الحالي. فئات التمويل تبين القنوات المطروحة، وليس الأموال المقبوضة.'],
    directory:['Explore every name','استكشف جميع الأسماء'],search:['Search names','ابحث عن اسم'],placeholder:['Type a name in English or Arabic…','اكتب اسماً بالعربية أو الإنكليزية…'],
    show:['Show','اعرض'],all:['All entries','جميع الأسماء'],armsFilter:['Both arms axes coded','المحوران مصنّفان في رسم السلاح'],financeFilter:['Both financing axes coded','المحوران مصنّفان في رسم التمويل'],missingFilter:['Some axes not yet coded','بعض المحاور لم تُصنّف بعد'],
    matches:['matching entries','نتيجة مطابقة'],of:['of','من'],previous:['Previous','السابق'],next:['Next','التالي'],
    missingArmsFilter:['Arms graph: incomplete coding','رسم السلاح: تصنيف غير مكتمل'],missingFinanceFilter:['Financing graph: incomplete coding','رسم التمويل: تصنيف غير مكتمل'],
    noMatches:['No matching names. Try a shorter name or change the filter.','لا توجد أسماء مطابقة. جرّب اسماً أقصر أو غيّر التصفية.'],
    knownLegend:['● coded with sources  ○ not yet coded','● مصنّف بمصادر  ○ لم يُصنّف بعد'],
    method:['How to read the graphs & sources','كيف تقرأ الرسوم والمصادر؟'],
    methodX:['Reconstruction categories distinguish security-first and unconditional rebuilding, urgent action, return and compensation, physical works, budget allocations, dedicated funds, institutional delivery and general recovery commitments.','تميز فئات الإعمار بين أولوية الأمن والإعمار دون شروط والتحرك العاجل والعودة والتعويضات والأعمال المادية واعتمادات الموازنة والصناديق المخصصة والتنفيذ المؤسسي والالتزامات العامة بالتعافي.'],
    methodArms:['Arms categories distinguish retention, dialogue, reciprocal steps, army phases, the state-monopoly principle, implementing disarmament, conditions for reconstruction aid and civilian transformation. Rejecting an aid-for-arms trade alone is not enough to code an arms position.','تميز فئات السلاح بين الاحتفاظ به والحوار والخطوات المتبادلة ومراحل الجيش ومبدأ الحصرية وتنفيذ نزع السلاح وشروط مساعدة الإعمار والتحول المدني. لا يكفي رفض مقايضة المساعدة بالسلاح وحده لتصنيف موقف من السلاح.'],
    methodFinance:['Funding categories distinguish budget allocations, existing reserves, party assistance, combined domestic and external resources, donor contributions, loans, Iranian contributions, investment, aid conditions and supervised grants. Proposed or expected funding is not a verified payment.','تميز فئات التمويل بين اعتمادات الموازنة والاحتياطيات والمساعدة الحزبية والجمع بين الموارد المحلية والخارجية ومساهمات المانحين والقروض والمساهمة الإيرانية والاستثمار وشروط المساعدة والمنح الخاضعة للرقابة. التمويل المقترح أو المتوقع ليس دفعة مؤكدة.'],
    methodParty:['Party placements use the named leaders or representatives shown in the evidence panel. They are not an average of all members or proof of unanimous party policy. Independents are included in the MPs layer.','تعتمد مواضع الأحزاب على تصريحات القيادات أو الممثلين المحددين في لوحة الأدلة. ليست متوسطاً لمواقف الأعضاء ولا إثباتاً للإجماع الحزبي. المستقلون مدرجون ضمن طبقة النواب.'],
    methodCoverage:['The directory includes all 128 MPs on the official Parliament list and all 24 cabinet members. The expanded party list covers parliamentary and non-parliamentary parties and movements in the cited directory, plus the existing archive and Project Watan. It is not an exhaustive legal register of Lebanon’s licensed parties; the present activity of smaller movements has not been individually verified.','يشمل الدليل النواب الـ١٢٨ في لائحة مجلس النواب الرسمية وأعضاء الحكومة الـ٢٤. وتشمل لائحة الأحزاب الموسعة أحزاباً وحركات داخل البرلمان وخارجه في الدليل المشار إليه، إضافة إلى الأرشيف السابق ومشروع وطن الإنسان. وهي ليست سجلاً قانونياً شاملاً لجميع الأحزاب المرخصة، ولم يُتحقق منفرداً من النشاط الحالي لكل حركة صغيرة.'],
    methodMissing:['A separate dashed row shows sourced reconstruction positions with the other axis not yet coded. Entries whose reconstruction statements have not yet been added and coded remain in the directory. Research is incomplete: absence here does not establish silence. No zero, middle score, party position or cabinet statement substitutes for a missing personal position. Each placement links to its own evidence.','يعرض الصف المتقطع مواقف الإعمار المسندة بمصادر حين لم يُصنّف المحور الآخر بعد. تبقى في الدليل الأسماء التي لم تُضف تصريحاتها عن الإعمار وتُصنّف بعد. البحث غير مكتمل: الغياب هنا لا يثبت الصمت. لا يُستعاض عن الموقف الشخصي غير المصنّف بصفر أو درجة وسطى أو موقف الحزب أو الحكومة. لكل تصنيف أدلته الخاصة.'],
    archive:['Full statement archive ↗','أرشيف التصريحات الكامل ↗'],parliament:['Official Parliament roster ↗','لائحة مجلس النواب الرسمية ↗'],cabinet:['Official cabinet roster ↗','لائحة الحكومة الرسمية ↗'],partySource:['Party directory ↗','دليل الأحزاب ↗'],
    download:['Download graph data','تنزيل بيانات الرسوم'],
    loadError:['The graphs could not load. Refresh the page to try again.','تعذر تحميل الرسوم. أعد تحميل الصفحة للمحاولة مجدداً.'],
    loading:['Loading the political graphs…','جارٍ تحميل الرسوم السياسية…'],
    layerOverview:['Evidence coverage in this layer','تغطية الأدلة في هذه الطبقة'],
    rosterTotal:['Names in directory','الأسماء في الدليل'],
    reconstructionCoded:['Reconstruction documented','موقف الإعمار موثّق'],
    completeBoth:['Placed on both graphs','مصنّف على الرسمين'],
    supportingStatements:['Distinct supporting statements','تصريحات داعمة غير مكررة'],
    latestCited:['Latest cited statement','أحدث تصريح مستشهد به'],
    earliestCited:['Earliest cited statement','أقدم تصريح مستشهد به'],
    evidencePeriod:['Cited statement period','فترة التصريحات المستشهد بها'],
    noReconstruction:['Reconstruction not yet coded','الإعمار لم يُصنّف بعد'],
    percentageNote:['Percentages use every name in this layer. The dashed row has reconstruction evidence only; names without a coded reconstruction position remain in the directory.','تُحسب النسب من جميع أسماء هذه الطبقة. يضم الصف المتقطع الأسماء ذات موقف الإعمار الموثّق فقط؛ وتبقى الأسماء دون موقف إعمار مصنّف في الدليل.'],
    cellsHint:['Select a cell count to see everyone in that category. Hover over or focus a flag or portrait for its evidence dates and reasoning.','اختر عدد الخانة لرؤية جميع الأسماء فيها. مرّر المؤشر أو انتقل بلوحة المفاتيح إلى علم أو صورة لرؤية تواريخ الأدلة وأسباب التصنيف.'],
    namesInCell:['Names in this category','الأسماء في هذه الفئة'],
    noNamesInCell:['No names are coded in this category.','لا توجد أسماء مصنّفة ضمن هذه الفئة.'],
    close:['Close','إغلاق'],
    viewEvidence:['Read the statements ↓','اقرأ التصريحات ↓'],
    selectedName:['Selected name','الاسم المحدد'],
    axisSources:['Supporting statements for this axis','التصريحات الداعمة لهذا المحور'],
    graphSources:['Distinct statements supporting these axes','تصريحات غير مكررة تدعم هذين المحورين'],
    distributions:['Category breakdown & exact figures','توزيع الفئات والأرقام الدقيقة'],
    distributionNote:['This breakdown includes everyone in the layer, even when their reconstruction position is not yet coded. Categories describe statements, not approval ratings or measured performance.','يشمل هذا التوزيع جميع أسماء الطبقة حتى إن لم يُصنّف موقفها من الإعمار. تصف الفئات التصريحات ولا تمثل نسب تأييد أو قياساً للأداء.'],
    chartTable:['Graph categories and names','فئات الرسم والأسماء'],
    count:['Count','العدد'],share:['Share of this layer','النسبة من هذه الطبقة'],
    names:['Names','الأسماء'],
    downloadFigures:['Download these graph figures · CSV','تنزيل أرقام هذا الرسم · CSV'],
    axesSupported:['Supports these axes','يدعم هذه المحاور'],
    statements:['statements','تصريحات'],
    positionSummary:['Position summary','ملخص الموقف'],
    plottedCategory:['Graph category','فئة الرسم'],
    graphDisplay:['Graph display','طريقة عرض الرسم'],
    detailedView:['Names & positions','الأسماء والمواقف'],
    compactView:['Marker overview','عرض مختصر للعلامات'],
    detailedHint:['Every card sits in its reconstruction and arms or financing category. Read the statement summaries directly, then open the dated sources for the evidence.','تقع كل بطاقة في فئتها على محوري الإعمار والسلاح أو التمويل. اقرأ ملخصات المواقف مباشرة، ثم افتح المصادر المؤرخة للاطلاع على الأدلة.'],
    statementSummary:['Statement summary','ملخص التصريح'],
    reconstructionShort:['Reconstruction position','الموقف من الإعمار'],
    noCategoryEntries:['No documented placements','لا توجد مواضع موثّقة'],
    mapSource:['Source','المصدر'],
    allEvidence:['All supporting statements','جميع التصريحات الداعمة'],
    viewpointPending:['Position not yet classified in this dataset.','لم يُصنّف هذا الموقف في قاعدة البيانات بعد.'],
    mapMissing:['Names without a coded reconstruction position remain in the directory below.','تبقى الأسماء التي لم يُصنّف موقفها من الإعمار في الدليل أدناه.'],
    directoryPositionNote:['Each axis is named below. Select an entry to read its evidence.','يظهر الموقف من كل محور أدناه. اختر اسماً لقراءة أدلته.'],
    labelledDotsHint:['Read the position at the photo or emblem; the name and both summaries sit beside it. Select a point for the speaker, full statements and dated sources.','اقرأ موضع الصورة أو الشعار؛ يظهر الاسم وملخصا الموقف بجانبه. اختر نقطة لعرض المتحدث والتصريحات الكاملة والمصادر المؤرخة.'],
    panGraph:['Scroll sideways to read the full graph.','مرّر أفقياً لقراءة الرسم كاملاً.'],
    citedSpeakers:['Cited speakers','المتحدثون المستشهد بهم'],
    statementContext:['Statement context','سياق التصريح'],
    sourcesOnGraph:['Dated sources','المصادر المؤرخة'],
    focusColumn:['Reconstruction column','عمود الإعمار'],
    allColumns:['All represented categories','جميع الفئات الممثلة'],
    visiblePoints:['points shown','نقطة معروضة'],
    graphScope:['Empty categories are omitted from the graph and remain in the category guide. Scroll sideways to compare columns, or focus on one above.','تُحذف الفئات الفارغة من الرسم وتبقى في دليل الفئات. مرّر أفقياً للمقارنة أو اختر عموداً أعلاه.']
  };
  const t = key => {
    const match=key.match(/^(reconstruction|arms|financing)(\d+)(Detail|Examples)?$/);
    if(match&&data?.categories){
      const category=data.categories[match[1]].find(c=>c.id===Number(match[2]));
      if(category)return local(category[match[3]==='Detail'?'description':match[3]==='Examples'?'examples':'label']);
    }
    return W[key]?.[lang === 'ar' ? 1 : 0] || key;
  };
  const local = value => typeof value === 'string' ? value : value?.[lang] || value?.en || '';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeURL = value => { try { const u = new URL(value); return u.protocol === 'https:' ? u.href : '#'; } catch { return '#'; } };
  const date = value => new Intl.DateTimeFormat(lang === 'ar' ? 'ar-LB' : 'en-GB', {day:'numeric',month:'short',year:'numeric'}).format(new Date(value+'T12:00:00Z'));
  const axisLabel = (axis, p) => p ? t(axis+M.categoryValue(p)) : t('unknown');
  const categoryValues = axis => M.categoryValues(axis,data.categories);
  const shortCategory = (axis,value) => local(data.categories[axis].find(c=>c.id===value)?.shortLabel)||t(axis+value);
  const allLayer = () => data.entities.filter(e => e.layer === layer);
  const percentage = (count,total) => new Intl.NumberFormat(lang==='ar'?'ar-LB':'en-GB',{style:'percent',maximumFractionDigits:1}).format(total?count/total:0);
  const period = info => info.latest ? (info.earliest===info.latest?date(info.latest):`${date(info.earliest)} — ${date(info.latest)}`) : '—';
  const entityButton = e => `<button type="button" class="key-button" data-select="${e.id}" aria-pressed="${e.id===selected}">${symbolIcon(e)||portraitIcon(e)}${esc(local(e.name))}</button>`;
  const numbers = () => new Map(allLayer().map((e,i) => [e.id, i+1]));
  const symbolPath = e => e.layer==='parties' && /^symbols\/[a-z0-9-]+\.(png|jpg|svg)$/.test(e.symbol?.path||'') ? e.symbol.path : null;
  const portraitPath = e => e.layer!=='parties' && /^portraits\/[a-z0-9-]+\.(png|jpg|webp)$/.test(e.portrait?.path||'') ? e.portrait.path : null;
  const symbolIcon = e => symbolPath(e) ? `<img class="party-symbol" src="${esc(symbolPath(e))}" alt="" aria-hidden="true">` : '';
  const portraitIcon = e => portraitPath(e) ? `<img class="person-portrait" src="${esc(portraitPath(e))}" alt="" aria-hidden="true" loading="lazy">` : '';
  const licenseLabel = s => lang==='ar' ? ({'Public domain':'ملكية عامة','Fair use':'استخدام تعريفي كما ورد في المصدر','Party emblem — editorial identification':'شعار الحزب — للتعريف به','Official biography photo — editorial identification':'صورة السيرة الرسمية — للتعريف بالشخص','Published biography photo — editorial identification':'صورة السيرة المنشورة — للتعريف بالشخص'}[s.license]||s.license) : s.license;
  function symbolCredits(){
    const entries=data.entities.filter(e=>symbolPath(e));
    return `<details class="symbol-credits"><summary>${t('symbolCredits')}</summary><ul>${entries.map(e=>`<li><a href="${safeURL(e.symbol.sourceUrl)}" target="_blank" rel="noopener noreferrer">${esc(local(e.name))}</a> — ${esc(e.symbol.author)}${e.symbol.author?' · ':''}${e.symbol.licenseUrl?`<a href="${safeURL(e.symbol.licenseUrl.replace(/^http:/,'https:'))}" target="_blank" rel="noopener noreferrer">${esc(licenseLabel(e.symbol))}</a>`:esc(licenseLabel(e.symbol))}</li>`).join('')}</ul></details>`;
  }

  function chartCard(metric) {
    const stats=M.statistics(allLayer(),metric,data.sources,data.categories);
    return `<section class="chart-card" data-metric="${metric}" aria-labelledby="${metric}-title">
      <div class="chart-heading"><div><h2 id="${metric}-title">${t(metric==='arms'?'armsTitle':'financeTitle')}</h2><p>${t(metric==='arms'?'armsIntro':'financeIntro')}</p></div><span class="chart-index">${metric==='arms'?'A':'B'}</span></div>
      <div class="chart-coverage">${[['bothAxes',stats.complete],['partial',stats.partial],['noReconstruction',stats.outside]].map(([label,count])=>`<div><strong>${count}<small>${percentage(count,stats.total)}</small></strong><span>${t(label)}</span></div>`).join('')}</div>
      ${categoryGuide(metric)}
      <div class="graph-focus"><label>${t('focusColumn')}<select data-column-focus="${metric}"><option value="all">${t('allColumns')}</option>${categoryValues('reconstruction').map(value=>{const count=allLayer().filter(e=>M.categoryValue(e.positions.reconstruction)===value).length;return count?`<option value="${value}" ${columnFocus[metric]===String(value)?'selected':''}>${t('reconstruction'+value)} · ${count}</option>`:'';}).join('')}</select></label><span id="visible-${metric}"></span></div>
      <p class="chart-instructions">${t('labelledDotsHint')}</p>
      <div class="plot-viewport" tabindex="0" role="region" aria-label="${esc(t(metric==='arms'?'armsTitle':'financeTitle'))}"><svg class="plot" id="plot-${metric}" role="group" aria-label="${esc(t(metric==='arms'?'armsTitle':'financeTitle'))}"></svg></div>
      <div class="cell-explorer" id="cell-${metric}" hidden></div>
      <div class="selection-peek" id="peek-${metric}" hidden></div>
      <div class="plot-note" id="counts-${metric}"></div>
      <p class="chart-footnote">${t('percentageNote')}</p>
      ${distributionCard(metric,stats)}</section>`;
  }
  function categoryGuide(metric){
    return `<details class="category-guide"><summary>${t('categoryGuide')} · ${categoryValues('reconstruction').length} ${t('reconstruction')} / ${categoryValues(metric).length} ${t(metric)}</summary><p class="category-guide-note">${esc(local(data.categoryMethod))}</p>${['reconstruction',metric].map(axis=>`<div class="category-axis" data-guide-axis="${axis}"><h4>${t(axis+'Guide')}</h4><div class="category-definitions">${categoryValues(axis).map(value=>`<div class="category-definition" data-category="${axis}${value}"><strong>${t(axis+value)}</strong><p>${t(axis+value+'Detail')}</p><p class="category-examples"><b>${t('categoryExamples')}:</b> ${t(axis+value+'Examples')}</p></div>`).join('')}</div></div>`).join('')}</details>`;
  }
  function distributionCard(metric,stats){
    return `<details class="graph-breakdown"><summary>${t('distributions')}</summary><div class="breakdown-body"><h3>${t(metric)}</h3><p class="source-note">${t('distributionNote')}</p>
      <div class="distribution">${stats.distribution.map(row=>`<div class="distribution-row"><span>${row.value?t(metric+row.value):t('unknown')}</span><div class="distribution-track" aria-hidden="true"><i style="width:${stats.total?row.count/stats.total*100:0}%" class="${row.value?'':'uncoded'}"></i></div><b>${row.count} <small>${percentage(row.count,stats.total)}</small></b></div>`).join('')}</div>
      <p class="source-note"><b>${stats.sources}</b> ${t('graphSources')} · ${t('evidencePeriod')}: ${period(stats)}</p>
      <h3>${t('chartTable')}</h3><div class="figures-scroll" tabindex="0" role="region" aria-label="${esc(t('chartTable'))}"><table class="graph-figures"><thead><tr><th>${t('reconstruction')}</th><th>${t(metric)}</th><th>${t('count')}</th><th>${t('share')}</th><th>${t('names')}</th></tr></thead><tbody>${stats.cells.map(cell=>`<tr><td>${t('reconstruction'+cell.x)}</td><td>${cell.y?t(metric+cell.y):t('unknown')}</td><td>${cell.entities.length}</td><td>${percentage(cell.entities.length,stats.total)}</td><td>${cell.entities.length?cell.entities.map(e=>`<button type="button" class="table-name" data-select="${e.id}">${esc(local(e.name))}</button>`).join(' · '):'—'}</td></tr>`).join('')}</tbody></table></div>
      <button type="button" class="plain-button" data-download-figures="${metric}">${t('downloadFigures')}</button></div></details>`;
  }
  function layerOverview(){
    const entities=allLayer(),refs=[...new Set(entities.flatMap(e=>M.evidence(e,data.sources).refs))];
    const stats=[['rosterTotal',entities.length],['reconstructionCoded',entities.filter(e=>e.positions.reconstruction).length],['completeBoth',entities.filter(e=>M.placement(e,'arms')&&M.placement(e,'financing')).length],['supportingStatements',refs.length]];
    return `<section class="layer-overview" aria-label="${esc(t('layerOverview'))}">${stats.map(([label,count])=>`<div><strong>${count}</strong><span>${t(label)}</span></div>`).join('')}</section>`;
  }
  function downloadFigures(metric){
    const rows=[[t('names'),t('reconstruction'),t(metric),t('graphSources'),t('earliestCited'),t('latestCited'),lang==='ar'?'روابط المصادر':'Source URLs'],
      ...allLayer().map(e=>{const info=M.evidence(e,data.sources,['reconstruction',metric]);return [local(e.name),axisLabel('reconstruction',e.positions.reconstruction),axisLabel(metric,e.positions[metric]),info.refs.length,info.earliest||'',info.latest||'',info.statements.map(s=>s.url).join(' | ')];})];
    const csv='\ufeff'+rows.map(row=>row.map(value=>{let text=String(value);if(/^\s*[=+@-]/.test(text))text="'"+text;return '"'+text.replace(/"/g,'""')+'"';}).join(',')).join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=`lebanon-${layer}-${metric}-${lang}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function render() {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.title = t('title');
    if (!data) { root.innerHTML = `<p class="loading">${t('loading')}</p>`; return; }
    root.innerHTML = `<main class="graph-page">
      <header class="intro"><div><p class="kicker">${t('kicker')}</p><h1>${t('title')}</h1><p>${t('intro')}</p></div><div class="roster-date">${t('statementDate')}<br><b>${date(data.statementsReviewed||data.reviewed)}</b></div></header>
      <nav class="layers" aria-label="${lang==='ar'?'طبقات المقارنة':'Comparison layers'}">${['parties','deputies','ministers'].map((id,i)=>`<button type="button" class="layer" data-layer="${id}" aria-pressed="${layer===id}"><span class="layer-number">0${i+1}</span><span class="layer-label">${t(id)}<span class="layer-sub">${t(id+'Sub')}</span></span><span class="layer-count">${data.entities.filter(e=>e.layer===id).length}</span></button>`).join('')}</nav>
      ${layerOverview()}
      <div class="chart-pair">${chartCard('arms')}${chartCard('financing')}</div>
      <p class="legend-title">${t('keyTitle')}</p><div id="point-key" class="point-key"></div>
      <p class="category-note">${t(layer==='parties'?'partyCategoryNote':'portraitNote')} ${t('railNote')}</p><p class="coverage-note">${t('coverageNote')}</p>
      <p id="selection-status" class="sr-only" role="status" aria-live="polite"></p><section class="inspector" id="inspector" aria-label="${esc(t('evidenceHeading'))}"></section>
      <section aria-labelledby="directory-title"><div class="directory-heading"><h2 id="directory-title">${t('directory')} · ${t(layer)}</h2><p>${t('directoryPositionNote')}</p></div>
      <div class="filters"><label>${t('search')}<input id="name-search" type="search" autocomplete="off" placeholder="${esc(t('placeholder'))}" value="${esc(query)}"></label><label>${t('show')}<select id="coverage"><option value="all">${t('all')}</option><option value="arms">${t('armsFilter')}</option><option value="financing">${t('financeFilter')}</option><option value="missing">${t('missingFilter')}</option><option value="missing-arms">${t('missingArmsFilter')}</option><option value="missing-financing">${t('missingFinanceFilter')}</option></select></label></div>
      <p class="source-note" id="directory-count" role="status" aria-live="polite"></p><div id="directory-list" class="directory-list"></div><div id="pagination" class="pagination"></div></section>
      <details class="method"><summary>${t('method')}</summary><div class="method-body"><p>${t('methodX')}</p><p>${t('methodArms')}</p><p>${t('methodFinance')}</p><p>${t('methodParty')}</p><p>${t('methodMissing')}</p><p>${t('methodCoverage')}</p><p>${t('rosterDate')}: ${date(data.rosterReviewed||data.reviewed)}.</p><p>${t('datedNote')}</p><div class="method-links"><a href="${safeURL(data.rosterSources.deputies)}" target="_blank" rel="noopener noreferrer">${t('parliament')}</a><a href="${safeURL(data.rosterSources.ministers)}" target="_blank" rel="noopener noreferrer">${t('cabinet')}</a><a href="${safeURL(data.rosterSources.parties)}" target="_blank" rel="noopener noreferrer">${t('partySource')}</a><a href="archive.html?lang=${lang}">${t('archive')}</a><button type="button" class="plain-button" id="download">${t('download')}</button></div></div></details>
      </main><div id="marker-tooltip" class="marker-tooltip" role="tooltip" hidden></div>`;
    root.querySelector('.method-body').insertAdjacentHTML('beforeend',symbolCredits());
    root.querySelector('#coverage').value = coverage;
    root.querySelectorAll('[data-layer]').forEach(button => button.addEventListener('click', () => {
      layer = button.dataset.layer; selected = null; query = ''; coverage = 'all'; page = 0; activeCells.arms=null;activeCells.financing=null;columnFocus.arms='all';columnFocus.financing='all';render();
      root.querySelector(`[data-layer="${layer}"]`).focus({preventScroll:true});
    }));
    root.querySelector('#name-search').addEventListener('input', event => {query=event.target.value;page=0;renderDirectory();});
    root.querySelector('#coverage').addEventListener('change', event => {coverage=event.target.value;page=0;renderDirectory();});
    root.querySelector('#download').addEventListener('click', () => {
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
      const a=document.createElement('a');a.href=url;a.download='lebanon-political-positions.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    root.querySelectorAll('[data-download-figures]').forEach(button=>button.addEventListener('click',()=>downloadFigures(button.dataset.downloadFigures)));
    root.querySelectorAll('[data-column-focus]').forEach(control=>control.addEventListener('change',()=>{
      const metric=control.dataset.columnFocus;columnFocus[metric]=control.value;activeCells[metric]=null;
      drawChart(metric);renderCell(metric);root.querySelector(`#plot-${metric}`).parentElement.scrollLeft=0;
    }));
    root.querySelectorAll('.graph-figures [data-select]').forEach(button=>button.addEventListener('click',()=>{select(button.dataset.select);root.querySelector('#inspector').scrollIntoView({behavior:'smooth',block:'start'});}));
    renderCharts();renderKey();renderInspector();renderDirectory();
    resizeObserver.disconnect();
    root.querySelectorAll('.plot').forEach(svg=>resizeObserver.observe(svg));
  }

  function svgNode(tag, attrs={}, text) {
    const node=document.createElementNS('http://www.w3.org/2000/svg',tag);
    for(const [k,v] of Object.entries(attrs)) node.setAttribute(k,String(v));
    if(text!==undefined) node.textContent=text;
    return node;
  }
  function wrappedText(svg, text, x, y, maxChars, attrs={}) {
    const words=text.split(' '), lines=[];let line='';
    for(const word of words){if(line && (line+' '+word).length>maxChars){lines.push(line);line=word;}else line+=(line?' ':'')+word;}
    if(line)lines.push(line);
    const node=svgNode('text',{x,y,'font-size':11,'text-anchor':'middle',...attrs});
    lines.forEach((line,i)=>node.append(svgNode('tspan',{x,dy:i===0?0:14},line)));
    svg.append(node);return node;
  }
  function drawChart(metric) {
    const svg=root.querySelector('#plot-'+metric);if(!svg)return;
    const entities=allLayer(),shown=columnFocus[metric]==='all'?entities:entities.filter(e=>M.categoryValue(e.positions.reconstruction)===Number(columnFocus[metric]));
    const xValues=categoryValues('reconstruction').filter(x=>shown.some(e=>M.categoryValue(e.positions.reconstruction)===x));
    if(!xValues.length)xValues.push(Number(columnFocus[metric])||categoryValues('reconstruction')[0]);
    const yValues=categoryValues(metric).filter(y=>shown.some(e=>e.positions.reconstruction&&M.categoryValue(e.positions[metric])===y));
    const xIndex=new Map(xValues.map((x,index)=>[x,index]));
    const minWidth=xValues.length===1?320:900;
    svg.style.minWidth=minWidth+'px';
    const width=Math.max(minWidth,svg.parentElement.clientWidth||svg.clientWidth||1100);
    const left=width<600?84:124,right=12,bottom=20;
    const pw=width-left-right,cw=pw/xValues.length;
    const ids=numbers(),cells=M.cells(shown,metric);
    const partyMarkers=layer==='parties',textWidth=xValues.length===1?Math.min(280,pw-70):Math.min(236,Math.max(190,pw/4.5));
    const wrap=(text,maxChars)=>{
      const result=[];let line='';
      for(const word of text.split(/\s+/)){
        if(line&&(line+' '+word).length>maxChars){result.push(line);line=word;}else line+=(line?' ':'')+word;
      }
      if(line)result.push(line);return result;
    };
    const lines=(text,fontSize)=>wrap(text,Math.floor(textWidth/(fontSize*.61)));
    const top=43+Math.max(...xValues.map(x=>wrap(shortCategory('reconstruction',x),Math.max(8,Math.floor((cw-8)/6.5))).length))*14;
    const pointX=x=>xValues.length===1?(lang==='ar'?width-right-24:left+24):left+(xIndex.get(x)+.5)*cw;
    const labels=new Map(shown.filter(e=>e.positions.reconstruction).map(e=>{
      const known=e.positions[metric],blocks=[];
      const add=(kind,text,size,weight,lineHeight,gap)=>blocks.push({kind,rows:lines(text,size),size,weight,lineHeight,gap});
      add('name',local(e.name),13,750,16,4);
      add('reconstruction',local(e.positions.reconstruction.reason),11.5,400,14.5,4);
      add('summary',known?local(known.reason):t('viewpointPending'),11.5,400,14.5,0);
      return [e.id,{blocks,height:Math.max(44,blocks.reduce((sum,b)=>sum+b.rows.length*b.lineHeight+b.gap,0)+10)}];
    }));
    const partial=M.reconstructionOnly(shown,metric),partialCells=new Map();
    for(const e of partial){const x=M.categoryValue(e.positions.reconstruction);if(!partialCells.has(x))partialCells.set(x,[]);partialCells.get(x).push(e);}
    const cellHeader=27;
    const pack=entries=>M.packLabels(entries.map(e=>({id:e.id,x:pointX(M.categoryValue(e.positions.reconstruction)),width:textWidth,height:labels.get(e.id).height})),{left:left+2,right:width-4,preferredSide:lang==='ar'?'left':'right',gap:10});
    const layouts=new Map(yValues.map(y=>[y,pack(shown.filter(e=>e.positions.reconstruction&&M.categoryValue(e.positions[metric])===y))]));
    if(partial.length)layouts.set('unknown',pack(partial));
    const rowHeights=Object.fromEntries(yValues.map(y=>[y,Math.max(45+wrap(shortCategory(metric,y),Math.floor((left-14)/6.5)).length*14,layouts.get(y).height+cellHeader+15)]));
    const rowTops={};let ph=0;
    for(const y of yValues){rowTops[y]=top+ph;ph+=rowHeights[y];}
    const railTop=top+ph+15,railHeight=partial.length?layouts.get('unknown').height+cellHeader+15:0;
    const axisTop=partial.length?railTop+railHeight:top+ph,height=axisTop+bottom;
    svg.style.height=height+'px';
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.replaceChildren();
    const dir=lang==='ar'?'rtl':'ltr';
    for(const y of yValues){
      svg.append(svgNode('rect',{x:left,y:rowTops[y],width:pw,height:rowHeights[y],fill:yValues.indexOf(y)%2?'#fafaf8':'#fff',stroke:'#dededb','stroke-width':.8}));
      const title=wrappedText(svg,shortCategory(metric,y),left/2,rowTops[y]+24,Math.floor((left-14)/6.5),{class:'axis-category-title','data-axis':metric,'data-category':y,'font-size':11,'font-weight':700,direction:dir});
      title.append(svgNode('title',{},t(metric+y)));
    }
    if(partial.length){
      svg.append(svgNode('rect',{x:left,y:railTop,width:pw,height:railHeight,fill:'#fcfcfc',stroke:'#777','stroke-dasharray':'4 4'}));
      wrappedText(svg,t(metric==='arms'?'unknownArms':'unknownFinancing'),left/2,railTop+24,Math.floor((left-14)/6.5),{'font-size':11,'font-weight':700,direction:dir});
      for(const x of xValues)if(partialCells.has(x))cells.set(`${x}:unknown`,partialCells.get(x));
    }
    for(const value of xValues){
      const centre=left+(xIndex.get(value)+.5)*cw;
      const title=wrappedText(svg,shortCategory('reconstruction',value),centre,34,Math.max(8,Math.floor((cw-8)/6.5)),{class:'axis-category-title','data-axis':'reconstruction','data-category':value,'font-size':11,'font-weight':700,direction:dir});
      title.append(svgNode('title',{},t('reconstruction'+value)));
      if(xValues.length>1)svg.append(svgNode('line',{x1:centre,y1:top,x2:centre,y2:axisTop,stroke:'#ddd','stroke-width':.7,'stroke-dasharray':'2 5'}));
    }
    wrappedText(svg,t('reconstruction'),left+pw/2,13,80,{'font-size':11,'font-weight':700,direction:dir});
    svg.append(svgNode('path',{d:`M ${left} ${top} V ${axisTop} H ${width-right}`,fill:'none',stroke:'#000','stroke-width':1}));
    svg.dataset.rowHeights=JSON.stringify(rowHeights);svg.dataset.rowTops=JSON.stringify(rowTops);svg.dataset.railTop=railTop;svg.dataset.railHeight=railHeight;
    svg.dataset.xValues=JSON.stringify(xValues);svg.dataset.yValues=JSON.stringify(yValues);svg.dataset.gridTop=top;svg.dataset.plotLeft=left;
    for(const [key,entries] of cells){
      const [xText,yText]=key.split(':'),x=Number(xText),y=yText==='unknown'?'unknown':Number(yText),cellTop=y==='unknown'?railTop:rowTops[y];
      const title=`${t('reconstruction'+x)} · ${y==='unknown'?t('unknown'):t(metric+y)} · ${entries.length} · ${percentage(entries.length,entities.length)}`;
      const count=svgNode('g',{class:'cell-count',role:'button',tabindex:0,'data-cell':key,'aria-label':title,'aria-pressed':activeCells[metric]===key});
      count.append(svgNode('title',{},title));
      count.append(svgNode('rect',{x:left+xIndex.get(x)*cw+3,y:cellTop+2,width:cw-6,height:20,rx:3,fill:activeCells[metric]===key?'#e6e6df':'#f0f0ec'}));
      count.append(svgNode('text',{x:left+(xIndex.get(x)+.5)*cw,y:cellTop+16,'text-anchor':'middle','font-size':10,fill:'#000'},`${entries.length} · ${percentage(entries.length,entities.length)}`));
      const open=()=>{activeCells[metric]=activeCells[metric]===key?null:key;drawChart(metric);renderCell(metric);root.querySelector(`#plot-${metric} [data-cell="${key}"]`)?.focus({preventScroll:true});};
      count.addEventListener('click',open);count.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open();}});
      svg.append(count);
    }
    let plotted=0;
    for(const [y,layout] of layouts){
      const unknown=y==='unknown',cellTop=unknown?railTop:rowTops[y];
      for(const placed of layout.points){
        const e=shown.find(e=>e.id===placed.id),label=labels.get(e.id);
        const px=placed.x,cursor=cellTop+cellHeader+7+placed.top,py=cursor+22;
        const title=`${local(e.name)} · ${t('reconstruction')}: ${axisLabel('reconstruction',e.positions.reconstruction)} · ${t(metric)}: ${axisLabel(metric,e.positions[metric])}`;
        const group=svgNode('g',{class:'point'+(unknown?' partial-point':''),role:'button',tabindex:0,'data-entity':e.id,'data-label-height':label.height,'data-label-top':cursor,'data-label-width':textWidth,'data-box-left':placed.left,'data-box-right':placed.right,'data-text-left':placed.textLeft,'aria-label':title,'aria-describedby':'marker-tooltip','aria-pressed':e.id===selected,transform:`translate(${px},${py})`});
        group.append(svgNode('title',{},title));
        const symbol=symbolPath(e);
        if(symbol){
          group.classList.add('flag-point');
          group.append(svgNode('rect',{class:'marker-frame',x:-20,y:-16,width:40,height:32,rx:3,fill:'#fff',stroke:'#000','stroke-width':e.id===selected?3:1}));
          group.append(svgNode('image',{class:'marker-image',href:symbol,x:-18,y:-14,width:36,height:28,preserveAspectRatio:'xMidYMid meet','pointer-events':'none','aria-hidden':true}));
        }else if(portraitPath(e)){
          const clipId=`portrait-${metric}-${e.id}`;
          const clip=svgNode('clipPath',{id:clipId});clip.append(svgNode('circle',{r:19}));group.append(clip);
          group.append(svgNode('circle',{class:'marker-frame',r:21,fill:'#fff',stroke:'#000','stroke-width':e.id===selected?3:1}));
          group.append(svgNode('image',{class:'marker-image',href:portraitPath(e),x:-19,y:-19,width:38,height:38,preserveAspectRatio:'xMidYMid slice','clip-path':`url(#${clipId})`,'pointer-events':'none','aria-hidden':true}));
        }else if(partyMarkers && e.symbol?.status==='unverified'){
          group.classList.add('text-party-point');
          group.append(svgNode('rect',{class:'marker-frame',x:-20,y:-16,width:40,height:32,rx:3,fill:'#fff',stroke:'#000','stroke-width':e.id===selected?3:1}));
          wrappedText(group,local(e.symbol.label),0,-3,9,{'font-size':8,'font-weight':700,direction:dir,class:'marker-label'});
        }else{
          group.append(svgNode('circle',{r:12,fill:e.id===selected?'#fff':metric==='arms'?'#f3dbcb':'#dce8ed',stroke:'#000','stroke-width':e.id===selected?3:1.3}));
          group.append(svgNode('text',{'text-anchor':'middle','dominant-baseline':'central','font-size':ids.get(e.id)>99?9:11,'font-weight':700,direction:'ltr'},ids.get(e.id)));
        }
        const textX=(placed.side==='left'?placed.textLeft+textWidth:placed.textLeft)-px;
        const anchor=(placed.side==='left')===(lang==='ar')?'start':'end';let textY=-6;
        group.append(svgNode('line',{class:'label-connector',x1:placed.side==='right'?22:-22,x2:placed.side==='right'?27:-27,y1:0,y2:0,stroke:'#000','stroke-width':.7}));
        for(const {kind,rows,size,weight,lineHeight,gap,source} of label.blocks){
          const node=svgNode('text',{class:'point-'+kind,x:textX,y:textY,'font-size':size,'font-weight':weight,'text-anchor':anchor,direction:dir,fill:'#000'});
          rows.forEach((line,i)=>node.append(svgNode('tspan',{x:textX,dy:i===0?0:lineHeight},line)));
          if(source){
            const link=svgNode('a',{class:'point-source',href:safeURL(source.url),target:'_blank',rel:'noopener noreferrer',tabindex:0,'data-source':source.id,'aria-label':`${local(source.speaker)} · ${date(source.date)} · ${local(source.publisher)}`});
            link.append(node);
            link.addEventListener('click',event=>event.stopPropagation());
            link.addEventListener('keydown',event=>event.stopPropagation());
            group.append(link);
          }else group.append(node);
          textY+=rows.length*lineHeight+gap;
        }
        group.addEventListener('click',()=>select(e.id));
        group.addEventListener('pointerenter',event=>showTooltip(e,metric,event));
        group.addEventListener('pointermove',event=>positionTooltip(event));
        group.addEventListener('pointerleave',hideTooltip);
        group.addEventListener('focus',event=>showTooltip(e,metric,event));
        group.addEventListener('blur',hideTooltip);
        group.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select(e.id);}});
        svg.append(group);plotted++;
      }
    }
    if(!plotted)wrappedText(svg,t('noPoints'),left+pw/2,top+ph/2,Math.max(14,Math.floor(pw/7)),{direction:dir,'font-weight':650});
    const countPanel=root.querySelector('#counts-'+metric);
    root.querySelector('#visible-'+metric).textContent=`${plotted} / ${entities.filter(e=>e.positions.reconstruction).length} ${t('visiblePoints')}`;
    const stats=M.statistics(entities,metric,data.sources,data.categories);
    countPanel.innerHTML=`<span><b>${stats.sources}</b> ${t('graphSources')}</span><span>${t('evidencePeriod')}: <b>${period(stats)}</b></span><button type="button" class="unplaced-button"><b>${stats.total-stats.complete}</b> ${t('missingFilter')} ↗</button>`;
    countPanel.querySelector('button').addEventListener('click',()=>{
      query='';coverage='missing-'+metric;page=0;
      root.querySelector('#name-search').value='';root.querySelector('#coverage').value=coverage;renderDirectory();
      root.querySelector('#directory-title').scrollIntoView({behavior:'smooth',block:'start'});
    });
  }
  function renderCell(metric){
    const panel=root.querySelector('#cell-'+metric),key=activeCells[metric];
    panel.hidden=!key;if(!key){panel.replaceChildren();return;}
    const [x,y]=key.split(':'),entries=allLayer().filter(e=>M.categoryValue(e.positions.reconstruction)===Number(x)&&(y==='unknown'?!e.positions[metric]:M.categoryValue(e.positions[metric])===Number(y)));
    panel.innerHTML=`<div class="cell-explorer-heading"><div><strong>${t('namesInCell')} · ${entries.length}</strong><p>${t('reconstruction'+x)} · ${y==='unknown'?t('unknown'):t(metric+y)}</p></div><button type="button" class="plain-button" data-close-cell>${t('close')}</button></div><div class="point-key">${entries.map(entityButton).join('')||`<p>${t('noNamesInCell')}</p>`}</div>`;
    panel.querySelector('[data-close-cell]').addEventListener('click',()=>{activeCells[metric]=null;renderCell(metric);drawChart(metric);root.querySelector(`#plot-${metric} [data-cell="${key}"]`)?.focus({preventScroll:true});});
    panel.querySelectorAll('[data-select]').forEach(button=>button.addEventListener('click',()=>select(button.dataset.select)));
  }
  function renderPeek(metric){
    const panel=root.querySelector('#peek-'+metric),e=allLayer().find(e=>e.id===selected);
    panel.hidden=!e;if(!e)return;
    const info=M.evidence(e,data.sources,['reconstruction',metric]);
    panel.innerHTML=`<div class="peek-heading">${symbolIcon(e)||portraitIcon(e)}<div><small>${t('selectedName')}</small><strong>${esc(local(e.name))}</strong></div><button type="button" class="plain-button" data-view-evidence>${t('viewEvidence')}</button></div><div class="peek-positions">${['reconstruction',metric].map(axis=>`<p><strong>${t(axis)} · ${axisLabel(axis,e.positions[axis])}</strong><span>${e.positions[axis]?esc(local(e.positions[axis].reason)):t('unknownDetail')}</span></p>`).join('')}</div><p class="source-note">${info.refs.length} ${t('statements')} · ${period(info)}</p>`;
    panel.querySelector('[data-view-evidence]').addEventListener('click',()=>{root.querySelector('#inspector').scrollIntoView({behavior:'smooth',block:'start'});root.querySelector('.inspector-heading h2')?.focus({preventScroll:true});});
  }
  function hideTooltip(){const tip=root.querySelector('#marker-tooltip');if(tip)tip.hidden=true;}
  function positionTooltip(event){
    const tip=root.querySelector('#marker-tooltip');if(!tip||tip.hidden)return;
    const rect=event.currentTarget?.getBoundingClientRect();
    const x=Number.isFinite(event.clientX)?event.clientX:rect?.left||8,y=Number.isFinite(event.clientY)?event.clientY:rect?.top||8;
    tip.style.left=Math.max(8,Math.min(x+16,window.innerWidth-(tip.offsetWidth||330)-8))+'px';
    tip.style.top=Math.max(8,Math.min(y+16,window.innerHeight-(tip.offsetHeight||360)-8))+'px';
  }
  function showTooltip(e,metric,event){
    const tip=root.querySelector('#marker-tooltip'),info=M.evidence(e,data.sources,['reconstruction',metric]);
    tip.innerHTML=`<div class="tooltip-name">${symbolIcon(e)||portraitIcon(e)}<strong>${esc(local(e.name))}</strong></div><p class="tooltip-role">${esc(local(e.role))}</p>${['reconstruction',metric].map(axis=>{const p=e.positions[axis],evidence=M.evidence(e,data.sources,[axis]);return `<div class="tooltip-axis"><small>${t(axis)}</small><b>${axisLabel(axis,p)}</b><p>${p?esc(local(p.reason)):t('unknownDetail')}</p>${p?`<small>${p.sources.length} ${t('statements')} · ${period(evidence)}</small>`:''}</div>`;}).join('')}<p class="tooltip-footer">${info.refs.length} ${t('graphSources')}</p>`;
    tip.hidden=false;positionTooltip(event);
  }
  function renderCharts(){hideTooltip();for(const metric of ['arms','financing']){drawChart(metric);renderCell(metric);renderPeek(metric);}}
  const resizeObserver=new ResizeObserver(()=>requestAnimationFrame(renderCharts));
  function select(id){
    hideTooltip();
    const focused=document.activeElement;
    const metric=focused?.closest('svg')?.id;
    const focusId=focused?.getAttribute('data-entity')||focused?.getAttribute('data-select');
    const wasKey=focused?.classList.contains('key-button');
    selected=id;renderCharts();renderKey();renderInspector();renderDirectory();
    root.querySelector('#selection-status').textContent=local(data.entities.find(e=>e.id===id)?.name);
    if(focusId){
      const target=metric?root.querySelector(`#${metric} [data-entity="${focusId}"]`):
        root.querySelector(`${wasKey?'#point-key':'#directory-list'} [data-select="${focusId}"]`);
      target?.focus({preventScroll:true});
    }
  }
  function renderKey(){
    const ids=numbers(),placed=allLayer().filter(e=>e.positions.reconstruction);
    const key=root.querySelector('#point-key');
    key.innerHTML=placed.map(e=>`<button type="button" class="key-button" data-select="${e.id}" aria-pressed="${e.id===selected}">${symbolIcon(e)||portraitIcon(e)||`<span class="number">${ids.get(e.id)}</span>`}${esc(local(e.name))}</button>`).join('');
    key.querySelectorAll('[data-select]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.select)));
  }
  function renderInspector(){
    const panel=root.querySelector('#inspector'),e=data.entities.find(e=>e.id===selected&&e.layer===layer);
    panel.hidden=!e;
    if(!e){panel.innerHTML=`<div class="blank"><h3>${t('noSelection')}</h3><p>${t('noSelectionText')}</p></div>`;return;}
    const refs=[...new Set(M.axes.flatMap(axis=>e.positions[axis]?.sources||[]))];
    const statements=refs.map(ref=>data.sources[ref]).sort((a,b)=>b.date.localeCompare(a.date));
    panel.innerHTML=`<div class="inspector-heading"><div><h2 tabindex="-1">${esc(local(e.name))}</h2><p>${esc(local(e.role))}</p></div><a href="${safeURL(e.rosterUrl)}" target="_blank" rel="noopener noreferrer">${t('rosterLink')}</a></div><div class="inspector-content">
      ${statements.length?`<div class="evidence-summary"><span><b>${statements.length}</b> ${t('supportingStatements')}</span><span>${t('evidencePeriod')}: <b>${period(M.evidence(e,data.sources))}</b></span></div>`:''}
      ${symbolPath(e)?`<div class="selected-symbol">${symbolIcon(e)}</div>`:''}
      ${e.symbol?.status==='unverified'?`<p class="source-note">${esc(local(e.symbol.note))}</p>`:''}
      ${portraitPath(e)?`<div class="selected-portrait">${portraitIcon(e)}<div><a href="${safeURL(e.portrait.sourceUrl)}" target="_blank" rel="noopener noreferrer">${t('portraitSource')}</a><p class="source-note">${esc(e.portrait.author)} · ${esc(licenseLabel(e.portrait))}</p></div></div>`:''}
      ${e.scope?`<p class="source-note">${esc(local(e.scope))}</p>`:`<p class="source-note">${t('personalRule')}</p>`}
      ${e.affiliationUrl?`<p class="source-note"><a href="${safeURL(e.affiliationUrl)}" target="_blank" rel="noopener noreferrer">${t('affiliationSource')}</a></p>`:''}
      <div class="axis-cards">${M.axes.map(axis=>{const p=e.positions[axis];return `<div class="axis-card ${p?'':'missing'}"><p class="axis-name">${t(axis)}</p><strong>${esc(axisLabel(axis,p))}</strong><p>${p?esc(local(p.reason)):t('unknownDetail')}</p>${p?`<p class="axis-evidence-date">${p.sources.length} ${t('axisSources')}<br>${period(M.evidence(e,data.sources,[axis]))}</p><p>${p.sources.map(ref=>`<a href="#source-${ref}">${esc(ref)}</a>`).join(' · ')}</p>`:''}</div>`;}).join('')}</div>
      ${statements.length?`<p class="evidence-label">${t('evidenceHeading')}</p><p class="source-note">${t('datedNote')}</p><div class="evidence-cards">${statements.map(s=>`<article class="evidence-card" id="source-${s.id}"><div class="meta"><bdi>${s.id}</bdi> · ${date(s.date)} · ${esc(local(s.speaker))}</div><p class="supported-axes">${t('axesSupported')}: ${M.axes.filter(axis=>e.positions[axis]?.sources.includes(s.id)).map(axis=>t(axis)).join(' · ')}</p><p>${esc(local(s.summary))}</p><a href="${safeURL(s.url)}" target="_blank" rel="noopener noreferrer">${esc(local(s.publisher))} ↗</a></article>`).join('')}</div>`:`<p class="empty-evidence">${t('emptyEvidence')}</p>`}
      </div>`;
  }
  function renderDirectory(){
    const matches=M.filter(data.entities,{layer,query,coverage});
    const pages=Math.max(1,Math.ceil(matches.length/pageSize));page=Math.min(page,pages-1);
    root.querySelector('#directory-count').textContent=`${matches.length} ${t('matches')} · ${allLayer().length} ${t(layer)}`;
    const list=root.querySelector('#directory-list');
    list.innerHTML=matches.slice(page*pageSize,(page+1)*pageSize).map(e=>`<button type="button" class="person-card" data-select="${e.id}" aria-pressed="${e.id===selected}">${symbolIcon(e)||portraitIcon(e)}<strong>${esc(local(e.name))}</strong><span class="role">${esc(local(e.role))}</span><span class="directory-positions">${M.axes.map(axis=>`<span><b>${t(axis)}</b>${esc(axisLabel(axis,e.positions[axis]))}</span>`).join('')}</span></button>`).join('')||`<p class="empty-results">${t('noMatches')}</p>`;
    list.querySelectorAll('[data-select]').forEach(b=>b.addEventListener('click',()=>{
      select(b.dataset.select);root.querySelector('#inspector').scrollIntoView({behavior:'smooth',block:'start'});
    }));
    const controls=root.querySelector('#pagination');
    controls.innerHTML=`<button type="button" id="previous" ${page===0?'disabled':''}>${t('previous')}</button><span>${page+1} ${t('of')} ${pages}</span><button type="button" id="next" ${page>=pages-1?'disabled':''}>${t('next')}</button>`;
    controls.querySelector('#previous').addEventListener('click',()=>{page--;renderDirectory();});
    controls.querySelector('#next').addEventListener('click',()=>{page++;renderDirectory();});
  }
  addEventListener('message',event=>{
    if(event.source===window.parent&&event.data?.type==='streamlit:render'){
      const next=event.data.args?.language==='ar'?'ar':'en';
      if(lang!==next){lang=next;render();}
    }
  });
  addEventListener('scroll',hideTooltip,true);
  addEventListener('keydown',event=>{if(event.key==='Escape')hideTooltip();});
  render();
  fetch('./positions.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(payload=>{
    M.validate(payload);data=payload;render();
  }).catch(error=>{root.innerHTML=`<p class="page-error" role="alert">${t('loadError')}</p>`;console.error('Political graphs:',error);});
})();
