'use strict';
// Browser exercise against a local in-memory API fixture, not an identity or persistence test.
const {chromium}=require('playwright');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');

const root=path.join(__dirname,'../web');
const evidence={supplier:{line:1,source_text:'Supplier: Test'},currency:{line:2,source_text:'Currency: AED'},
  subtotal:{line:3,source_text:'Subtotal: 1000.00'},vat_rate:{line:4,source_text:'VAT Rate: 5'},
  vat_amount:{line:5,source_text:'VAT Amount: 50.00'},total:{line:6,source_text:'Total: 1050.00'}};
const quotation={document:'synthetic.txt',supplier:'Test',currency:'AED',subtotal:'1000.00',vat_rate_percent:'5',
  vat_amount:'50.00',total:'1050.00',evidence,checks:{vat_matches_rate:true,total_matches_components:true}};
let rows=[],review=null,failSave=true,failReload=false,failStatus=true,failProcessing=true,expired=false,testRole='analyst';
const server=http.createServer(async(req,res)=>{
  const assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css'};
  if(assets[req.url]){res.setHeader('Content-Type',req.url.endsWith('.js')?'text/javascript':req.url.endsWith('.css')?'text/css':'text/html');res.end(fs.readFileSync(path.join(root,assets[req.url])));return;}
  let raw='';for await(const chunk of req)raw+=chunk;let data;
  if(req.url==='/auth/config')data={mode:'oidc',intake_enabled:true};
  else if(req.url==='/auth/me'){if(expired){res.statusCode=403;data={error:'Session unavailable'};}else data={role:testRole};}
  else if(req.url==='/api/quotations')data={quotations:rows,storage:'postgres'};
  else if(req.url==='/api/intake/batch'){if(expired){res.statusCode=403;data={error:'Session unavailable'};}else data={files:[{id:'synthetic-document',created:true}]};}
  else if(req.url==='/api/intake/status?id=synthetic-document'){if(failStatus){failStatus=false;res.statusCode=503;data={error:'Status unavailable'};}else data={state:failProcessing?'failed':'completed',attempts:1};}
  else if(req.url==='/api/intake/retry'){failProcessing=false;data={state:'validated'};}
  else if(req.url==='/api/intake/promote'){rows=[{id:'q1',quotation}];data={...rows[0],created:true};}
  else if(req.url==='/api/review/show'){if(failReload){failReload=false;res.statusCode=503;data={error:'Storage unavailable'};}else if(!review){res.statusCode=400;data={error:'Review is not initialized'};}else data=review;}
  else if(req.url==='/api/review/start'){
    review={document:'synthetic.txt',status:'pending_review',revision:1,fields:{supplier:'Test',currency:'AED',subtotal:'1000.00',vat_rate_percent:'5',vat_amount:'50.00',total:'1050.00'},checks:{vat_matches_rate:true,total_matches_components:true},history:[],corrections:[]};data=review;
  }else if(req.url==='/api/review/correct'){
    if(expired){res.statusCode=403;data={error:'Session unavailable'};}
    else if(failSave){failSave=false;res.statusCode=503;data={error:'Storage unavailable'};}
    else{const p=JSON.parse(raw);assert.equal(p.expected_revision,2);review.corrections.push({sequence:3,field:p.field,from:review.fields[p.field],to:p.value,reason:p.reason,evidence:{source:p.source,line:p.line,quote:p.quote}});review.fields[p.field]=p.value;review.checks.total_matches_components=false;review.revision=3;data=review;}
  }else if(req.url==='/api/review/decide'){res.statusCode=403;data={error:'Request denied'};}
  else{res.statusCode=404;data={error:'Unknown test endpoint'};}
  res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));
});

