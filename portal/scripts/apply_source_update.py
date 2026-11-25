"""Guarded source-only update. Runtime configuration/data are never payload files."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
from uuid import uuid4


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_target(root, relative):
    path=PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or not path.parts or any(part in {'.env','.data','.git','.venv','node_modules'} or part.startswith('.env.') for part in path.parts):
        raise ValueError('Update contains a forbidden path')
    target=root.joinpath(*path.parts)
    for parent in [target,*target.parents]:
        if parent==root:break
        if parent.is_symlink():raise ValueError('Symlinked update paths require manual review')
    return target


def atomic_write(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.nawa-update-'+uuid4().hex)
    try:
        with temporary.open('xb') as output:output.write(data)
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_update(root,payload,lock):
    root,payload=Path(root).resolve(),Path(payload).resolve()
    manifest=json.loads((payload/'manifest.json').read_text(encoding='utf-8'))
    records=manifest['files']
    if not records or len({item['path'] for item in records})!=len(records):
        raise ValueError('Invalid update manifest')
    # Verify every incoming byte and existing source before writing any source.
    prepared=[]
    with lock(root):
        for item in records:
            target=safe_target(root,item['path'])
            incoming=safe_target(payload/'files',item['path'])
            data=incoming.read_bytes()
            if digest(data)!=item['sha256']:raise ValueError('Update payload checksum mismatch: '+item['path'])
            if target.exists() and not target.is_file():raise ValueError('Update target is not a file: '+item['path'])
            before=target.read_bytes() if target.exists() else None
            expected=item['base_sha256']
            if (digest(before) if before is not None else None)!=expected:
                raise ValueError('Source differs from the expected base release: '+item['path']+'. No source files were changed; use the full release in a new folder or review your custom changes.')
            prepared.append((item['path'],target,before,data))
        backup=root/'.data/update-backups'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8])
        backup.mkdir(parents=True,mode=0o700)
        for name,target,before,data in prepared:
            if before is not None:
                saved=backup.joinpath(*PurePosixPath(name).parts);saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_bytes(before)
        (backup/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        changed=[]
        try:
            for name,target,before,data in prepared:
                atomic_write(target,data)
                changed.append((target,before))
        except Exception:
            for target,before in reversed(changed):
                if before is None:target.unlink(missing_ok=True)
                else:atomic_write(target,before)
            raise
    return {'files_updated':len(prepared),'source_backup':str(backup),'release':manifest['release']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--payload',type=Path,required=True)
    args=parser.parse_args()
    root=args.project.resolve()
    if not (root/'nawa.py').is_file():parser.error('Select the project folder containing nawa.py')
    sys.path.insert(0,str(root))
    from scripts.process_control import project_lock
    try:
        result=apply_update(root,args.payload,project_lock)
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        print('UPDATE STOPPED:',exc)
        raise SystemExit(1) from None
    print('SOURCE UPDATE COMPLETE:',result['release'],';',result['files_updated'],'files.')
    print('Previous source backup:',result['source_backup'])
    print('Configuration and saved records were not payload targets.')
    print('Next: py -3.12 nawa.py setup --stop-running, then run --auto-ports after setup succeeds.')
