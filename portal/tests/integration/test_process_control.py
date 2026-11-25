import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from scripts import process_control as pc
from scripts import devtools

ROOT = r'C:\Workspace\شركة\nawa-workspace'


def record(exe, argv):
    return {'ExecutablePath': exe, 'argv': argv, 'ProcessId': 123, 'Started': 100000000}


@pytest.mark.parametrize('row,expected', [
    (record(r'C:\Program Files\nodejs\node.exe', ['node', ROOT+r'\apps\web\node_modules\vite\bin\vite.js']), True),
    (record(r'C:\Program Files\nodejs\NODE.EXE', ['node', ROOT.replace('\\','/')+'/apps/web/node_modules/vite/bin/vite.js']), True),
    (record(ROOT+r'\apps\web\node_modules\@esbuild\win32-x64\esbuild.exe', ['esbuild']), True),
    (record(ROOT+r'\apps\web\node_modules\@esbuild\win32-arm64\esbuild.exe', ['esbuild']), True),
    (record(ROOT+r'\.venv\Scripts\python.exe', ['python','-m','uvicorn','uae_ai.main:app']), True),
    (record(ROOT+r'\.venv\Scripts\python.exe', ['python','-m','uae_ai.worker']), True),
    (record(r'C:\Other\.venv\Scripts\python.exe', ['python','-m','uae_ai.worker']), False),
    (record(r'C:\node.exe', ['node', r'C:\other\vite.js', '--config', ROOT]), False),
    (record(r'C:\node.exe', ['node', ROOT+'-other'+r'\apps\web\node_modules\vite\bin\vite.js']), False),
    (record(r'C:\node.exe', ['node', 'node_modules/vite/bin/vite.js']), False),
    (record(r'C:\other\@esbuild\win32-x64\esbuild.exe', ['esbuild']), False),
    (record(ROOT+r'\.venv\Scripts\python.exe', ['python','-m','alembic','upgrade','head']), False),
    (record(r'C:\Python312\python.exe', ['python','-m','uvicorn','uae_ai.main:app']), False),
    (record('', []), False),
])
def test_only_proven_project_processes_are_selected(row, expected):
    assert pc.is_project_process(row, ROOT) is expected


def test_handle_creation_time_prevents_pid_reuse(monkeypatch):
    calls=[]
    class Kernel:
        def OpenProcess(self,*a): return 42
        def CloseHandle(self,h): calls.append('close')
        def GetProcessTimes(self,h,created,*rest):
            created._obj.dwLowDateTime=100000001
            created._obj.dwHighDateTime=0
            return 1
        def QueryFullProcessImageNameW(self,h,flag,buffer,length):
            buffer.value=r'C:\node.exe'
            return 1
        def TerminateProcess(self,*a): calls.append('kill'); return 1
        def WaitForSingleObject(self,*a): return 0
    monkeypatch.setattr(pc,'kernel32',lambda:Kernel())
    pc.terminate_verified(record(r'C:\node.exe',[]))
    assert calls==['kill','close']
    calls.clear()
    wrong=record(r'C:\node.exe',[]);wrong['Started']=1
    pc.terminate_verified(wrong)
    assert calls==['close']
    calls.clear()
    pc.terminate_verified(record(r'C:\other\node.exe',[]))
    assert calls==['close']


def test_stop_does_not_target_other_project_processes(monkeypatch):
    ours=record(r'C:\node.exe',['node',ROOT+r'\apps\web\node_modules\vite\bin\vite.js'])
    other=record(r'C:\node.exe',['node',r'C:\other\vite.js'])
    snapshots=iter([[ours,other],[other]])
    monkeypatch.setattr(pc,'os',SimpleNamespace(name='nt'))
    monkeypatch.setattr(pc,'windows_inventory',lambda:next(snapshots))
    monkeypatch.setattr(pc.time,'sleep',lambda _:None)
    stopped=[];monkeypatch.setattr(pc,'terminate_verified',lambda row:stopped.append(row))
    pc.stop_windows_project(ROOT)
    assert stopped==[ours]