(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,executablePath:process.env.NAWA_CHROMIUM});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:900}});
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await page.locator('#upload').setInputFiles({name:'synthetic.txt',mimeType:'text/plain',buffer:Buffer.from('synthetic')});
    await page.getByRole('button',{name:'Add selected file'}).click();
    await page.getByText(/Could not confirm processing.*Check processing/i).waitFor();
    await page.getByRole('button',{name:'Check processing'}).click();
    await page.getByText(/Processing failed.*reason and retry/i).waitFor();
    await page.getByRole('button',{name:'Retry processing'}).click();
    await page.getByText('Enter a reason for the retry.').waitFor();
    await page.getByLabel('Reason for retry').fill('Retry synthetic processing');
    await page.getByRole('button',{name:'Retry processing'}).click();
    await page.getByText(/Retry requested.*Check processing/i).waitFor();
    await page.getByRole('button',{name:'Check processing'}).click();
    await page.getByRole('button',{name:'Start review'}).click();
    await page.getByLabel('Field to correct').selectOption('total');
    await page.getByLabel('Corrected value').fill('1049.00');
    await page.getByLabel('Reason for correction').fill('Source checked <img src=x onerror=alert(1)>');
    await page.getByLabel('Original source line').fill('6');
    await page.getByLabel('Exact source excerpt').fill('Total: 1050.00');
    await page.getByRole('button',{name:'Save correction'}).click();
    await page.getByText(/Could not save.*try again/i).waitFor();
    assert.equal(await page.getByLabel('Corrected value').inputValue(),'1049.00');
    review.revision=2;
    failReload=true;
    await page.getByRole('button',{name:'Reload saved review'}).click();
    await page.getByText('Your entries below were not confirmed as saved.').waitFor();
    await page.getByText('value: 1049.00',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Retry opening review'}).click();
    await page.getByText('Status: pending_review · revision 2').waitFor();
    assert.equal(await page.getByLabel('Corrected value').inputValue(),'1049.00');
    assert.equal(await page.getByLabel('Reason for correction').inputValue(),'Source checked <img src=x onerror=alert(1)>');
    await page.getByRole('button',{name:'Save correction'}).click();
    await page.getByText('Status: pending_review · revision 3').waitFor();
    assert.match(await page.locator('#details').innerText(),/1049\.00[\s\S]*Originally extracted: 1050\.00/);
    await page.getByRole('button',{name:'Reopen saved review'}).click();
    await page.getByText('Saved review reopened from the server at revision 3.').waitFor();
    await page.reload();
    await page.getByText('Status: pending_review · revision 3').waitFor();
    assert.match(await page.locator('#details').innerText(),/1049\.00[\s\S]*Original source/);
    await page.getByText('Cited excerpt: Total: 1050.00',{exact:true}).waitFor();
    assert.equal(await page.locator('.correction-evidence img').count(),0);
    assert.equal(await page.getByRole('button',{name:'Approve',exact:true}).count(),0);
    if(process.env.NAWA_UI_SCREENSHOT)await page.screenshot({path:process.env.NAWA_UI_SCREENSHOT,fullPage:true});
    testRole='reviewer';await page.reload();
    await page.getByText('Status: pending_review · revision 3').waitFor();
    assert.equal(await page.getByRole('button',{name:'Save correction'}).count(),0);
    assert.equal(await page.getByRole('button',{name:'Approve',exact:true}).count(),1);
    await page.getByText('Cited excerpt: Total: 1050.00',{exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Add selected file'}).isDisabled(),true);
    await page.getByPlaceholder('Explain your decision').fill('Synthetic decision');
    await page.getByRole('button',{name:'Approve',exact:true}).click();
    await page.getByText(/Decision denied.*another authorized Reviewer/i).waitFor();
    testRole='analyst';await page.reload();
    await page.getByText('Status: pending_review · revision 3').waitFor();
    await page.getByLabel('Field to correct').selectOption('total');
    await page.getByLabel('Corrected value').fill('1048.00');
    await page.getByLabel('Reason for correction').fill('Second unsaved change');
    expired=true;await page.getByRole('button',{name:'Save correction'}).click();
    await page.getByText(/session has ended.*Copy your unsaved entries/i).waitFor();
    assert.equal(await page.getByLabel('Corrected value').inputValue(),'1048.00');
    assert.equal(await page.getByRole('link',{name:'Sign in again'}).getAttribute('href'),'/auth/login');
    expired=false;
    failSave=true;await page.getByRole('button',{name:'Save correction'}).click();
    await page.getByText(/Could not save.*try again/i).waitFor();
    review.status='approved';review.revision=4;
    await page.getByRole('button',{name:'Reload saved review'}).click();
    await page.getByText('This review is final. Your input could not be confirmed as saved.').waitFor();
    await page.getByText('value: 1048.00',{exact:true}).waitFor();
    expired=true;
    await page.locator('#upload').setInputFiles({name:'synthetic.txt',mimeType:'text/plain',buffer:Buffer.from('synthetic')});
    await page.getByRole('button',{name:'Add selected file'}).click();
    await page.getByText(/session has ended.*select the file again/i).waitFor();
    assert.equal(await page.getByRole('link',{name:'Sign in again'}).getAttribute('href'),'/auth/login');
    console.log('PASS: browser upload, retry, correction and reopen against in-memory mock API');
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
