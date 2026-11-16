"""Container-only entrypoint for the Phase 9 synthetic dashboard.

The existing dashboard CLI stays bound to 127.0.0.1 for Mac/local use.
This container process binds 0.0.0.0 *inside its isolated container* so
Docker can publish 127.0.0.1:8765 on the host. Never publish to a LAN IP.
"""
from http.server import HTTPServer
import os
from .dashboard import DashboardState, make_handler


def serve():
    mode = os.environ.get('NAWA_STORAGE', 'memory')
    if mode == 'memory':
        state = DashboardState()
    elif mode == 'postgres':
        import psycopg
        from .postgres_state import PostgresState
        def connect():
            return psycopg.connect(host=os.environ['POSTGRES_HOST'],
                                   dbname=os.environ['POSTGRES_DB'],
                                   user=os.environ['POSTGRES_USER'],
                                   password=os.environ['POSTGRES_PASSWORD'],
                                   connect_timeout=5)
        state = PostgresState(connect)
        state.storage_mode = 'postgres'
    else:
        raise ValueError('NAWA_STORAGE must be memory or postgres')
    with HTTPServer(('0.0.0.0', 8765), make_handler(state)) as server:
        print('NAWA synthetic Docker dashboard: http://127.0.0.1:8765', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    serve()
