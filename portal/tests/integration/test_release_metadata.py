import copy
import json
from pathlib import Path
import shutil
from scripts.set_version import set_version
from scripts.repair_frontend_lock import repair

ROOT=Path(__file__).resolve().parents[2]


def test_release_bump_leaves_every_dependency_record_unchanged(tmp_path):
    for name in ['apps/web/package.json','apps/web/package-lock.json','pyproject.toml','backend/src/uae_ai/__init__.py']:
        target=tmp_path/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target)
    original=json.loads((tmp_path/'apps/web/package-lock.json').read_text())
    set_version(tmp_path,'0.3.1')
    set_version(tmp_path,'0.4.0')
    result=json.loads((tmp_path/'apps/web/package-lock.json').read_text())
    assert {k:v for k,v in result['packages'].items() if k}=={k:v for k,v in original['packages'].items() if k}
    assert result['version']==result['packages']['']['version']=='0.4.0'
    assert result['packages']['node_modules/@jridgewell/gen-mapping']['version']=='0.3.13'


def test_repair_restores_entire_lock_preserves_metadata_and_backup(tmp_path):
    original=json.loads((ROOT/'apps/web/package-lock.json').read_text())
    broken=copy.deepcopy(original)
    for node in ['@jridgewell/gen-mapping','@standard-schema/utils','immer']:
        item=broken['packages']['node_modules/'+node]
        item['version']=item['version'].replace('0.3.1','0.4.0').replace('0.3.0','0.4.0').replace('10.2.0','10.4.0')
        item['resolved']=item['resolved'].replace('0.3.1','0.4.0').replace('0.3.0','0.4.0').replace('10.2.0','10.4.0')
    broken['packages']['node_modules/@babel/generator']['dependencies']['@jridgewell/gen-mapping']='^0.4.02'
    broken['packages']['node_modules/@reduxjs/toolkit']['dependencies']['@standard-schema/utils']='^0.4.0'
    path=tmp_path/'package-lock.json';path.write_text(json.dumps(broken))
    repair(path)
    assert json.loads(path.read_text())==original
    backup=(tmp_path/'package-lock.before-repair.json').read_bytes()
    repair(path)
    assert (tmp_path/'package-lock.before-repair.json').read_bytes()==backup
