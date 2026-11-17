'use strict';
const $ = (id) => document.getElementById(id);
let authMode = 'unknown';
const csrfToken = () => (document.cookie.split('; ').find(value=>value.startsWith('nawa_csrf='))||'').slice('nawa_csrf='.length);
const records = new Map();
let selected = null;
const message = (text, error=false) => { $('message').textContent=text; $('message').className = error?'message error':'message'; };
async function request(path, payload) {
  const response = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',...(authMode==='oidc'?{'X-NAWA-CSRF':csrfToken()}:{})},body:JSON.stringify(payload)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error||'Request failed');
  return result;
}
async function task(action){try{await action();}catch(e){message(e.message,true);}}
function el(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=String(text);if(className)node.className=className;return node;}
function clear(node){node.replaceChildren();}
function loaded(row){records.set(row.id,row.quotation);selected=row.id;$('count').textContent=records.size;renderItems();renderDetails();renderReview();message(`Loaded ${row.quotation.document}`);}
function renderItems(){const root=$('items');clear(root);for(const [id,q] of records){const item=el('div',undefined,'item'+(selected===id?' active':''));const chk=el('input');chk.type='checkbox';chk.dataset.id=id;chk.setAttribute('aria-label',`Compare ${q.document}`);item.append(chk);const body=el('div',undefined,'item-main');body.append(el('b',q.supplier));body.append(el('span',q.document));body.addEventListener('click',()=>{selected=id;renderItems();renderDetails();renderReview();});item.append(body);const right=el('div');right.append(el('div',`AED ${q.total}`,'amount'));right.append(el('span',Object.values(q.checks).every(Boolean)?'Valid VAT':'Review VAT','tag'+(Object.values(q.checks).every(Boolean)?'':' bad')));item.append(right);root.append(item);}}
function renderDetails(){const root=$('details');clear(root);if(!selected)return;const q=records.get(selected);const labels={supplier:'Supplier',currency:'Currency',subtotal:'Subtotal',vat_rate_percent:'VAT rate (%)',vat_amount:'VAT amount',total:'Grand total'};for(const [field,label] of Object.entries(labels)){const line=el('div',undefined,'field');line.append(el('span',label));const content=el('div');content.append(el('strong',q[field]));const evidence=q.evidence[field]||q.evidence[field==='vat_rate_percent'?'vat_rate':field];if(evidence){content.append(el('div',`Line ${evidence.page?evidence.page+':':''}${evidence.page_line||evidence.line}: ${evidence.source_text}`,'evidence'));}line.append(content);root.append(line);}const check=el('p',Object.values(q.checks).every(Boolean)?'✓ Financial checks passed':'⚠ Financial mismatch: review required','notice');root.append(check);}
async function renderReview(){const root=$('review');clear(root);if(!selected){root.append(el('p','Select a quotation.','empty'));return;}const itemId=selected;let review;try{review=await request('/api/review/show',{id:itemId});}catch(error){if(error.message!=='Review is not initialized'){message(error.message,true);return;}const start=el('button','Start review');start.addEventListener('click',()=>task(async()=>{await request('/api/review/start',{id:itemId});message('Review created');await renderReview();}));root.append(el('p','Start a synthetic review with revision tracking.','muted'));root.append(start);return;}if(selected!==itemId)return;root.append(el('p',`Status: ${review.status} · revision ${review.revision}`,'muted'));const history=el('div',undefined,'history');for(const h of review.history){history.append(el('div',`#${h.sequence} ${h.type} · ${h.actor} · ${h.timestamp}`,'row'));}if(review.status==='approved'||review.status==='rejected'){root.append(history);return;}const form=el('div',undefined,'review-form');const actor=el('input');actor.placeholder='Reviewer ID (demo only)';actor.value=authMode==='oidc'?'Authenticated reviewer':'reviewer-1';actor.disabled=authMode==='oidc';form.append(el('label',authMode==='oidc'?'Review identity':'Reviewer ID')); form.append(actor);const reason=el('textarea');reason.placeholder='Explain your decision';form.append(el('label','Reason / review notes'));form.append(reason);const controls=el('div',undefined,'horizontal');for(const [decision,label] of [['approve','Approve'],['request_changes','Request changes'],['reject','Reject']]){const button=el('button',label,decision==='approve'?'':'secondary');button.addEventListener('click',()=>task(async()=>{const result=await request('/api/review/decide',{id:itemId,actor:actor.value,reason:reason.value,decision,expected_revision:review.revision});message(`Recorded ${result.status}`);renderReview();}));controls.append(button);}form.append(controls);root.append(form);
const correction=el('div',undefined,'review-form');correction.append(el('label','Correction (requires source evidence)'));const fields=el('select');for(const key of ['supplier','currency','subtotal','vat_rate_percent','vat_amount','total']){const option=el('option',key);option.value=key;fields.append(option);}const value=el('input');value.placeholder='Corrected value';const note=el('input');note.placeholder='Reason for correction';const evidenceLine=el('input');evidenceLine.placeholder='Evidence line number';evidenceLine.type='number';evidenceLine.min='1';const quote=el('textarea');quote.placeholder='Verbatim excerpt from source (reviewer assertion)';const save=el('button','Record correction','secondary');save.addEventListener('click',()=>task(async()=>{const result=await request('/api/review/correct',{id:itemId,actor:actor.value,field:fields.value,value:value.value,reason:note.value,source:review.document,line:Number(evidenceLine.value),quote:quote.value,expected_revision:review.revision});message(`Correction recorded, revision ${result.revision}`);renderReview();renderDetails();}));for(const x of [fields,value,note,evidenceLine,quote,save])correction.append(x);root.append(el('hr'));root.append(correction);root.append(history);}
$('loadSample').addEventListener('click',()=>task(async()=>loaded(await request('/api/load-sample',{name:$('sample').value}))));
$('uploadBtn').addEventListener('click',()=>task(async()=>{const file=$('upload').files[0];if(!file)throw new Error('Choose a synthetic TXT or PDF file');if(file.size>4*1024*1024)throw new Error('File exceeds 4 MiB');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=16384){binary+=String.fromCharCode(...bytes.subarray(i,i+16384));}loaded(await request('/api/upload',{filename:file.name,content_base64:btoa(binary)}));}));
$('intakeSubmit').addEventListener('click',()=>task(async()=>{
  const files=Array.from($('intakeFiles').files);
  if(!files.length||files.length>10)throw new Error('Choose between 1 and 10 synthetic files');
  const batch=[];
  for(const file of files){
    if(file.size>4*1024*1024)throw new Error('Each file must be at most 4 MiB');
    const bytes=new Uint8Array(await file.arrayBuffer());let binary='';
    for(let i=0;i<bytes.length;i+=16384)binary+=String.fromCharCode(...bytes.subarray(i,i+16384));
    batch.push({filename:file.name,content_base64:btoa(binary)});
  }
  if(new TextEncoder().encode(JSON.stringify({files:batch})).length>8*1024*1024)throw new Error('The selected batch is too large; submit fewer files');
  const result=await request('/api/intake/batch',{files:batch});const root=$('intakeResults');clear(root);
  result.files.forEach((item,index)=>{const detail=item.error||`${item.created?'Submitted':'Already submitted'} · ID: ${item.id}`;root.append(el('p',`${files[index].name}: ${detail}`,'row'));});
  message('Batch submitted. Check each document status below.');
}));
$('intakeCheck').addEventListener('click',()=>task(async()=>{
  const id=$('intakeId').value.trim();if(!id)throw new Error('Enter a document ID');
  const response=await fetch('/api/intake/status?id='+encodeURIComponent(id));const status=await response.json();
  if(!response.ok)throw new Error(status.error||'Status unavailable');
  let text=`Status: ${status.state} · attempts: ${status.attempts}`;
  if(status.state==='completed'){
    const resultResponse=await fetch('/api/intake/result?id='+encodeURIComponent(id));const result=await resultResponse.json();
    if(!resultResponse.ok)throw new Error(result.error||'Result unavailable');
    text+=` · Supplier: ${result.result.supplier} · Total: AED ${result.result.total}`;
  }
  $('intakeStatus').textContent=text;
}));
$('versionLink').addEventListener('click',()=>task(async()=>{
  const id=$('intakeId').value.trim();const family=$('versionFamily').value.trim();const raw=$('versionPrevious').value.trim();
  if(!id||!/^\d+$/.test(raw)||!Number.isSafeInteger(Number(raw)))throw new Error('Enter a document ID and a valid latest version number');
  const result=await request('/api/intake/version',{id,family_id:family||null,expected_previous:Number(raw)});
  $('versionFamily').value=result.family_id;$('versionPrevious').value=String(result.version);
  $('versionResults').textContent=`Linked version ${result.version}. Family ID: ${result.family_id}`;
}));
$('versionHistory').addEventListener('click',()=>task(async()=>{
  const family=$('versionFamily').value.trim();if(!family)throw new Error('Enter a version family ID');
  const response=await fetch('/api/intake/versions?family='+encodeURIComponent(family));const result=await response.json();
  if(!response.ok)throw new Error(result.error||'Version history unavailable');
  const root=$('versionResults');clear(root);
  for(const item of result.versions)root.append(el('p',`Version ${item.version} · Document ID: ${item.id}`,'row'));
}));
$('compareBtn').addEventListener('click',()=>task(async()=>{const ids=Array.from(document.querySelectorAll('#items input:checked')).map(x=>x.dataset.id);const result=await request('/api/compare',{ids});const root=$('comparison');clear(root);for(const q of result.quotations){root.append(el('div',`${q.supplier} — AED ${q.total} — ${Object.values(q.checks).every(Boolean)?'Valid':'Excluded (financial mismatch)'}`,'row'));}root.append(el('p',`Lowest valid total: ${result.lowest_valid_total||'None'}`));root.append(el('p',result.note,'muted'));message('Comparison completed');}));
async function initialize(){const main=document.querySelector('main');main.hidden=true;try{const config=await fetch('/auth/config');if(!config.ok)throw new Error('Authentication configuration unavailable');const auth=await config.json();authMode=auth.mode;if(!['demo','oidc'].includes(authMode))throw new Error('Unknown authentication mode');if(authMode==='oidc'){const me=await fetch('/auth/me');if(me.status===403){$('signin').hidden=false;return;}if(!me.ok)throw new Error('Identity service unavailable');$('logout').hidden=false;if(auth.intake_enabled===true)$('intakePanel').hidden=false;}else{$('footerNote').textContent+=' · Reviewer identities are not authenticated';}main.hidden=false;const response=await fetch('/api/quotations');const result=await response.json();if(!response.ok)throw new Error(result.error||'Storage unavailable');for(const row of result.quotations)records.set(row.id,row.quotation);$('count').textContent=records.size;if(records.size){selected=records.keys().next().value;renderItems();renderDetails();renderReview();}const note=$('storageMode');if(note)note.textContent=result.storage==='postgres'?'PostgreSQL development storage':'Local, in-memory decisions';}catch(error){$('signin').hidden=false;$('signinError').textContent=error.message;}}
$('logout').addEventListener('click',()=>task(async()=>{const response=await fetch('/auth/logout',{method:'POST',headers:{'X-NAWA-CSRF':csrfToken()}});if(!response.ok)throw new Error('Sign-out failed');window.location.reload();}));
initialize();
