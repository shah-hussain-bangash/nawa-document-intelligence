"""Experimental gated Windows process runner; not a sandbox or NAWA integration."""
import subprocess
import threading
import time
from windows_cleanup_job import WindowsCleanupJob
from windows_gated_launcher_experiment import start_gated

class GatedRunError(RuntimeError):
    pass

def run_gated_bounded(command, *, timeout=20, max_output=256 * 1024,
                      max_processes=4, memory_limit_bytes=512 * 1024 * 1024, cpu_percent=50):
    """Run trusted test commands in a cleanup job with time and output limits."""
    if timeout <= 0 or max_output <= 0:
        raise ValueError('Limits must be positive')
    deadline = time.monotonic() + timeout
    job = WindowsCleanupJob(max_processes=max_processes, memory_limit_bytes=memory_limit_bytes,
                            cpu_percent=cpu_percent)
    parent = None
    reader = None
    chunks = []
    state = {'size':0, 'overflow':False}
    try:
        parent = start_gated(job, command)
        def drain():
            while True:
                chunk = parent.stdout.read(8192)
                if not chunk:
                    return
                state['size'] += len(chunk)
                if state['size'] > max_output:
                    state['overflow'] = True
                    try:
                        parent.kill()
                    except ProcessLookupError:
                        pass
                    return
                chunks.append(chunk)
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            parent.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise GatedRunError('Process timed out') from exc
        if state['overflow']:
            raise GatedRunError('Process output exceeds limit')
        if parent.returncode:
            raise GatedRunError('Process failed')
    finally:
        # Closing the job stops the starter and its non-breakaway descendants.
        job.close()
        if parent is not None:
            if parent.poll() is None:
                parent.wait(timeout=5)
            if reader is not None:
                reader.join(timeout=5)
                if reader.is_alive():
                    raise GatedRunError('Output pipe did not close after job cleanup')
            parent.stdout.close()
    if state['overflow']:
        raise GatedRunError('Process output exceeds limit')
    return b''.join(chunks)