def test_operation_lock_blocks_parallel_setup_and_run_and_recovers(tmp_path):
    with pc.project_lock(tmp_path):
        with pytest.raises(RuntimeError, match='already running or installing'):
            with pc.project_lock(tmp_path):
                pytest.fail('Second operation must not acquire lock')
    with pc.project_lock(tmp_path):
        pass  # Stale file is harmless: OS lock is released on process exit.


def frontend(tmp_path):
    web=tmp_path/'apps/web';web.mkdir(parents=True)
    (web/'package.json').write_text('{"version":"0.4.2"}')
    (web/'package-lock.json').write_text('{"version":"0.4.2"}')
    (web/'node_modules/vite/bin').mkdir(parents=True)
    (web/'node_modules/vite/bin/vite.js').write_text('// test fixture')
    (web/'node_modules/.package-lock.json').write_text('{}')


def test_old_hidden_npm_lock_does_not_prove_install_succeeded(tmp_path):
    frontend(tmp_path)
    with pytest.raises(RuntimeError, match='incomplete'):
        pc.require_frontend_ready(tmp_path)
    pc.mark_frontend_ready(tmp_path)
    pc.require_frontend_ready(tmp_path)
    (tmp_path/'apps/web/package-lock.json').write_text('{"changed":true}')
    with pytest.raises(RuntimeError, match='lockfile changed'):
        pc.require_frontend_ready(tmp_path)


def test_setup_preflight_happens_before_install_and_keeps_data(tmp_path, monkeypatch):
    frontend(tmp_path)
    (tmp_path/'.env').write_text('APP_ENV=local\n')
    monkeypatch.setattr(devtools,'ROOT',tmp_path)
    monkeypatch.setattr(devtools,'verify_python',lambda:None)
    monkeypatch.setattr(devtools,'node_version',lambda:'24.22.1')
    monkeypatch.setattr(devtools,'npm_executable',lambda:'npm')
    def blocked(_): raise RuntimeError('Native file is in use')
    monkeypatch.setattr(devtools,'check_windows_native_files',blocked)
    monkeypatch.setattr(devtools,'checked',lambda *a,**k:pytest.fail('No install before preflight'))
    assert devtools.main(['setup'])==1
    assert (tmp_path/'.env').read_text()=='APP_ENV=local\n'


def test_failed_install_invalidates_success_marker(tmp_path, monkeypatch):
    frontend(tmp_path);pc.mark_frontend_ready(tmp_path)
    (tmp_path/'.env').write_text('APP_ENV=local\n')
    monkeypatch.setattr(devtools,'ROOT',tmp_path)
    monkeypatch.setattr(devtools,'verify_python',lambda:None)
    monkeypatch.setattr(devtools,'node_version',lambda:'24.22.1')
    monkeypatch.setattr(devtools,'npm_executable',lambda:'npm')
    monkeypatch.setattr(devtools,'environment_python',lambda:Path(sys.executable))
    monkeypatch.setattr(devtools,'check_windows_native_files',lambda _:None)
    def fail(command,**kwargs):
        if command[1]=='ci': raise subprocess.CalledProcessError(1,command)
    monkeypatch.setattr(devtools,'checked',fail)
    assert devtools.main(['setup'])==1
    assert not (tmp_path/'.data/runtime/frontend-ready.json').exists()


def test_production_stop_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(devtools,'ROOT',tmp_path)
    monkeypatch.setattr(devtools,'local_environment',lambda _: {'APP_ENV':'production'})
    monkeypatch.setattr(devtools,'stop_windows_project',lambda _:pytest.fail('Production must not be stopped'))
    assert devtools.main(['stop'])==1


@pytest.mark.skipif(os.name!='nt',reason='Native Windows job-object smoke requires Windows')
def test_native_windows_job_cleans_up_its_child():
    job=pc.WindowsJob()
    child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
    try:
        job.attach(child)
        job.close()
        child.wait(timeout=8)
    finally:
        job.close()
        if child.poll() is None: child.kill()
        child.wait(timeout=8)
