"""Synthetic PostgreSQL locking check on a disposable local-only test cluster.

Requires Windows PostgreSQL 18 binaries. Creates a new cluster under a fresh
temporary directory, binds only 127.0.0.1, uses trust authentication for the
short test, and stops the server. Never target an existing data directory.
"""
from pathlib import Path
import socket
import os
import sys
import subprocess
import tempfile
import time

BIN = Path(r'C:\Program Files\PostgreSQL\18\bin')
SCHEMA = Path(__file__).with_name('phase13-postgres-schema-draft.sql')
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def run(args, **kwargs):
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True, creationflags=FLAGS, **kwargs)
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr)
        raise


def main():
    with tempfile.TemporaryDirectory(prefix='nawa-phase13-pg-') as tmp:
        cluster = Path(tmp) / 'cluster'
        run([str(BIN / 'initdb.exe'), '-D', str(cluster), '-U', 'nawa_test', '--auth=trust', '--no-locale', '--encoding=UTF8'])
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = str(sock.getsockname()[1])
        log = open(Path(tmp) / 'server.log', 'wb')
        proc = subprocess.Popen([str(BIN / 'postgres.exe'), '-D', str(cluster), '-h', '127.0.0.1', '-p', port],
                                stdout=log, stderr=subprocess.STDOUT, creationflags=FLAGS)
        base = [str(BIN / 'psql.exe'), '-X', '-qAt', '-h', '127.0.0.1', '-p', port,
                '-U', 'nawa_test', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1']
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError('Isolated PostgreSQL did not start')
                if subprocess.run([str(BIN / 'pg_isready.exe'), '-q', '-h', '127.0.0.1', '-p', port],
                                  capture_output=True, creationflags=FLAGS).returncode == 0:
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('Isolated PostgreSQL readiness timed out')
            identity_schema = SCHEMA.parent.parent / 'demo' / 'nawa_demo' / 'migrations' / '002_identity_foundation.sql'
            run(base + ['-c', 'CREATE TABLE nawa_quotations (id text PRIMARY KEY);',
                        '-f', str(identity_schema)])
            project = SCHEMA.parent.parent
            env = os.environ.copy()
            env['NAWA_PHASE13_TEST_DSN'] = f'host=127.0.0.1 port={port} dbname=postgres user=nawa_test'
            env['PYTHONPATH'] = os.pathsep.join((str(project / '.deps'), str(project / '.deps-pdf')))
            setup = ('import os,psycopg; from nawa_demo.intake_migrate import apply_intake_migrations; '
                     'conn=psycopg.connect(os.environ["NAWA_PHASE13_TEST_DSN"]); '
                     'apply_intake_migrations(conn); conn.commit(); conn.close()')
            run([sys.executable, '-c', setup], cwd=project / 'demo', env=env)
            run(base + ['-c', """INSERT INTO nawa_tenants VALUES ('a');
                INSERT INTO nawa_intake_documents(id,tenant_id,filename,sha256,size_bytes) VALUES
                ('00000000-0000-0000-0000-000000000001','a','one.txt',repeat('a',64),1),
                ('00000000-0000-0000-0000-000000000002','a','two.txt',repeat('b',64),1);
                INSERT INTO nawa_intake_jobs(id,tenant_id,document_id,state) VALUES
                ('10000000-0000-0000-0000-000000000001','a','00000000-0000-0000-0000-000000000001','received'),
                ('10000000-0000-0000-0000-000000000002','a','00000000-0000-0000-0000-000000000002','received');"""])
            claim = """WITH candidate AS (SELECT id FROM nawa_intake_jobs WHERE tenant_id='a' AND state='received'
                ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
                UPDATE nawa_intake_jobs j SET state='processing', attempts=attempts+1,
                claim_token_hash=repeat('c',64), lease_until=now()+interval '1 minute'
                FROM candidate WHERE j.id=candidate.id RETURNING j.id;"""
            # The advisory lock is taken after the first row is claimed, giving
            # the second session a deterministic signal that the row is locked.
            first = subprocess.Popen(base + ['-c', 'BEGIN; ' + claim +
                                      ' SELECT pg_advisory_xact_lock(387123); SELECT pg_sleep(3); COMMIT;'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=FLAGS)
            for _ in range(100):
                held = run(base + ['-c', "SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND objid=387123 AND granted;"]).stdout.strip()
                if held == '1':
                    break
                if first.poll() is not None:
                    raise RuntimeError('First worker exited before taking a lock')
                time.sleep(.05)
            else:
                raise RuntimeError('First worker lock did not appear')
            second = run(base + ['-c', 'BEGIN; ' + claim + ' COMMIT;']).stdout.strip()
            first_out, first_err = first.communicate(timeout=10)
            if first.returncode:
                raise RuntimeError('First worker failed: ' + first_err)
            first_id = first_out.strip().splitlines()[0]
            if not second or first_id == second:
                raise AssertionError('Workers did not obtain two different jobs')
            count = run(base + ['-c', "SELECT count(*) FROM nawa_intake_jobs WHERE state='processing' AND attempts=1;"]).stdout.strip()
            if count != '2':
                raise AssertionError('Expected exactly two claimed jobs')
            print('PASS: two concurrent PostgreSQL workers claimed different synthetic jobs')
            result = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                          '-p', 'test_intake_postgres.py', '-v'], cwd=project / 'demo', env=env)
            print(result.stderr.strip())
        finally:
            subprocess.run([str(BIN / 'pg_ctl.exe'), '-D', str(cluster), '-m', 'fast', '-w', 'stop'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=FLAGS)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            log.close()


if __name__ == '__main__':
    main()

