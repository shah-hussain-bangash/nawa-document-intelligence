"""Run one synthetic intake job in an explicitly configured test environment."""
import os
from pathlib import Path

from .intake_postgres import PostgresIntakeJobs
from .intake_store import LocalIntakeStore
from .intake_worker import process_one


def main():
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
    state = process_one(PostgresIntakeJobs(connect), LocalIntakeStore(directory), tenant)
    print('Synthetic intake worker:', state or 'no job')


if __name__ == '__main__':
    main()
