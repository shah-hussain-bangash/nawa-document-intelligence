"""Run synthetic intake jobs in an explicitly configured test environment."""
import argparse
import os
from pathlib import Path
import signal
import threading

from .intake_postgres import PostgresIntakeJobs
from .intake_store import LocalIntakeStore
from .intake_worker import process_one
from .intake_migrate import verify_intake_migrations


def run_loop(run_one, stop, interval):
    """Poll until asked to stop; transient failures never expose exception text."""
    while not stop.is_set():
        try:
            state = run_one()
            if state:
                print('Synthetic intake worker:', state, flush=True)
        except Exception:
            print('Synthetic intake worker temporarily unavailable.', flush=True)
        stop.wait(interval)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loop', action='store_true', help='poll for synthetic jobs until stopped')
    parser.add_argument('--interval', type=float, default=2)
    args = parser.parse_args(argv)
    if not 0.5 <= args.interval <= 30:
        raise ValueError('Polling interval must be between 0.5 and 30 seconds')
    if os.environ.get('NAWA_INTAKE') != 'synthetic' or os.environ.get('NAWA_AUTH') != 'oidc':
        raise ValueError('Worker requires explicitly enabled synthetic OIDC test mode')
    directory = os.environ.get('NAWA_INTAKE_DIR', '')
    tenant = os.environ.get('NAWA_TENANT_ID', '')
    if not Path(directory).is_absolute() or not tenant.strip():
        raise ValueError('Worker requires an absolute storage directory and test tenant')
    import psycopg
    def connect():
        return psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'],
                               user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                               port=os.environ.get('POSTGRES_PORT', '5432'),
                               connect_timeout=5)
    jobs = PostgresIntakeJobs(connect)
    store = LocalIntakeStore(directory)
    def run_one():
        with connect() as conn:
            verify_intake_migrations(conn)
        return process_one(jobs, store, tenant)
    if args.loop:
        stop = threading.Event()
        def request_stop(_signum, _frame):
            stop.set()
        signal.signal(signal.SIGTERM, request_stop)
        signal.signal(signal.SIGINT, request_stop)
        run_loop(run_one, stop, args.interval)
    else:
        state = run_one()
        print('Synthetic intake worker:', state or 'no job')


if __name__ == '__main__':
    main()

