// Real browser UI check against synthetic stub endpoints, not Keycloak.
(async () => {
  const waitFor = async (predicate) => {
    for (let i=0;i<120;i++) {
      if (predicate()) return;
      await new Promise(resolve => setTimeout(resolve,50));
    }
    throw new Error('Timed out waiting for synthetic UI');
  };
  try {
    await waitFor(() => !document.querySelector('main').hidden && !document.getElementById('intakePanel').hidden);
    const upload = document.getElementById('intakeFiles');
    const transfer = new DataTransfer();
    transfer.items.add(new File(['synthetic quotation'], 'synthetic.txt', {type:'text/plain'}));
    upload.files = transfer.files;
    document.getElementById('intakeSubmit').click();
    await waitFor(() => document.getElementById('intakeResults').textContent.includes('demo-id'));
    document.getElementById('intakeRefresh').click();
    await waitFor(() => document.getElementById('intakeJobs').querySelector('button'));
    document.getElementById('intakeJobs').querySelector('button').click();
    if (document.getElementById('intakeId').value !== 'demo-id') throw new Error('Selection failed');
    document.getElementById('intakeCheck').click();
    await waitFor(() => document.getElementById('intakeStatus').textContent.includes('1050.00'));
    document.getElementById('intakePromote').click();
    await waitFor(() => document.getElementById('count').textContent === '1');
    document.body.setAttribute('data-synthetic-ui-check', 'PASS');
  } catch (error) {
    document.body.setAttribute('data-synthetic-ui-check', 'FAIL');
    document.body.setAttribute('data-synthetic-ui-error', String(error.message));
  }
})();

