"""Experimental Windows job cleanup for disposable synthetic processes.

Not a sandbox; use only with the gated experimental starter and trusted code.
"""
import ctypes
import os
from ctypes import wintypes

class _BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                ('flags', wintypes.DWORD), ('min_working', ctypes.c_size_t),
                ('max_working', ctypes.c_size_t), ('active_limit', wintypes.DWORD),
                ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                ('scheduling', wintypes.DWORD)]

class _IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]

class _ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', _BasicLimits), ('io', _IOCounters),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]

class WindowsCleanupJob:
    def __init__(self, *, max_processes=4, memory_limit_bytes=512 * 1024 * 1024):
        if os.name != 'nt':
            raise OSError('Windows job cleanup requires Windows')
        if not isinstance(max_processes, int) or isinstance(max_processes, bool) or not 1 <= max_processes <= 32:
            raise ValueError('Invalid job process limit')
        if not isinstance(memory_limit_bytes, int) or isinstance(memory_limit_bytes, bool) or not 32 * 1024 * 1024 <= memory_limit_bytes <= 4 * 1024 * 1024 * 1024:
            raise ValueError('Invalid job memory limit')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                        ctypes.c_void_p, wintypes.DWORD]
        self.kernel.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), 'Cannot create Windows job')
        limits = _ExtendedLimits()
        # KILL_ON_JOB_CLOSE | ACTIVE_PROCESS | JOB_MEMORY
        limits.basic.flags = 0x2000 | 0x8 | 0x200
        limits.basic.active_limit = max_processes
        limits.job_memory = memory_limit_bytes
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.get_last_error()
            self.close()
            raise OSError(error, 'Cannot configure Windows job cleanup')

    def attach(self, process):
        if not self.handle:
            raise RuntimeError('Windows job is closed')
        if not self.kernel.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))):
            raise OSError(ctypes.get_last_error(), 'Cannot assign process to Windows job')

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
