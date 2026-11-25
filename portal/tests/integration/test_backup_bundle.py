from pathlib import Path
import json
import sqlite3
import zipfile
import pytest
from scripts.backup_workspace import backup, restore
from test_workspace import app, client, login


def test_verified_bundle_restores_database_and_originals(client,app,tmp_path):
    login(client)
    doc=client.post('/api/v1/documents',files={'file':('test.txt',b'Original quotation source','text/plain')}).json()
    settings=app.state.settings
    output=tmp_path.parent/(tmp_path.name+'-backup.zip')
    backup(settings.database_url,settings.data_dir,output)
    target=tmp_path/'restored'
    restore(output,target)
    with sqlite3.connect(target/'database.sqlite3') as database:
        assert database.execute('SELECT title FROM documents WHERE id=?',(doc['id'],)).fetchone()[0]=='test.txt'
    originals=list((target/'uploads').iterdir())
    assert any(p.read_bytes()==b'Original quotation source' for p in originals)
    assert not (target/'.env').exists()
    with pytest.raises(ValueError):restore(output,target)
    with pytest.raises(ValueError):backup(settings.database_url,settings.data_dir,output)


def test_restore_rejects_tampered_original_and_path_traversal(client,app,tmp_path):
    output=tmp_path.parent/(tmp_path.name+'-backup.zip')
    backup(app.state.settings.database_url,app.state.settings.data_dir,output)
    damaged=tmp_path/'damaged.zip'
    with zipfile.ZipFile(output) as original,zipfile.ZipFile(damaged,'w') as target:
        for name in original.namelist():
            target.writestr(name,b'bad' if name=='database.sqlite3' else original.read(name))
    with pytest.raises(ValueError):restore(damaged,tmp_path/'invalid-restore')
    assert not (tmp_path/'invalid-restore').exists()
    with zipfile.ZipFile(damaged,'w') as target:target.writestr('../escaped','bad')
    with pytest.raises(ValueError):restore(damaged,tmp_path/'invalid-restore')
    assert not (tmp_path/'escaped').exists()
