"""Read-only bridge for disposable Phase 13 synthetic PostgreSQL test data.

Not exposed as an endpoint. Caller supplies an already authenticated
server-side Principal and a verified-store implementation. The lifecycle
table is a disposable QA experiment, not a production deletion policy.
"""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from nawa_demo.intake_scoped import ScopedIntake
from phase13_snapshot_fixture import fixture_snapshot


def verify_extracted_evidence(content, stored_result):
    """Re-extract synthetic PDF evidence in the existing bounded parser."""
    if not isinstance(stored_result, dict) or not isinstance(stored_result.get('evidence'), dict):
        raise ValueError('Synthetic evidence unavailable')
    with TemporaryDirectory(prefix='nawa14-citation-') as directory:
        source = Path(directory) / 'source.pdf'
        output = Path(directory) / 'result.json'
        source.write_bytes(content)
        try:
            with output.open('wb') as stream:
                subprocess.run([sys.executable, '-m', 'nawa_demo.intake_parser', str(source)],
                               stdout=stream, stderr=subprocess.DEVNULL, check=True, timeout=20)
            with output.open('rb') as stream:
                encoded = stream.read(2 * 1024 * 1024 + 1)
            if len(encoded) > 2 * 1024 * 1024:
                raise ValueError('Synthetic parser output too large')
            parsed = json.loads(encoded.decode('utf-8'))
        except (subprocess.SubprocessError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Synthetic evidence verification failed') from exc
    if not isinstance(parsed, dict) or parsed.get('evidence') != stored_result['evidence']:
        raise ValueError('Synthetic evidence differs from verified PDF')


def load_snapshot(connect, store, principal):
    ScopedIntake._require(principal, 'view')
    with connect() as conn:
        ScopedIntake._recheck(conn, principal, 'view')
        rows = conn.execute('''SELECT d.id,v.family_id,v.version,d.filename,d.sha256,j.state,j.result,l.state
            FROM nawa_intake_documents d
            JOIN nawa_intake_jobs j ON j.tenant_id=d.tenant_id AND j.document_id=d.id
            JOIN nawa_intake_versions v ON v.tenant_id=d.tenant_id AND v.document_id=d.id
            LEFT JOIN nawa_phase14_qa_lifecycle l ON l.tenant_id=d.tenant_id AND l.document_id=d.id
            WHERE d.tenant_id=%s ORDER BY v.family_id,v.version''', (principal.tenant,)).fetchall()
        items = [{'document_id':doc.hex, 'family_id':family.hex, 'version':version,
                  'tenant_id':principal.tenant, 'filename':filename, 'sha256':digest.strip(),
                  'job_state':state if lifecycle == 'active' else 'unavailable',
                  'lifecycle_state':lifecycle, 'result':result, 'source_verified':False}
                 for doc,family,version,filename,digest,state,result,lifecycle in rows]
        if any(item['lifecycle_state'] not in ('active','withdrawn','deleted') for item in items):
            raise ValueError('Missing synthetic lifecycle state')
        latest = {}
        for item in items:
            family = item['family_id']
            if family not in latest or item['version'] > latest[family]['version']:
                latest[family] = item
        for item in latest.values():
            if item['job_state'] == 'completed':
                content = store.read_verified(item['document_id'], item['sha256'])
                if not item['filename'].lower().endswith('.pdf'):
                    raise ValueError('Synthetic PDF required')
                verify_extracted_evidence(content, item['result'])
                item['source_verified'] = True
        return fixture_snapshot(items, tenant=principal.tenant, principal=principal.subject,
                                membership_active=True)

