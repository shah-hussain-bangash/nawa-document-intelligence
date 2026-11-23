'use strict';
// Deterministic DOM/API simulation; not a browser, identity, or database test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function element(tag='div') {
  return {tag, hidden:true, textContent:'', className:'', value:'', files:[], children:[], events:{}, dataset:{}, style:{},
    addEventListener(name, handler){this.events[name]=handler;},
    append(...nodes){this.children.push(...nodes);}, replaceChildren(...nodes){this.children=nodes;}, setAttribute() {}};
}
const nodes=new Map(), get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);};
const main=element(), document={cookie:'nawa_csrf=test',getElementById:get,createElement:element,
  querySelector:s=>s==='main'?main:null,querySelectorAll:()=>[]};
const evidence={supplier:{line:1,source_text:'Supplier: Test'},currency:{line:2,source_text:'Currency: AED'},
  subtotal:{line:3,source_text:'Subtotal: 1000.00'},vat_rate:{line:4,source_text:'VAT Rate: 5'},
  vat_amount:{line:5,source_text:'VAT Amount: 50.00'},total:{line:6,source_text:'Total: 1050.00'}};
const quotation={document:'synthetic.txt',supplier:'Test',currency:'AED',subtotal:'1000.00',vat_rate_percent:'5',
  vat_amount:'50.00',total:'1050.00',evidence,checks:{vat_matches_rate:true,total_matches_components:true}};
const quotation2={...quotation,document:'second-synthetic.txt'};
let saved={document:'synthetic.txt',status:'pending_review',revision:1,fields:{supplier:'Test',currency:'AED',subtotal:'1000.00',
  vat_rate_percent:'5',vat_amount:'50.00',total:'1050.00'},checks:{vat_matches_rate:true,total_matches_components:true},history:[],corrections:[]};
