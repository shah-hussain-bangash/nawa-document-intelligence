"""Synthetic session-to-inspector routing experiment; no HTTP endpoint."""
import re
from .authorization import Principal
from .session_draft import SessionError, SessionStore

_JOB = re.compile(r'[0-9a-f]{32}\Z')

class SyntheticInspectorBroker:
    """Route using the server session tenant, never a client-chosen tenant."""
    def __init__(self, sessions, routes, inspector):
        if not isinstance(sessions, SessionStore) or not isinstance(routes, dict) or not callable(inspector):
            raise ValueError('Invalid synthetic broker configuration')
        self._sessions = sessions
        self._routes = {key:dict(value) if isinstance(value, dict) else value
                        for key, value in routes.items()}  # trusted server-side configuration only
        self._inspector = inspector

    def inspect(self, session_token, job_id):
        if not isinstance(job_id, str) or not _JOB.fullmatch(job_id):
            raise ValueError('Invalid synthetic job ID')
        try:
            principal = self._sessions.authorize_current(session_token, 'view')
            if not isinstance(principal, Principal) or principal.active is not True:
                raise SessionError('Session unavailable')
            route = self._routes.get(principal.tenant)
            if not isinstance(route, dict):
                raise SessionError('Session unavailable')
            ledger, app, schema = route['ledger_connect'], route['app_connect'], route['schema']
            if not callable(ledger) or not callable(app) or not isinstance(schema, str):
                raise SessionError('Session unavailable')
        except (SessionError, KeyError, TypeError) as exc:
            raise PermissionError('Synthetic inspection unavailable') from exc
        try:
            return self._inspector(ledger, app, schema=schema, job_id=job_id, tenant=principal.tenant)
        except Exception:
            raise RuntimeError('Synthetic inspection unavailable') from None
