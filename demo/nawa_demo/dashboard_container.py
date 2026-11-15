"""Container-only entrypoint for the Phase 9 synthetic dashboard.

The existing dashboard CLI stays bound to 127.0.0.1 for Mac/local use.
This container process binds 0.0.0.0 *inside its isolated container* so
Docker can publish 127.0.0.1:8765 on the host. Never publish to a LAN IP.
"""
from http.server import HTTPServer
from .dashboard import DashboardState, make_handler


def serve():
    state = DashboardState()
    with HTTPServer(('0.0.0.0', 8765), make_handler(state)) as server:
        print('NAWA synthetic Docker dashboard: http://127.0.0.1:8765', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    serve()
