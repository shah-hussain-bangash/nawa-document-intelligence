"""Read-only bridge for disposable Phase 13 synthetic PostgreSQL test data.

Not exposed as an endpoint. Caller supplies an already authenticated
server-side Principal and a verified-store implementation. No deletion
policy or atomic check-to-use guarantee is provided.
"""
from nawa_demo.intake_scoped import ScopedIntake
from phase13_snapshot_fixture import fixture_snapshot


def load_snapshot(connect, store, principal):
    ScopedIntake._require(principal, 'view')
    with connect() as conn:
        ScopedIntake._recheck(conn, principal, 'view')
        rows = conn.execute('''SELECT d.id,v.family_id,v.version,d.filename,d.sha256,j.state,j.result
            FROM nawa_intake_documents d
            JOIN nawa_intake_jobs j ON j.tenant_id=d.tenant_id AND j.document_id=d.id
            JOIN nawa_intake_versions v ON v.tenant_id=d.tenant_id AND v.document_id=d.id
            WHERE d.tenant_id=%s ORDER BY v.family_id,v.version''', (principal.tenant,)).fetchall()
        items = [{'document_id':doc.hex, 'family_id':family.hex, 'version':version,
                  'tenant_id':principal.tenant, 'filename':filename, 'sha256':digest.strip(),
                  'job_state':state, 'result':result, 'source_verified':False}
                 for doc,family,version,filename,digest,state,result in rows]
        latest = {}
        for item in items:
            family = item['family_id']
            if family not in latest or item['version'] > latest[family]['version']:
                latest[family] = item
        for item in latest.values():
            if item['job_state'] == 'completed':
                store.read_verified(item['document_id'], item['sha256'])
                item['source_verified'] = True
        return fixture_snapshot(items, tenant=principal.tenant, principal=principal.subject,
                                membership_active=True)

