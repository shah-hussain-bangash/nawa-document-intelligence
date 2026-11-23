'use strict';
const $ = (id) => document.getElementById(id);
let authMode = 'unknown';
let workspaceRole = null;
const csrfToken = () => (document.cookie.split('; ').find(value=>value.startsWith('nawa_csrf='))||'').slice('nawa_csrf='.length);
const records = new Map();
let selected = null;
const message = (text, error=false) => { $('message').textContent=text; $('message').className = error?'message error':'message'; };
const sourceCheckNote = (checks) => {if(!Array.isArray(checks))return '';const pages=checks.filter(x=>x.kind==='pdf_text_layer'&&Number.isInteger(x.page)&&Number.isInteger(x.page_line)).map(x=>`page ${x.page}, line ${x.page_line}`);return pages.length?` · retained PDF text matched: ${pages.join('; ')}`:'';};
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
function renderItems(){
  const root=$('items');clear(root);
  for(const [id,q] of records){
    const item=el('div',undefined,'item'+(selected===id?' active':''));
    const chk=el('input');chk.type='checkbox';chk.dataset.id=id;chk.setAttribute('aria-label',`Compare ${q.document}`);item.append(chk);
    const body=el('button',undefined,'item-main');body.type='button';body.append(el('b',q.supplier),el('span',q.document));
    body.setAttribute('aria-label',`Open review for ${q.document}`);
    body.addEventListener('click',()=>{selected=id;renderItems();renderDetails();renderReview();});item.append(body);
    const right=el('div');right.append(el('div',`AED ${q.total}`,'amount'));
    right.append(el('span',Object.values(q.checks).every(Boolean)?'Original VAT valid':'Original VAT needs review','tag'+(Object.values(q.checks).every(Boolean)?'':' bad')));
    item.append(right);root.append(item);
  }
}
function renderDetails(review=null){
  const root=$('details');clear(root);if(!selected)return;
  const q=records.get(selected);
  const labels={supplier:'Supplier',currency:'Currency',subtotal:'Subtotal',vat_rate_percent:'VAT rate (%)',vat_amount:'VAT amount',total:'Grand total'};
  root.append(el('p',review?'Saved review values are shown beside the original source evidence.':'Original extracted values and source evidence. Start a review to save corrections.','muted'));
  for(const [field,label] of Object.entries(labels)){
    const line=el('div',undefined,'field');line.append(el('span',label));const content=el('div');
    const current=review && review.fields && typeof review.fields[field]==='string'?review.fields[field]:q[field];
    content.append(el('strong',current));
    if(review && current!==q[field])content.append(el('div',`Originally extracted: ${q[field]}`,'evidence'));
    const evidence=q.evidence[field]||q.evidence[field==='vat_rate_percent'?'vat_rate':field];
    if(evidence){
      const location=evidence.page?`Page ${evidence.page}, line ${evidence.page_line||evidence.line} (global line ${evidence.line})`:`Line ${evidence.line}`;
      content.append(el('div',`Original source · ${location}: ${evidence.source_text}`,'evidence'));
      if(typeof evidence.raw_extracted_text==='string'&&evidence.raw_extracted_text!==evidence.source_text){
        const raw=el('div',`Raw PDF text for matching: ${evidence.raw_extracted_text}`,'evidence');raw.style.whiteSpace='pre-wrap';content.append(raw);
      }
    }
    line.append(content);root.append(line);
  }
  const checks=review && review.checks?review.checks:q.checks;
  const valid=checks.vat_matches_rate===true&&checks.total_matches_components===true;
  root.append(el('p',valid?'✓ Financial checks passed':'⚠ Financial checks need review','notice'));
}
async function renderReview(){
  const root=$('review');clear(root);if(!selected){root.append(el('p','Select a quotation.','empty'));return;}
  const itemId=selected;root.append(el('p','Loading saved review…','muted'));let review;
  try{review=await request('/api/review/show',{id:itemId});}
  catch(error){
    if(selected!==itemId)return;clear(root);
    if(error.message!=='Review is not initialized'){
      root.append(el('p',`Could not open the review: ${error.message}. Try again.`,'review-error'));
      const retry=el('button','Retry opening review','secondary');retry.addEventListener('click',()=>renderReview());root.append(retry);return;
    }
    if(authMode==='oidc'&&workspaceRole!=='analyst'){
      root.append(el('p','An Analyst must start and prepare this review before a Reviewer can record a decision.','muted'));return;
    }
    const start=el('button','Start review');
    const feedback=el('p','','review-feedback');feedback.setAttribute('role','status');
    start.addEventListener('click',async()=>{try{await request('/api/review/start',{id:itemId});message('Review created. You can now correct a field.');await renderReview();}catch(error){feedback.textContent=`Could not start the review: ${error.message}. Try again.`;feedback.className='review-feedback review-error';}});
    root.append(el('p','Start a synthetic review, then select a field and provide source evidence.','muted'),start,feedback);return;
  }
  if(selected!==itemId)return;clear(root);renderDetails(review);
  root.append(el('p',`Status: ${review.status} · revision ${review.revision}`,'muted'));
  root.append(el('p','Saved review loaded. Compare the saved values with the original evidence.','review-guidance'));
  const history=el('div',undefined,'history');for(const h of review.history){history.append(el('div',`#${h.sequence} ${h.type} · ${h.actor} · ${h.timestamp}`,'row'));}
  if(review.status==='approved'||review.status==='rejected'){root.append(history);return;}
  const feedback=el('p','','review-feedback');feedback.setAttribute('role','status');feedback.setAttribute('aria-live','polite');root.append(feedback);
  const reviewTask=async(action)=>{try{feedback.textContent='';await action();}catch(error){feedback.textContent=`Could not save: ${error.message}. Check the details and try again.`;feedback.className='review-feedback review-error';}};
  const form=el('div',undefined,'review-form');const actor=el('input');actor.placeholder='Reviewer ID (demo only)';actor.value=authMode==='oidc'?'Signed-in user':'reviewer-1';actor.disabled=authMode==='oidc';form.append(el('label',authMode==='oidc'?'Review identity':'Reviewer ID'),actor);
  if(authMode!=='oidc'||workspaceRole==='reviewer'){
    const reason=el('textarea');reason.placeholder='Explain your decision';form.append(el('label','Reason / review notes'),reason);
    const controls=el('div',undefined,'horizontal');
    for(const [decision,label] of [['approve','Approve'],['request_changes','Request changes'],['reject','Reject']]){
      const button=el('button',label,decision==='approve'?'':'secondary');
      button.addEventListener('click',()=>reviewTask(async()=>{const result=await request('/api/review/decide',{id:itemId,actor:actor.value,reason:reason.value,decision,expected_revision:review.revision});message(`Recorded ${result.status}`);await renderReview();}));controls.append(button);
    }
    form.append(controls);
  }else if(workspaceRole==='analyst')form.append(el('p','After preparation, a separate Reviewer records the final decision.','muted'));
  root.append(form);
  if(authMode==='oidc'&&workspaceRole!=='analyst'){
    root.append(el('p','Corrections are prepared by an Analyst.','muted'),history);return;
  }
  const correction=el('div',undefined,'review-form');correction.append(el('h3','Correct a field'),el('p','Enter the corrected value and its exact source evidence. For PDFs, use the global line and raw text shown in extracted fields.','muted'));
  function inputLabel(label,control,id){const name=el('label',label);name.setAttribute('for',id);control.id=id;correction.append(name,control);}
  const fields=el('select');for(const [key,label] of Object.entries({supplier:'Supplier',currency:'Currency',subtotal:'Subtotal',vat_rate_percent:'VAT rate (%)',vat_amount:'VAT amount',total:'Grand total'})){const option=el('option',label);option.value=key;fields.append(option);}inputLabel('Field to correct',fields,'correction-field');
  const value=el('input');inputLabel('Corrected value',value,'correction-value');
  const note=el('input');inputLabel('Reason for correction',note,'correction-reason');
  const evidenceLine=el('input');evidenceLine.type='number';evidenceLine.min='1';inputLabel('Original source line',evidenceLine,'correction-line');
  const quote=el('textarea');inputLabel('Exact source excerpt',quote,'correction-quote');
  const save=el('button','Save correction','secondary');
  save.addEventListener('click',()=>reviewTask(async()=>{
    const result=await request('/api/review/correct',{id:itemId,actor:actor.value,field:fields.value,value:value.value,reason:note.value,source:review.document,line:Number(evidenceLine.value),quote:quote.value,expected_revision:review.revision});
    message(`Correction saved, revision ${result.revision}. Reopen the quotation to check it.${sourceCheckNote(result.source_checks)}`);await renderReview();
  }));
  correction.append(save);root.append(el('hr'),correction,history);
}
$('loadSample').addEventListener('click',()=>task(async()=>loaded(await request('/api/load-sample',{name:$('sample').value}))));
$('uploadBtn').addEventListener('click',async()=>{const feedback=$('uploadFeedback');feedback.textContent='';try{const file=$('upload').files[0];if(!file)throw new Error('Choose a synthetic TXT or PDF file');if(file.size>4*1024*1024)throw new Error('File exceeds 4 MiB');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=16384){binary+=String.fromCharCode(...bytes.subarray(i,i+16384));}loaded(await request('/api/upload',{filename:file.name,content_base64:btoa(binary)}));feedback.className='review-feedback';feedback.textContent='Quotation loaded. Open its review below to check the extracted values.';}catch(error){feedback.className='review-feedback review-error';feedback.textContent=`Could not load the quotation: ${error.message}. Check the file and try again.`;}});
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
  const accepted=result.files.filter(item=>item.id).length;
  message(`${accepted} of ${files.length} files accepted or already stored.`,accepted===0);
}));
$('intakeRefresh').addEventListener('click',()=>task(async()=>{
  const response=await fetch('/api/intake/documents');const result=await response.json();
  if(!response.ok)throw new Error(result.error||'Documents unavailable');
  const root=$('intakeJobs');clear(root);
  if(!result.documents.length){root.append(el('p','No synthetic documents found.','empty'));return;}
  for(const item of result.documents){
    const row=el('div',undefined,'row');
    row.append(el('span',`${item.filename} · ${item.state} · attempts: ${item.attempts} · ID: ${item.id}`));
    const use=el('button','Use document','secondary');
    use.addEventListener('click',()=>{$('intakeId').value=item.id;$('intakeStatus').textContent='Document selected. Check its status or choose an action.';});
    row.append(use);root.append(row);
  }
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
$('intakePromote').addEventListener('click',()=>task(async()=>{
  const id=$('intakeId').value.trim();if(!id)throw new Error('Enter a completed document ID');
  const result=await request('/api/intake/promote',{id});loaded(result);
  message(result.created?'Document added to quotation review.':'Document is already in quotation review.');
}));
for(const [button,action] of [['intakeRevalidate','revalidate'],['intakeRetry','retry']]){
  $(button).addEventListener('click',()=>task(async()=>{
    const id=$('intakeId').value.trim(), reason=$('requeueReason').value.trim();
    if(!id||!reason)throw new Error('Enter a document ID and a reason');
    const result=await request('/api/intake/'+action,{id,reason});
    $('intakeStatus').textContent=`Status: ${result.state}. The worker will process the document.`;
    message('The request was recorded.');
  }));
}
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
$('compareBtn').addEventListener('click',()=>task(async()=>{const ids=Array.from(document.querySelectorAll('#items input:checked')).map(x=>x.dataset.id);const result=await request('/api/compare',{ids});const root=$('comparison');clear(root);for(const q of result.quotations){const excluded=q.comparison&&q.comparison.eligible===false;const state=excluded?'Excluded (review not approved)':Object.values(q.checks).every(Boolean)?'Valid':'Excluded (financial mismatch)';const basis=q.comparison?.basis==='approved_review'?` · approved review revision ${q.comparison.review_revision}`:'';root.append(el('div',`${q.supplier} — AED ${q.total} — ${state}${basis}${sourceCheckNote(q.comparison?.source_checks)}`,'row'));}root.append(el('p',`Lowest valid total: ${result.lowest_valid_total||'None'}`));root.append(el('p',result.note,'muted'));message('Comparison completed');}));
async function initialize(){const main=document.querySelector('main');main.hidden=true;try{const config=await fetch('/auth/config');if(!config.ok)throw new Error('Authentication configuration unavailable');const auth=await config.json();authMode=auth.mode;if(!['demo','oidc'].includes(authMode))throw new Error('Unknown authentication mode');if(authMode==='oidc'){const me=await fetch('/auth/me');if(me.status===403){$('signin').hidden=false;return;}if(!me.ok)throw new Error('Identity service unavailable');const identity=await me.json();workspaceRole=identity.role;if(workspaceRole!=='analyst'){$('roleNotice').textContent='An Analyst uploads and prepares quotations; a Reviewer records the final decision.';for(const id of ['loadSample','uploadBtn','intakeSubmit','intakePromote'])$(id).disabled=true;}$('logout').hidden=false;if(auth.intake_enabled===true)$('intakePanel').hidden=false;}else{$('footerNote').textContent+=' · Reviewer identities are not authenticated';}main.hidden=false;const response=await fetch('/api/quotations');const result=await response.json();if(!response.ok)throw new Error(result.error||'Storage unavailable');for(const row of result.quotations)records.set(row.id,row.quotation);$('count').textContent=records.size;if(records.size){selected=records.keys().next().value;renderItems();renderDetails();renderReview();}const note=$('storageMode');if(note)note.textContent=result.storage==='postgres'?'PostgreSQL development storage':'Local, in-memory decisions';}catch(error){$('signin').hidden=false;$('signinError').textContent=error.message;}}
$('logout').addEventListener('click',()=>task(async()=>{const response=await fetch('/auth/logout',{method:'POST',headers:{'X-NAWA-CSRF':csrfToken()}});if(!response.ok)throw new Error('Sign-out failed');window.location.reload();}));
initialize();


