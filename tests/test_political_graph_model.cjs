/* Run with: node tests/test_political_graph_model.cjs */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const M = require('../imported/parties/graph-model.js');
const sources = {one:{id:'one',date:'2024-11-01'}, two:{id:'two',date:'2026-10-01'}};
const position = (value, refs) => ({value,sources:refs});
const entries = [
  {id:'complete',positions:{reconstruction:position(3,['one']),arms:position(3,['one','two']),financing:null}},
  {id:'partial',positions:{reconstruction:position(2,['one']),arms:null,financing:null}},
  {id:'arms-only',positions:{reconstruction:null,arms:position(2,['two']),financing:null}},
  {id:'unknown',positions:{reconstruction:null,arms:null,financing:null}},
];
const original=JSON.stringify(entries);
const stats=M.statistics(entries,'arms',sources);
assert.deepEqual([stats.total,stats.complete,stats.partial,stats.outside],[4,1,1,2]);
assert.deepEqual(stats.distribution.map(row=>row.count),[0,1,1,2]);
assert.equal(stats.distribution.reduce((n,row)=>n+row.count,0),stats.total);
assert.equal(stats.cells.reduce((n,cell)=>n+cell.entities.length,0),stats.complete+stats.partial);
assert.equal(stats.sources,2,'reuse of a citation does not create more statements');
assert.equal(stats.earliest,'2024-11-01');
assert.equal(stats.latest,'2026-10-01');
assert.deepEqual(M.evidence(entries[0],sources).statements.map(s=>s.id),['two','one']);
assert.equal(M.evidence(entries[0],sources,['reconstruction']).latest,'2024-11-01','dates must be axis-specific');
assert.equal(JSON.stringify(entries),original,'presentation analytics must not alter source positions');
assert.equal(M.statistics([],'arms',sources).latest,null);

const data=JSON.parse(fs.readFileSync('imported/parties/positions.json','utf8'));
for(const layer of ['parties','deputies','ministers'])for(const metric of ['arms','financing']){
  const entities=data.entities.filter(e=>e.layer===layer),summary=M.statistics(entities,metric,data.sources,data.categories);
  assert.equal(summary.complete+summary.partial+summary.outside,entities.length);
  assert.equal(summary.distribution.reduce((n,row)=>n+row.count,0),entities.length);
  assert.equal(new Set(summary.cells.flatMap(cell=>cell.entities.map(e=>e.id))).size,summary.complete+summary.partial);
  assert(summary.latest<=data.statementsReviewed);
}
assert.deepEqual(M.axes.map(axis=>data.categories[axis].length),[9,8,10]);
assert(M.validate(data));
const hamdan=data.entities.find(e=>e.id==='mp-381');
assert.equal(M.topicFilter(data.entities,{layer:'deputies',query:hamdan.name.ar}).some(e=>e.id===hamdan.id),true,'newly sourced MPs are searchable in Arabic');
assert.equal(M.topicFilter(data.entities,{layer:'deputies',topic:'reconstruction:8'}).some(e=>e.id===hamdan.id),true);
assert.equal(M.topicFilter(data.entities,{layer:'deputies',topic:'arms:5'}).some(e=>e.id===hamdan.id),false,'state-led reconstruction alone does not establish an arms position');
const duplicate=structuredClone(hamdan);
duplicate.stances.reconstruction.push(duplicate.stances.reconstruction[0]);
const overlapping=M.topicCounts([duplicate],'reconstruction',data.categories);
assert.equal(overlapping.filter(c=>c.entities.length).length,2,'one MP can support two themes');
assert(overlapping.every(c=>c.entities.length<=1),'multiple statements do not double-count an MP within one theme');
const invalidTopic=structuredClone(data);
invalidTopic.entities.find(e=>e.id===hamdan.id).stances.reconstruction[0].sources=['TM-01'];
assert.throws(()=>M.validate(invalidTopic),/Unattributed topic/,'reject another person’s evidence');
const party=id=>data.entities.find(e=>e.id==='party-'+id);
assert.notEqual(M.placement(party('fpm'),'arms').x,M.placement(party('amal'),'financing').x,'rejecting political conditions differs from urgent state action');
const minister=id=>data.entities.find(e=>e.id==='minister-'+id);
assert.notEqual(M.placement(party('marada'),'arms').y,M.placement(minister('mitri'),'arms').y,'political dialogue differs from a phased army plan');
assert.notEqual(M.placement(party('kataeb'),'financing').y,M.placement(minister('jaber'),'financing').y,'conditional foreign assistance differs from an infrastructure loan');
const invalid=structuredClone(data);invalid.entities.find(e=>e.positions.arms).positions.arms.category=999;
assert.throws(()=>M.validate(invalid),/Unreviewed category/);
// Labels can use neighbouring empty columns, while each photo keeps its X.
const layoutPoints=[{id:'one',x:160,width:190,height:100},{id:'two',x:280,width:190,height:130},{id:'three',x:450,width:190,height:80},{id:'four',x:450,width:190,height:160},{id:'five',x:720,width:190,height:90}];
for(const preferredSide of ['left','right']){
  const result=M.packLabels(layoutPoints,{left:124,right:900,preferredSide});
  assert.equal(result.points.length,layoutPoints.length);
  assert.deepEqual(M.packLabels(layoutPoints,{left:124,right:900,preferredSide}),result,'layout is stable across redraws');
  for(const point of result.points){
    assert.equal(point.x,layoutPoints.find(p=>p.id===point.id).x,'packing never changes the X category');
    assert(point.left>=124&&point.right<=900);
    for(const other of result.points)if(other!==point)assert(point.right<=other.left||other.right<=point.left||point.bottom<=other.top||other.bottom<=point.top,'photo, connector and label boxes never overlap');
  }
  assert(result.height<layoutPoints.reduce((sum,p)=>sum+p.height,0),'packing reuses vacant horizontal space');
}
console.log('PASS: coverage totals, category denominators, missing positions, unique citations, evidence dates, and source preservation.');
