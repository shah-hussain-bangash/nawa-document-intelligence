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
let saved={document:'synthetic.txt',status:'pending_review',revision:1,fields:{supplier:'Test',currency:'AED',subtotal:'1000.00',
  vat_rate_percent:'5',vat_amount:'50.00',total:'1050.00'},checks:{vat_matches_rate:true,total_matches_components:true},history:[],corrections:[]};
let failSave=true,holdNextShow=false,finishHeldShow=null;
async function fetch(url,opts={}) {
  let data,ok=true,status=200;
  if(url==='/auth/config')data={mode:'oidc',intake_enabled:true};
  else if(url==='/auth/me')data={role:'analyst'};
  else if(url==='/api/quotations')data={quotations:[{id:'q1',quotation}],storage:'postgres'};
  else if(url==='/api/review/show'){
    data=structuredClone(saved);
    if(holdNextShow){holdNextShow=false;await new Promise(resolve=>{finishHeldShow=resolve;});}
  }
  else if(url==='/api/review/correct'){
    if(failSave){ok=false;status=503;data={error:'Storage unavailable'};}
    else {const p=JSON.parse(opts.body);assert.equal(p.expected_revision,2);saved.corrections.push({sequence:3,field:p.field,from:saved.fields[p.field],to:p.value,reason:p.reason,evidence:{source:p.source,line:p.line,quote:p.quote}});saved.fields[p.field]=p.value;saved.checks.total_matches_components=false;saved.revision++;data=structuredClone(saved);}
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
    btoa:value=>Buffer.from(value,'binary').toString('base64'),window:{location:{reload(){}}}});
  await tick();await tick();
  let review=get('review');
  assert.equal(byText(review,'Approve'),undefined);
  byId(review,'correction-field').value='total';byId(review,'correction-value').value='1049.00';
  byId(review,'correction-reason').value='Source checked';byId(review,'correction-line').value='6';
  byId(review,'correction-quote').value='Total: 1050.00';
  await byText(review,'Save correction').events.click();
  assert.match(flatten(review).find(x=>x.className.includes('review-feedback')).textContent,/Could not save.*try again/i);
  assert.equal(byId(review,'correction-value').value,'1049.00');
  saved.revision=2;
  const reload=byText(review,'Reload saved review');assert.equal(reload.hidden,false);
  reload.events.click();await tick();await tick();
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
  holdNextShow=true;flatten(get('items')).find(x=>x.tag==='button').events.click();await tick();
  saved.revision=4;flatten(get('items')).find(x=>x.tag==='button').events.click();await tick();await tick();
  finishHeldShow();await tick();await tick();
  assert.ok(flatten(review).some(x=>x.textContent.includes('revision 4')));
  assert.equal(flatten(review).some(x=>x.textContent.includes('revision 3')),false);
  console.log('PASS: reopening preserves input and ignores out-of-order saved-review responses');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
