'use strict';
const $ = (id) => document.getElementById(id);
let authMode = 'unknown';
let workspaceRole = null;
let intakeEnabled = false;
const csrfToken = () => (document.cookie.split('; ').find(value=>value.startsWith('nawa_csrf='))||'').slice('nawa_csrf='.length);
const records = new Map();
let selected = null;
let reviewRequestVersion = 0;
const message = (text, error=false) => { $('message').textContent=text; $('message').className = error?'message error':'message'; };
const sourceCheckNote = (checks) => {if(!Array.isArray(checks))return '';const pages=checks.filter(x=>x.kind==='pdf_text_layer'&&Number.isInteger(x.page)&&Number.isInteger(x.page_line)).map(x=>`page ${x.page}, line ${x.page_line}`);return pages.length?` · retained PDF text matched: ${pages.join('; ')}`:'';};
async function request(path, payload) {
  const response = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',...(authMode==='oidc'?{'X-NAWA-CSRF':csrfToken()}:{})},body:JSON.stringify(payload)});
  const result = await response.json();
  if (!response.ok){const error=new Error(result.error||'Request failed');error.status=response.status;throw error;}
  return result;
}
async function task(action){try{await action();}catch(e){message(e.message,true);}}
function el(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=String(text);if(className)node.className=className;return node;}
function clear(node){node.replaceChildren();}
function showUnsaved(root,draft){
  if(!draft)return;
  root.append(el('p','Your entries below were not confirmed as saved.','review-error'));
  if(draft.correction)for(const [label,value] of Object.entries(draft.correction))root.append(el('p',`${label}: ${value}`,'muted'));
  if(draft.reason)root.append(el('p',`Decision notes: ${draft.reason}`,'muted'));
}
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
async function renderReview(draft=null,reopened=false){
  const root=$('review');clear(root);if(!selected){root.append(el('p','Select a quotation.','empty'));return;}
  const itemId=selected, requestVersion=++reviewRequestVersion;root.append(el('p','Loading saved review…','muted'));let review;
  try{review=await request('/api/review/show',{id:itemId});}
  catch(error){
    if(selected!==itemId||reviewRequestVersion!==requestVersion)return;clear(root);
    if(error.message!=='Review is not initialized'){
      root.append(el('p',`Could not open the review: ${error.message}. Try again.`,'review-error'));
      showUnsaved(root,draft);
      const retry=el('button','Retry opening review','secondary');retry.addEventListener('click',()=>renderReview(draft,reopened));root.append(retry);return;
    }
    if(authMode==='oidc'&&workspaceRole!=='analyst'){
      root.append(el('p','An Analyst must start and prepare this review before a Reviewer can record a decision.','muted'));showUnsaved(root,draft);return;
    }
    const start=el('button','Start review');
    const feedback=el('p','','review-feedback');feedback.setAttribute('role','status');
    start.addEventListener('click',async()=>{try{await request('/api/review/start',{id:itemId});message('Review created. You can now correct a field.');await renderReview(draft);}catch(error){feedback.textContent=`Could not start the review: ${error.message}. Try again.`;feedback.className='review-feedback review-error';}});
    root.append(el('p','Start a synthetic review, then select a field and provide source evidence.','muted'));showUnsaved(root,draft);root.append(start,feedback);return;
  }
  if(selected!==itemId||reviewRequestVersion!==requestVersion)return;clear(root);renderDetails(review);
  root.append(el('p',`Status: ${review.status} · revision ${review.revision}`,'muted'));
  const guidance=el('p',reopened?`Saved review reopened from the server at revision ${review.revision}.`:'Saved review loaded. Compare the saved values with the original evidence.','review-guidance');guidance.setAttribute('role','status');root.append(guidance);
  let captureDraft=()=>null;
  const reopen=el('button','Reopen saved review','secondary');reopen.addEventListener('click',()=>renderReview(captureDraft(),true));root.append(reopen);
  const corrections=Array.isArray(review.corrections)?review.corrections:null;
  if(corrections&&corrections.length){
    const evidencePanel=el('section',undefined,'correction-evidence');
    evidencePanel.append(el('h3','Evidence cited for corrections'));
    evidencePanel.append(el('p','The preparer supplied these excerpts. Compare them with the original source; a matching line alone does not prove the corrected value.','muted'));
    for(const change of corrections){
      const entry=el('div',undefined,'correction-evidence-entry');
      const cited=change.evidence||{};
      entry.append(el('strong',`Revision ${change.sequence} · ${change.field}: ${change.from} → ${change.to}`));
      entry.append(el('p',`Reason: ${change.reason}`),el('p',`Source: ${cited.source} · line ${cited.line}`));
      const excerpt=el('p',`Cited excerpt: ${cited.quote}`);excerpt.setAttribute('dir','auto');entry.append(excerpt);evidencePanel.append(entry);
    }
    root.append(evidencePanel);
  }else if(!corrections&&review.history.some(item=>item.type==='correction')){
    root.append(el('p','Correction evidence is unavailable in this response. Verify the original source before deciding.','review-error'));
  }
  const history=el('div',undefined,'history');for(const h of review.history){history.append(el('div',`#${h.sequence} ${h.type} · ${h.actor} · ${h.timestamp}`,'row'));}
  if(review.status==='approved'||review.status==='rejected'){
    if(draft){
      root.append(el('p','This review is final. Your input could not be confirmed as saved.','review-error'));
      showUnsaved(root,draft);
    }
    root.append(history);return;
  }
  if(draft)root.append(el('p','Latest review loaded. Your unsaved entries are still below; check the revision before saving.','review-guidance'));
  const feedback=el('p','','review-feedback');feedback.setAttribute('role','status');feedback.setAttribute('aria-live','polite');root.append(feedback);
  const reload=el('button','Reload saved review','secondary');reload.hidden=true;root.append(reload);
  let correctionInputs=null, decisionReason=null;
  const reviewTask=async(action,decision=false)=>{try{feedback.textContent='';reload.hidden=true;await action();}catch(error){feedback.textContent=decision&&error.status===403?'Decision denied. Check your access or ask another authorized Reviewer if you prepared this review.':`Could not save: ${error.message}. Check the details and try again, or reload the latest review.`;feedback.className='review-feedback review-error';reload.hidden=false;}};
  const form=el('div',undefined,'review-form');const actor=el('input');actor.placeholder='Reviewer ID (demo only)';actor.value=authMode==='oidc'?'Signed-in user':'reviewer-1';actor.disabled=authMode==='oidc';form.append(el('label',authMode==='oidc'?'Review identity':'Reviewer ID'),actor);
  if(draft && authMode!=='oidc')actor.value=draft.actor;
  captureDraft=()=>{
    const entries=correctionInputs?Object.fromEntries(Object.entries(correctionInputs).map(([key,input])=>[key,input.value])):null;
    const reason=decisionReason?decisionReason.value:'';
    const hasEntries=entries&&(['value','note','line','quote'].some(key=>entries[key].trim())||entries.field!=='supplier');
    return hasEntries||reason.trim()?{actor:actor.value,reason,correction:entries}:null;
  };
  reload.addEventListener('click',()=>renderReview(captureDraft(),true));
  if(authMode!=='oidc'||workspaceRole==='reviewer'){
    const reason=el('textarea');reason.placeholder='Explain your decision';if(draft)reason.value=draft.reason;decisionReason=reason;form.append(el('label','Reason / review notes'),reason);
    const controls=el('div',undefined,'horizontal');
    for(const [decision,label] of [['approve','Approve'],['request_changes','Request changes'],['reject','Reject']]){
      const button=el('button',label,decision==='approve'?'':'secondary');
      button.addEventListener('click',()=>reviewTask(async()=>{const result=await request('/api/review/decide',{id:itemId,actor:actor.value,reason:reason.value,decision,expected_revision:review.revision});message(`Recorded ${result.status}`);await renderReview();},true));controls.append(button);
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
  correctionInputs={field:fields,value,note,line:evidenceLine,quote};
  if(draft&&draft.correction)for(const [key,input] of Object.entries(correctionInputs))input.value=draft.correction[key]||'';
  const save=el('button','Save correction','secondary');
  save.addEventListener('click',()=>reviewTask(async()=>{
    const result=await request('/api/review/correct',{id:itemId,actor:actor.value,field:fields.value,value:value.value,reason:note.value,source:review.document,line:Number(evidenceLine.value),quote:quote.value,expected_revision:review.revision});
    message(`Correction saved, revision ${result.revision}. Reopen the quotation to check it.${sourceCheckNote(result.source_checks)}`);await renderReview();
  }));
  correction.append(save);root.append(el('hr'),correction,history);
}
$('loadSample').addEventListener('click',()=>task(async()=>loaded(await request('/api/load-sample',{name:$('sample').value}))));
$('uploadBtn').addEventListener('click',async()=>{
  const feedback=$('uploadFeedback'), button=$('uploadBtn');feedback.textContent='';button.disabled=true;
  try{
    const file=$('upload').files[0];if(!file)throw new Error('Choose a synthetic TXT or PDF file');
    if(file.size>4*1024*1024)throw new Error('File exceeds 4 MiB');
    const bytes=new Uint8Array(await file.arrayBuffer());let binary='';
    for(let i=0;i<bytes.length;i+=16384)binary+=String.fromCharCode(...bytes.subarray(i,i+16384));
    const encoded=btoa(binary);let result;
    if(intakeEnabled){
      feedback.className='review-feedback';feedback.textContent='Uploading the source for processing…';
      const batch=await request('/api/intake/batch',{files:[{filename:file.name,content_base64:encoded}]});
      const item=Array.isArray(batch.files)?batch.files[0]:null;
      if(!item||!item.id)throw new Error(item&&item.error||'The document was not accepted');
      const id=item.id;$('intakeId').value=id;
      for(let attempt=0;attempt<40;attempt++){
        feedback.textContent='Processing the quotation. Please wait…';
        const response=await fetch('/api/intake/status?id='+encodeURIComponent(id));const status=await response.json();
        if(!response.ok)throw new Error(status.error||'Document status unavailable');
        if(status.state==='completed'){result=await request('/api/intake/promote',{id});break;}
        if(status.state==='failed')throw new Error('Processing failed. Use Retry failed file in document intake below');
        if(attempt<39)await new Promise(resolve=>setTimeout(resolve,1000));
      }
      if(!result)throw new Error('Processing is still pending. Use Check status in document intake below');
    }else result=await request('/api/upload',{filename:file.name,content_base64:encoded});
    loaded(result);feedback.className='review-feedback';feedback.textContent='Quotation loaded. Start or open its review below to check the extracted values.';
  }catch(error){feedback.className='review-feedback review-error';feedback.textContent=`Could not load the quotation: ${error.message}. Check the details and try again.`;}
  finally{button.disabled=authMode==='oidc'&&workspaceRole!=='analyst';}
});
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
async function initialize(){const main=document.querySelector('main');main.hidden=true;try{const config=await fetch('/auth/config');if(!config.ok)throw new Error('Authentication configuration unavailable');const auth=await config.json();authMode=auth.mode;intakeEnabled=auth.mode==='oidc'&&auth.intake_enabled===true;if(!['demo','oidc'].includes(authMode))throw new Error('Unknown authentication mode');if(authMode==='oidc'){const me=await fetch('/auth/me');if(me.status===403){$('signin').hidden=false;return;}if(!me.ok)throw new Error('Identity service unavailable');const identity=await me.json();workspaceRole=identity.role;if(intakeEnabled&&workspaceRole==='analyst')$('roleNotice').textContent='Upload a synthetic file below to retain its source for evidence-linked corrections. The test worker must be running.';if(workspaceRole!=='analyst'){$('roleNotice').textContent='An Analyst uploads and prepares quotations; a Reviewer records the final decision.';for(const id of ['loadSample','uploadBtn','intakeSubmit','intakePromote'])$(id).disabled=true;}$('logout').hidden=false;if(auth.intake_enabled===true)$('intakePanel').hidden=false;}else{$('footerNote').textContent+=' · Reviewer identities are not authenticated';}main.hidden=false;const response=await fetch('/api/quotations');const result=await response.json();if(!response.ok)throw new Error(result.error||'Storage unavailable');for(const row of result.quotations)records.set(row.id,row.quotation);$('count').textContent=records.size;if(records.size){selected=records.keys().next().value;renderItems();renderDetails();renderReview();}const note=$('storageMode');if(note)note.textContent=result.storage==='postgres'?'PostgreSQL development storage':'Local, in-memory decisions';}catch(error){$('signin').hidden=false;$('signinError').textContent=error.message;}}
$('logout').addEventListener('click',()=>task(async()=>{const response=await fetch('/auth/logout',{method:'POST',headers:{'X-NAWA-CSRF':csrfToken()}});if(!response.ok)throw new Error('Sign-out failed');window.location.reload();}));
initialize();


