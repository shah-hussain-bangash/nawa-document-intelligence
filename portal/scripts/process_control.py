"""Local project lifecycle controls. Never kill a process by image name alone."""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import json
import ntpath
import os
from pathlib import Path
import subprocess
import time


def windows_path(value):
    return ntpath.normcase(ntpath.normpath(str(value)))


def is_project_process(record, root):
    """Require an exact project executable or Vite entry point, not a text substring."""
    exe = windows_path(record.get('ExecutablePath') or '')
    argv = record.get('argv', [])
    web = ntpath.join(str(root), 'apps', 'web', 'node_modules')
    if ntpath.basename(exe) == 'esbuild.exe':
        return exe.startswith(windows_path(ntpath.join(web, '@esbuild')) + '\\')
    if ntpath.basename(exe) == 'node.exe':
        allowed = {windows_path(ntpath.join(web, 'vite', 'bin', 'vite.js')),
                   windows_path(ntpath.join(web, '.bin', 'vite'))}
        return len(argv) > 1 and windows_path(argv[1]) in allowed
    python = windows_path(ntpath.join(str(root), '.venv', 'Scripts', 'python.exe'))
    return exe == python and (argv[1:4] == ['-m', 'uvicorn', 'uae_ai.main:app'] or argv[1:] == ['-m', 'uae_ai.worker'])


def split_windows_argv(command):
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel.LocalFree.restype = wintypes.HLOCAL
    count = ctypes.c_int()
    pointer = shell.CommandLineToArgvW(command, ctypes.byref(count))
    if not pointer:
        return []
    try:
        return [pointer[i] for i in range(count.value)]
    finally:
        kernel.LocalFree(ctypes.cast(pointer, wintypes.HLOCAL))


def windows_inventory():
    # Fixed script: project paths/config/credentials are never interpolated into PowerShell.
    script = '''[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); $ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='esbuild.exe' OR Name='python.exe'" | ForEach-Object { [pscustomobject]@{ProcessId=$_.ProcessId; ExecutablePath=$_.ExecutablePath; CommandLine=$_.CommandLine; Started=$_.CreationDate.ToUniversalTime().ToFileTimeUtc()} }) | ConvertTo-Json -Compress'''
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25)
    if result.returncode:
        raise RuntimeError('Could not inspect Windows project processes. Close the terminals running this project and retry; no processes were killed.')
    rows = json.loads(result.stdout or '[]')
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows:
        row['argv'] = split_windows_argv(row.get('CommandLine') or '')
    return rows


def kernel32():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    return kernel


def terminate_verified(record):
    """Revalidate creation time + executable on a held handle to avoid PID reuse."""
    kernel = kernel32()
    handle = kernel.OpenProcess(0x1000 | 0x0001 | 0x100000, False, int(record['ProcessId']))
    if not handle:
        # Already exited is harmless; access denial must remain visible.
        if ctypes.get_last_error() in {87, 1168}:
            return
        raise RuntimeError('Windows refused access to a project process. Close its terminal and retry.')
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            raise RuntimeError('Could not verify project process start time; no termination attempted.')
        started = times[0].dwLowDateTime | times[0].dwHighDateTime << 32
        # WMI timestamps have microsecond precision; FILETIME has 100ns precision.
        if abs(started - int(record['Started'])) > 10:
            return
        buffer = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(buffer))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)) or windows_path(buffer.value) != windows_path(record['ExecutablePath']):
            return
        if not kernel.TerminateProcess(handle, 1):
            if kernel.WaitForSingleObject(handle, 0) != 0:
                raise RuntimeError('A project process could not be stopped; close its terminal and retry.')
        kernel.WaitForSingleObject(handle, 5000)
    finally:
        kernel.CloseHandle(handle)


