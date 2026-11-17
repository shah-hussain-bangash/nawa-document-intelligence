'use strict';
// Small DOM simulation; this is not a real-browser or Keycloak sign-in test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function element() {
  return {
    hidden: true, textContent: '', className: '', value: '', files: [], children: [], events: {}, dataset: {},
    addEventListener(name, handler) { this.events[name] = handler; },
    append(...nodes) { this.children.push(...nodes); },
    replaceChildren(...nodes) { this.children = nodes; },
    setAttribute() {},
  };
}
const nodes = new Map();
const get = id => { if (!nodes.has(id)) nodes.set(id, element()); return nodes.get(id); };
const main = element();
const calls = [];
const document = {
  cookie: 'nawa_csrf=synthetic-csrf',
  getElementById: get,
  createElement: element,
  querySelector: selector => selector === 'main' ? main : null,
  querySelectorAll: () => [],
};
async function fetch(pathname, options = {}) {
  calls.push({pathname, options});
  let data;
  if (pathname === '/auth/config') data = {mode:'oidc', intake_enabled:true};
  else if (pathname === '/auth/me') data = {role:'analyst'};
  else if (pathname === '/api/quotations') data = {quotations:[], storage:'postgres'};
  else if (pathname === '/api/intake/batch') {
    const file = JSON.parse(options.body).files[0];
    data = file.filename === 'quota.txt' ? {files:[{error:'Synthetic document limit reached'}]} : {files:[{id:'abc123', created:true}]};
  }
  else if (pathname === '/api/intake/status?id=abc123') data = {state:'completed', attempts:1};
  else if (pathname === '/api/intake/result?id=abc123') data = {result:{supplier:'Synthetic supplier', total:'1050.00'}};
  else if (pathname === '/api/intake/version') data = {family_id:'synthetic-family', version:1};
  else if (pathname === '/api/intake/versions?family=synthetic-family') data = {versions:[{version:1,id:'abc123'}]};
  else if (pathname === '/api/intake/promote') data = {id:'quote1',created:true,quotation:{document:'synthetic.txt',supplier:'Synthetic',total:'1050.00',checks:{valid:true},evidence:{}}};
  else if (pathname === '/api/review/show') data = {status:'approved',revision:1,history:[]};
  else throw new Error('Unexpected request: ' + pathname);
  return {ok:true, status:200, json:async () => data};
}

async function mainTest() {
  const source = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');
  const context = {document, fetch, TextEncoder, Uint8Array, Map, Array, String, JSON,
                   btoa: value => Buffer.from(value, 'binary').toString('base64'),
                   window:{location:{reload(){}}}};
  vm.runInNewContext(source, context, {filename:'app.js'});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(main.hidden, false);
  assert.equal(get('intakePanel').hidden, false);
  get('intakeFiles').files = [{name:'synthetic.txt', size:4, arrayBuffer:async () => Uint8Array.from([116,101,115,116]).buffer}];
  await get('intakeSubmit').events.click();
  const submission = calls.find(x => x.pathname === '/api/intake/batch');
  assert.equal(submission.options.headers['X-NAWA-CSRF'], 'synthetic-csrf');
  assert.deepEqual(JSON.parse(submission.options.body).files, [{filename:'synthetic.txt', content_base64:'dGVzdA=='}]);
  assert.match(get('intakeResults').children[0].textContent, /abc123/);
  get('intakeFiles').files = [{name:'quota.txt', size:4, arrayBuffer:async () => Uint8Array.from([116,101,115,116]).buffer}];
  await get('intakeSubmit').events.click();
  assert.match(get('intakeResults').children[0].textContent, /limit reached/);
  assert.match(get('message').textContent, /0 of 1 files/);
  assert.equal(get('message').className, 'message error');
  get('intakeId').value = 'abc123';
  await get('intakeCheck').events.click();
  assert.match(get('intakeStatus').textContent, /completed.*1050\.00/);
  await get('intakePromote').events.click();
  assert.equal(get('count').textContent, 1);
  get('versionPrevious').value = '0';
  await get('versionLink').events.click();
  assert.equal(get('versionFamily').value, 'synthetic-family');
  await get('versionHistory').events.click();
  assert.match(get('versionResults').children[0].textContent, /Version 1.*abc123/);
  console.log('PASS: synthetic intake UI submits a batch and displays a completed result');
}

mainTest().catch(error => { console.error(error); process.exitCode = 1; });

