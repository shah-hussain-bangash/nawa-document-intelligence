"""Read-only check for a separate synthetic restore, not a recovery service."""
import re

_RESTORE_DB = re.compile(r'nawa_phase13_qa_restore_[0-9a-f]{12}\Z')


def verify_no_active_synthetic_grants(connect):
    """Return true only when a disposable restore currently has no active grants.

    This does not stop writers, validate sessions or reconstruct revocations.
    Callers must coordinate and keep all traffic and workers paused separately.
    """
    if not callable(connect):
        return False
    try:
        with connect() as conn:
            if conn.autocommit is not False or conn.info.host != '127.0.0.1':
                return False
            conn.execute('SET TRANSACTION READ ONLY')
            row = conn.execute('SELECT current_database()').fetchone()
            if (not row or not isinstance(row[0], str) or not _RESTORE_DB.fullmatch(row[0])):
                return False
            visibility = conn.execute(
                "SELECT has_table_privilege(current_user, 'public.nawa_synthetic_document_grants', 'SELECT'), "
                "row_security_active('public.nawa_synthetic_document_grants'), "
                "(SELECT relkind::text FROM pg_class WHERE oid = 'public.nawa_synthetic_document_grants'::regclass)"
            ).fetchone()
            if (not isinstance(visibility, tuple) or len(visibility) != 3
                    or visibility[0] is not True or visibility[1] is not False or visibility[2] != 'r'):
                return False
            active = conn.execute('SELECT EXISTS (SELECT 1 FROM public.nawa_synthetic_document_grants WHERE active)').fetchone()
            return isinstance(active, tuple) and len(active) == 1 and active[0] is False
    except Exception:
        return False
