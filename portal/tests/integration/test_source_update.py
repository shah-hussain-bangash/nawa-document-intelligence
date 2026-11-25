import hashlib
import json
from pathlib import Path
import pytest
from scripts.apply_source_update import apply_update
from scripts.process_control import project_lock


def prepare(tmp_path):
    root=tmp_path/'project';root.mkdir()
    (root/'nawa.py').write_bytes(b'old source')
    (root/'.env').write_bytes(b'PRIVATE_CONFIG=test-only')
    (root/'.data').mkdir();(root/'.data/records.txt').write_bytes(b'preserved records')
    payload=tmp_path/'payload';(payload/'files').mkdir(parents=True)
    (payload/'files/nawa.py').write_bytes(b'updated source')
    manifest={'release':'test','files':[{'path':'nawa.py','base_sha256':hashlib.sha256(b'old source').hexdigest(),'sha256':hashlib.sha256(b'updated source').hexdigest()}]}
    (payload/'manifest.json').write_text(json.dumps(manifest))
    return root,payload,manifest


def test_update_preserves_config_data_and_keeps_source_backup(tmp_path):
    root,payload,_=prepare(tmp_path)
    result=apply_update(root,payload,project_lock)
    assert (root/'nawa.py').read_bytes()==b'updated source'
    assert (Path(result['source_backup'])/'nawa.py').read_bytes()==b'old source'
    assert (root/'.env').read_bytes()==b'PRIVATE_CONFIG=test-only'
    assert (root/'.data/records.txt').read_bytes()==b'preserved records'


def test_update_rejects_custom_source_and_running_launcher_before_mutation(tmp_path):
    root,payload,_=prepare(tmp_path)
    with project_lock(root):
        with pytest.raises(RuntimeError):apply_update(root,payload,project_lock)
    (root/'nawa.py').write_bytes(b'custom code')
    with pytest.raises(ValueError,match='differs'):apply_update(root,payload,project_lock)
    assert (root/'nawa.py').read_bytes()==b'custom code'


@pytest.mark.parametrize('name',['../escaped','.env','.data/records.txt'])
def test_update_cannot_target_runtime_or_parent_paths(tmp_path,name):
    root,payload,manifest=prepare(tmp_path)
    manifest['files'][0]['path']=name
    (payload/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='forbidden'):apply_update(root,payload,project_lock)
    assert (root/'nawa.py').read_bytes()==b'old source'
    assert (root/'.env').read_bytes()==b'PRIVATE_CONFIG=test-only'


def test_update_checksum_failure_does_not_write_source(tmp_path):
    root,payload,_=prepare(tmp_path)
    (payload/'files/nawa.py').write_bytes(b'corrupted download')
    with pytest.raises(ValueError,match='checksum'):apply_update(root,payload,project_lock)
    assert (root/'nawa.py').read_bytes()==b'old source'


def test_update_restores_earlier_source_if_later_file_write_fails(tmp_path,monkeypatch):
    from scripts import apply_source_update as updater
    root,payload,manifest=prepare(tmp_path)
    (payload/'files/new.py').write_bytes(b'new file')
    manifest['files'].append({'path':'new.py','base_sha256':None,'sha256':hashlib.sha256(b'new file').hexdigest()})
    (payload/'manifest.json').write_text(json.dumps(manifest))
    original=updater.atomic_write
    def failed(path,data):
        if path.name=='new.py':raise OSError('Simulated file write denial')
        original(path,data)
    monkeypatch.setattr(updater,'atomic_write',failed)
    with pytest.raises(OSError):apply_update(root,payload,project_lock)
    assert (root/'nawa.py').read_bytes()==b'old source'
    assert not (root/'new.py').exists()
