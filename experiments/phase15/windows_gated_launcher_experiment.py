"""Synthetic Windows job experiment; not a production OCR launcher."""
import subprocess
import sys

# The starter executes only fixed code in isolated Python and waits for input.
# Child arguments are passed as arguments, not interpolated into this code.
STARTER = (
    'import subprocess,sys; '
    'gate=sys.stdin.readline(); '
    'sys.exit(subprocess.call(sys.argv[1:]) if gate == "go\\n" else 126)'
)

def start_gated(job, command):
    """Attach the waiting starter before signaling it to launch its child."""
    if not command:
        raise ValueError('A command is required')
    parent = subprocess.Popen([sys.executable, '-I', '-S', '-u', '-c', STARTER, *command],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        job.attach(parent)
        parent.stdin.write(b'go\n')
        parent.stdin.flush()
        parent.stdin.close()
        return parent
    except BaseException:
        parent.kill()
        parent.wait(timeout=5)
        parent.stdin.close()
        parent.stdout.close()
        raise