let failSave=true,holdNextShow=false,finishHeldShow=null,holdNextSave=false,finishHeldSave=null;
let reloadCount=0;
let correctionRequests=0;
let uninitializedQ1=false,finishHeldStart=null;
const windowEvents={};
async function fetch(url,opts={}) {
  let data,ok=true,status=200;
  if(url==='/auth/config')data={mode:'oidc',intake_enabled:true};
  else if(url==='/auth/me')data={role:'analyst'};
  else if(url==='/api/quotations')data={quotations:[{id:'q1',quotation},{id:'q2',quotation:quotation2}],storage:'postgres'};
  else if(url==='/api/review/show'){
    if(uninitializedQ1&&JSON.parse(opts.body).id==='q1')return {ok:false,status:400,json:async()=>({error:'Review is not initialized'})};
    data=structuredClone(saved);
    if(JSON.parse(opts.body).id==='q2')data.document='second-synthetic.txt';
    if(holdNextShow){holdNextShow=false;await new Promise(resolve=>{finishHeldShow=resolve;});}
  }
  else if(url==='/api/review/start'){
    await new Promise(resolve=>{finishHeldStart=resolve;});uninitializedQ1=false;data={};
  }
  else if(url==='/api/review/correct'){
    correctionRequests++;
    if(failSave){ok=false;status=503;data={error:'Storage unavailable'};}
    else {const p=JSON.parse(opts.body);assert.equal(p.expected_revision,saved.revision);if(holdNextSave){holdNextSave=false;await new Promise(resolve=>{finishHeldSave=resolve;});}saved.corrections.push({sequence:saved.revision+1,field:p.field,from:saved.fields[p.field],to:p.value,reason:p.reason,evidence:{source:p.source,line:p.line,quote:p.quote}});saved.fields[p.field]=p.value;saved.checks.total_matches_components=false;saved.revision++;data=structuredClone(saved);}
  }else throw Error('Unexpected '+url);
  return {ok,status,json:async()=>data};
}
function flatten(node){return [node,...node.children.flatMap(flatten)];}
function byId(root,id){return flatten(root).find(node=>node.id===id);}
function byText(root,text){return flatten(root).find(node=>node.textContent===text);}
async function tick(){await new Promise(resolve=>setImmediate(resolve));}
async function run(){
  const source=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
  vm.runInNewContext(source,{document,fetch,TextEncoder,Uint8Array,Map,Array,String,JSON,
    btoa:value=>Buffer.from(value,'binary').toString('base64'),window:{addEventListener(name,handler){windowEvents[name]=handler;},confirm(){return false;},location:{reload(){reloadCount++;}}}});
  await tick();await tick();
  let review=get('review');
  assert.equal(byText(review,'Approve'),undefined);
  byId(review,'correction-field').value='total';byId(review,'correction-value').value='1049.00';
  byId(review,'correction-reason').value='Source checked';byId(review,'correction-line').value='6';
  byId(review,'correction-quote').value='Total: 1050.00';
  const leaveEvent={prevented:false,preventDefault(){this.prevented=true;}};
  windowEvents.beforeunload(leaveEvent);assert.equal(leaveEvent.prevented,true);
  await get('logout').events.click();assert.equal(reloadCount,0);
  await byText(review,'Save correction').events.click();
  assert.match(flatten(review).find(x=>x.className.includes('review-feedback')).textContent,/Could not save.*try again/i);
  assert.equal(byId(review,'correction-value').value,'1049.00');
  flatten(get('items')).filter(x=>x.tag==='button')[1].events.click();await tick();await tick();
  byId(review,'correction-field').value='total';byId(review,'correction-value').value='222.00';
  byId(review,'correction-reason').value='Second quotation';
  flatten(get('items')).filter(x=>x.tag==='button')[0].events.click();await tick();await tick();
  assert.equal(byId(review,'correction-value').value,'1049.00');
  assert.equal(byId(review,'correction-reason').value,'Source checked');
  assert.ok(flatten(review).some(x=>x.textContent.includes('only in this tab')));
  flatten(get('items')).filter(x=>x.tag==='button')[1].events.click();await tick();await tick();
  assert.equal(byId(review,'correction-value').value,'222.00');
  flatten(get('items')).filter(x=>x.tag==='button')[0].events.click();await tick();await tick();
  saved.revision=2;
  byText(review,'Reopen saved review').events.click();await tick();await tick();
  assert.equal(byId(review,'correction-field').value,'total');
  assert.equal(byId(review,'correction-value').value,'1049.00');
  assert.equal(byId(review,'correction-reason').value,'Source checked');
  assert.ok(flatten(review).some(x=>x.textContent.includes('revision 2')));
  failSave=false;await byText(review,'Save correction').events.click();
  assert.ok(flatten(get('details')).some(x=>x.textContent==='1049.00'));
  assert.ok(flatten(get('details')).some(x=>x.textContent==='Originally extracted: 1050.00'));
  assert.ok(flatten(get('details')).some(x=>x.textContent.includes('Original source')));
  assert.ok(flatten(get('details')).some(x=>x.textContent.includes('Financial checks need review')));
  assert.ok(flatten(review).some(x=>x.textContent==='Cited excerpt: Total: 1050.00'));
  assert.ok(flatten(review).some(x=>x.textContent.includes('Compare them with the original source')));
  assert.ok(flatten(review).some(x=>x.textContent.includes('revision 3')));
  byId(review,'correction-value').value='1048.00';
  byText(review,'Reopen saved review').events.click();await tick();await tick();
  assert.equal(byId(review,'correction-value').value,'1048.00');
  assert.ok(flatten(review).some(x=>x.textContent.includes('reopened from the server at revision 3')));
  await flatten(get('items')).find(x=>x.tag==='button').events.click();await tick();await tick();
  assert.ok(flatten(get('details')).some(x=>x.textContent==='1049.00'));
  assert.ok(flatten(get('review')).some(x=>x.textContent.includes('revision 3')));
  byId(review,'correction-field').value='total';byId(review,'correction-value').value='1047.00';
  byId(review,'correction-reason').value='Later correction';byId(review,'correction-line').value='6';
  byId(review,'correction-quote').value='Total: 1050.00';
  holdNextSave=true;const delayedSave=byText(review,'Save correction').events.click();await tick();
  flatten(get('items')).filter(x=>x.tag==='button')[1].events.click();await tick();await tick();
  assert.equal(byId(review,'correction-value').value,'222.00');
  finishHeldSave();await delayedSave;await tick();
  assert.equal(byId(review,'correction-value').value,'222.00');
  assert.match(get('message').textContent,/saved for synthetic\.txt, revision 4/i);
  flatten(get('items')).filter(x=>x.tag==='button')[0].events.click();await tick();await tick();
  assert.ok(flatten(get('details')).some(x=>x.textContent==='1047.00'));
  assert.equal(byId(review,'correction-value').value,'');
  holdNextShow=true;flatten(get('items')).find(x=>x.tag==='button').events.click();await tick();
  saved.revision=5;flatten(get('items')).find(x=>x.tag==='button').events.click();await tick();await tick();
  finishHeldShow();await tick();await tick();
  assert.ok(flatten(review).some(x=>x.textContent.includes('revision 5')));
  assert.equal(flatten(review).some(x=>x.textContent.includes('revision 4')),false);
  byId(review,'correction-value').value='First draft';
  uninitializedQ1=true;byText(review,'Reopen saved review').events.click();await tick();await tick();
  const start=byText(review,'Start review');const pendingStart=start.events.click();await tick();
  assert.equal(start.disabled,true);
  flatten(get('items')).filter(x=>x.tag==='button')[1].events.click();await tick();await tick();
  assert.equal(byId(review,'correction-value').value,'222.00');
  finishHeldStart();await pendingStart;await tick();
  assert.equal(byId(review,'correction-value').value,'222.00');
  assert.match(get('message').textContent,/Review created for synthetic\.txt/);
  document.cookie='nawa_csrf=different-session';
  const requestsBefore=correctionRequests;
  await byText(review,'Save correction').events.click();
  assert.equal(correctionRequests,requestsBefore);
  assert.equal(main.hidden,true);
  assert.equal(get('sessionTransition').hidden,false);
  assert.equal(reloadCount,0);
  get('sessionRefresh').events.click();
  assert.equal(reloadCount,1);
  console.log('PASS: quotation drafts stay isolated and saved-review responses remain ordered');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
