/* Shared by the renderer and its offline logic checks. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.PoliticalGraphModel = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const axes = ['reconstruction', 'arms', 'financing'];
  const categoryValue = position => position ? (position.category ?? position.value) : null;
  const categoryValues = (axis, categories) => categories?.[axis]?.map(c=>c.id) || [1,2,3];
  const normalize = value => String(value || '').normalize('NFKD')
    .replace(/[\u0300-\u036f\u064b-\u065f\u0670]/g, '').replace(/[أإآ]/g, 'ا')
    .replace(/ى/g, 'ي').replace(/ة/g, 'ه').replace(/ـ/g, '').toLowerCase();
  function placement(entity, metric) {
    const x = entity.positions.reconstruction, y = entity.positions[metric];
    return x && y ? {x:categoryValue(x), y:categoryValue(y)} : null;
  }
  function filter(entities, {layer, query='', coverage='all'}) {
    const tokens = normalize(query).trim().split(/\s+/).filter(Boolean);
    return entities.filter(e => e.layer === layer &&
      tokens.every(token => normalize([e.name.en,e.name.ar,e.role.en,e.role.ar,...(e.aliases||[])].join(' ')).includes(token)) &&
      (coverage === 'all' || coverage === 'arms' && placement(e,'arms') ||
       coverage === 'financing' && placement(e,'financing') ||
       coverage === 'missing-arms' && !placement(e,'arms') ||
       coverage === 'missing-financing' && !placement(e,'financing') ||
       coverage === 'missing' && (!placement(e,'arms') || !placement(e,'financing'))));
  }
  function cells(entities, metric) {
    const map = new Map();
    for (const entity of entities) {
      const point = placement(entity, metric);
      if (!point) continue;
      const key = `${point.x}:${point.y}`;
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(entity);
    }
    return map;
  }
  function reconstructionOnly(entities, metric) {
    return entities.filter(e => e.positions.reconstruction && !e.positions[metric]);
  }
  function evidence(entity, sources, axisList=axes) {
    const refs=[...new Set(axisList.flatMap(axis=>entity.positions[axis]?.sources||[]))];
    const statements=refs.map(ref=>sources[ref]).filter(Boolean).sort((a,b)=>b.date.localeCompare(a.date));
    return {refs, statements, latest:statements[0]?.date||null, earliest:statements.at(-1)?.date||null};
  }
  // Keep markers on their X category; use free neighbouring space for labels.
  // Each bounding box includes the image, connector and text, so none overlap.
  function packLabels(points, {left, right, preferredSide='right', gap=12}) {
    function pack(reverse) {
      const placed=[];
      const ordered=points.map((p,i)=>({...p,index:i})).sort((a,b)=>(reverse?b.x-a.x:a.x-b.x)||a.index-b.index);
      for(const point of ordered){
        const candidates=[];
        for(const side of [preferredSide,preferredSide==='right'?'left':'right']){
          const textLeft=side==='right'?point.x+29:point.x-29-point.width;
          const boxLeft=Math.min(point.x-22,textLeft),boxRight=Math.max(point.x+22,textLeft+point.width);
          if(boxLeft<left||boxRight>right)continue;
          const height=Math.max(44,point.height);let top=0;
          for(const other of [...placed].sort((a,b)=>a.top-b.top)){
            if(boxLeft<other.right+gap&&boxRight+gap>other.left&&top<other.bottom+gap&&top+height+gap>other.top)top=other.bottom+gap;
          }
          candidates.push({...point,side,textLeft,left:boxLeft,right:boxRight,top,bottom:top+height});
        }
        if(!candidates.length)throw Error('Insufficient label space: '+point.id);
        candidates.sort((a,b)=>a.bottom-b.bottom);
        placed.push(candidates[0]);
      }
      return {points:placed,height:Math.max(0,...placed.map(p=>p.bottom))};
    }
    const forward=pack(preferredSide==='left'),backward=pack(preferredSide!=='left');
    return backward.height<forward.height?backward:forward;
  }
  function statistics(entities, metric, sources, categories) {
    const complete=entities.filter(e=>placement(e,metric));
    const partial=reconstructionOnly(entities,metric);
    const refs=[...new Set(entities.flatMap(e=>evidence(e,sources,['reconstruction',metric]).refs))];
    const dates=refs.map(ref=>sources[ref]?.date).filter(Boolean).sort();
    return {total:entities.length, complete:complete.length, partial:partial.length,
      outside:entities.length-complete.length-partial.length, sources:refs.length,
      earliest:dates[0]||null, latest:dates.at(-1)||null,
      distribution:[...categoryValues(metric,categories),null].map(value=>({value,
        count:entities.filter(e=>categoryValue(e.positions[metric])===value).length})),
      cells:categoryValues('reconstruction',categories).flatMap(x=>[...categoryValues(metric,categories),null].map(y=>({x,y,
        entities:entities.filter(e=>categoryValue(e.positions.reconstruction)===x&&categoryValue(e.positions[metric])===y)})))};
  }
  function validate(data) {
    if (!Array.isArray(data.entities) || !data.sources) throw Error('Missing graph data');
    const ids = new Set();
    for (const e of data.entities) {
      if (ids.has(e.id)) throw Error('Duplicate entity: '+e.id);
      ids.add(e.id);
      for (const axis of axes) {
        const p = e.positions[axis];
        if (p === null) continue;
        if (!p || ![1,2,3].includes(p.value) || !p.sources?.length) throw Error('Unsupported position: '+e.id);
        if(data.categories && !categoryValues(axis,data.categories).includes(p.category)) throw Error('Unreviewed category: '+e.id+' / '+axis);
        for (const ref of p.sources) {
          const s = data.sources[ref];
          if (!s || !e.actorIds.includes(s.actor) || !/^https:\/\//.test(s.url)) throw Error('Unattributed evidence: '+e.id);
        }
      }
    }
    return true;
  }
  return {axes, categoryValue, categoryValues, normalize, placement, filter, cells, reconstructionOnly, evidence, packLabels, statistics, validate};
});
