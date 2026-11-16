"""Development-only session primitives; not connected to dashboard endpoints.

Sessions are process-local and disappear on restart. Not suitable for a
multi-worker or production deployment. The membership lookup must obtain its
answer from trusted server-side records, never from browser-supplied roles.
"""
from __future__ import annotations

import hashlib
import math
import secrets
import threading
import time
from .authorization import Principal, PERMISSIONS, authorized

WRITE_ACTIONS = frozenset({'load', 'review_start', 'correct', 'decide'})


def _hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class SessionError(ValueError):
    pass


class SessionStore:
    def __init__(self, membership_lookup, *, ttl=300, limit=256, clock=time.monotonic):
        if (not callable(membership_lookup) or type(ttl) not in (int, float)
                or not math.isfinite(ttl) or ttl <= 0 or ttl > 300 or limit <= 0):
            raise ValueError('Invalid session configuration')
        self.lookup, self.ttl, self.limit, self.clock = membership_lookup, ttl, limit, clock
        self._sessions = {}
        self._lock = threading.Lock()

    def _membership(self, subject, tenant):
        principal = self.lookup(subject, tenant)
        if (not isinstance(principal, Principal) or principal.active is not True
                or principal.subject != subject or principal.tenant != tenant
                or not isinstance(principal.role, str) or principal.role not in PERMISSIONS):
            raise SessionError('Session unavailable')
        return principal

    def issue(self, subject, tenant, *, max_age=None):
        if not all(isinstance(x, str) and x.strip() for x in (subject, tenant)):
            raise SessionError('Session unavailable')
        if max_age is not None and (type(max_age) not in (int, float) or not math.isfinite(max_age) or max_age < 1):
            raise SessionError('Session unavailable')
        duration = int(min(self.ttl, max_age if max_age is not None else self.ttl))
        if duration < 1:
            raise SessionError('Session unavailable')
        self._membership(subject, tenant)
        with self._lock:
            now = self.clock()
            self._sessions = {key: value for key, value in self._sessions.items() if value['expires'] > now}
            if len(self._sessions) >= self.limit:
                raise SessionError('Session unavailable')
            session = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            self._sessions[_hash(session)] = {'subject': subject, 'tenant': tenant,
                                               'csrf_hash': _hash(csrf), 'expires': now + duration}
            return {'session': session, 'csrf': csrf, 'max_age': duration}

    def authorize(self, session, action, *, tenant, csrf=None):
        if not isinstance(session, str) or not session or not isinstance(action, str):
            raise SessionError('Session unavailable')
        with self._lock:
            key = _hash(session)
            record = self._sessions.get(key)
            if not record or record['expires'] <= self.clock():
                self._sessions.pop(key, None)
                raise SessionError('Session unavailable')
            if action in WRITE_ACTIONS:
                if not isinstance(csrf, str) or not csrf:
                    raise SessionError('Request denied')
                if not secrets.compare_digest(record['csrf_hash'], _hash(csrf)):
                    raise SessionError('Request denied')
            principal = self._membership(record['subject'], record['tenant'])
            if not authorized(principal, action, tenant=tenant):
                raise SessionError('Request denied')
            return principal

    def revoke(self, session):
        if not isinstance(session, str) or not session:
            return
        with self._lock:
            self._sessions.pop(_hash(session), None)

    def logout(self, session, csrf):
        if not isinstance(session, str) or not session or not isinstance(csrf, str) or not csrf:
            raise SessionError('Request denied')
        with self._lock:
            key = _hash(session)
            record = self._sessions.get(key)
            if (not record or record['expires'] <= self.clock()
                    or not secrets.compare_digest(record['csrf_hash'], _hash(csrf))):
                raise SessionError('Request denied')
            self._sessions.pop(key, None)

    def authorize_current(self, session, action, *, csrf=None):
        """Use the tenant bound to the server-side session, not client input."""
        if not isinstance(session, str) or not session:
            raise SessionError('Session unavailable')
        with self._lock:
            record = self._sessions.get(_hash(session))
            if not record:
                raise SessionError('Session unavailable')
            tenant = record['tenant']
        return self.authorize(session, action, tenant=tenant, csrf=csrf)
