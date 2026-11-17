"""Linux subprocess limits for the synthetic intake prototype, not a sandbox."""
import sys

MEMORY_BYTES = 512 * 1024 * 1024
CPU_SECONDS = 15
FILE_BYTES = 8 * 1024 * 1024


def apply_parser_limits():
    """Limit the current child process on Linux; Windows still uses timeouts only."""
    if not sys.platform.startswith('linux'):
        return False
    import resource
    for kind, maximum in ((resource.RLIMIT_AS, MEMORY_BYTES),
                          (resource.RLIMIT_CPU, CPU_SECONDS),
                          (resource.RLIMIT_FSIZE, FILE_BYTES)):
        soft, hard = resource.getrlimit(kind)
        # Never raise a limit imposed by the environment.
        new_hard = maximum if hard == resource.RLIM_INFINITY else min(hard, maximum)
        new_soft = new_hard if soft == resource.RLIM_INFINITY else min(soft, new_hard)
        resource.setrlimit(kind, (new_soft, new_hard))
    return True