def stop_windows_project(root):
    if os.name != 'nt':
        print('On this platform stop the project launcher with Ctrl+C; no unrelated process was stopped.')
        return
    count = 0
    # Re-scan to catch an esbuild child that appeared while its Vite parent exited.
    for _ in range(3):
        selected = [r for r in windows_inventory() if is_project_process(r, root)]
        if not selected:
            break
        for row in selected:
            terminate_verified(row)
            count += 1
        time.sleep(.2)
    print(f'Project stop completed ({count} matched process records). Other Node/Cursor projects were not targeted.')


def check_windows_native_files(root):
    if os.name != 'nt':
        return
    kernel = kernel32()
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    node = root / 'apps/web/node_modules'
    paths = list(node.glob('@esbuild/*/esbuild.exe')) + list(node.glob('@rollup/*/*.node'))
    for path in paths:
        # Request delete access without deleting/renaming; npm ci needs this access.
        handle = kernel.CreateFileW(str(path.resolve()), 0x10000, 7, None, 3, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            raise RuntimeError(f'Windows cannot replace {path.name} (file lock or permissions). Run python nawa.py stop, then setup --stop-running. If still blocked, close the app holding this file or use the new source in a fresh folder. No restart or data deletion is required by this tool.')
        kernel.CloseHandle(handle)


@contextmanager
def project_lock(root, timeout=0):
    path = root / '.data/runtime/operation.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0, 2)
        if not stream.tell():
            stream.write(b'0'); stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            stream.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('This project is already running or installing. Stop its launcher first, or use setup --stop-running on Windows. No installation files were changed.') from None
                time.sleep(.1)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def frontend_signature(root):
    digest = hashlib.sha256()
    for name in ['package.json', 'package-lock.json']:
        digest.update((root / 'apps/web' / name).read_bytes())
    return digest.hexdigest()


def mark_frontend_ready(root):
    path = root / '.data/runtime/frontend-ready.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'signature': frontend_signature(root)}), encoding='utf-8')
    temporary.replace(path)


def require_frontend_ready(root):
    try:
        marker = json.loads((root / '.data/runtime/frontend-ready.json').read_text(encoding='utf-8'))
        valid = marker.get('signature') == frontend_signature(root)
    except (OSError, ValueError):
        valid = False
    if not valid or not (root / 'apps/web/node_modules/vite/bin/vite.js').is_file():
        raise RuntimeError('Frontend setup is incomplete or its lockfile changed. Run python nawa.py setup --stop-running and wait for SETUP COMPLETE before starting.')


class WindowsJob:
    """Kill launcher-owned children when its job handle closes (including crashes)."""
    def __init__(self):
        self.handle = None
        if os.name != 'nt':
            return
        class Basic(ctypes.Structure):
            _fields_ = [('ProcessTime', ctypes.c_longlong), ('JobTime', ctypes.c_longlong),
                        ('Flags', wintypes.DWORD), ('MinWorking', ctypes.c_size_t),
                        ('MaxWorking', ctypes.c_size_t), ('ActiveLimit', wintypes.DWORD),
                        ('Affinity', ctypes.c_size_t), ('Priority', wintypes.DWORD),
                        ('Scheduling', wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ['ReadOps', 'WriteOps', 'OtherOps', 'ReadBytes', 'WriteBytes', 'OtherBytes']]
        class Extended(ctypes.Structure):
            _fields_ = [('Basic', Basic), ('IO', IO), ('ProcessMemory', ctypes.c_size_t),
                        ('JobMemory', ctypes.c_size_t), ('PeakProcess', ctypes.c_size_t),
                        ('PeakJob', ctypes.c_size_t)]
        self.kernel = kernel32()
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise RuntimeError('Windows could not create a project process job. No services were started.')
        limits = Extended()
        limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise RuntimeError('Windows could not enable project process cleanup. No services were started.')

    def attach(self, process):
        if self.handle and not self.kernel.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))):
            raise RuntimeError('Windows could not attach a child to the project cleanup job. Startup was cancelled.')

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
