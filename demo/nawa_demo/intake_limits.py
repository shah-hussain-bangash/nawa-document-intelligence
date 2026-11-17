"""Subprocess limits for the synthetic intake prototype, not a sandbox."""
import sys

MEMORY_BYTES = 512 * 1024 * 1024
CPU_SECONDS = 15
FILE_BYTES = 8 * 1024 * 1024
_WINDOWS_JOB_HANDLE = None


def _apply_windows_memory_limit():
    """Place this parser process in a job with a per-process memory limit."""
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [('per_process_time', ctypes.c_int64), ('per_job_time', ctypes.c_int64),
                    ('flags', wintypes.DWORD), ('min_working_set', ctypes.c_size_t),
                    ('max_working_set', ctypes.c_size_t), ('active_processes', wintypes.DWORD),
                    ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                    ('scheduling_class', wintypes.DWORD)]

    class IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ('read_ops', 'write_ops', 'other_ops',
                                                          'read_bytes', 'write_bytes', 'other_bytes')]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [('basic', BasicLimits), ('io', IoCounters), ('process_memory', ctypes.c_size_t),
                    ('job_memory', ctypes.c_size_t), ('peak_process_memory', ctypes.c_size_t),
                    ('peak_job_memory', ctypes.c_size_t)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = ExtendedLimits()
    limits.basic.flags = 0x00000100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
    limits.process_memory = MEMORY_BYTES
    if (not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits))
            or not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess())):
        error = ctypes.get_last_error()
        kernel.CloseHandle(job)
        raise ctypes.WinError(error)
    # Keep the kernel handle open until the parser exits.
    global _WINDOWS_JOB_HANDLE
    _WINDOWS_JOB_HANDLE = job


def apply_parser_limits():
    """Limit this parser process on Linux or Windows; not a security sandbox."""
    if sys.platform == 'win32':
        _apply_windows_memory_limit()
        return True
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

