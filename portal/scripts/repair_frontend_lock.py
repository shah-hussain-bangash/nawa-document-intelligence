"""Repair the five dependency records accidentally rewritten in UI release bumps."""
import json
from pathlib import Path
import shutil


def repair(path):
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    packages=data['packages']
    corrections={
        '@jridgewell/gen-mapping': ('0.3.13', 'https://registry.npmjs.org/@jridgewell/gen-mapping/-/gen-mapping-0.3.13.tgz'),
        '@standard-schema/utils': ('0.3.0', 'https://registry.npmjs.org/@standard-schema/utils/-/utils-0.3.0.tgz'),
        'immer': ('10.2.0', 'https://registry.npmjs.org/immer/-/immer-10.2.0.tgz'),
    }
    # All affected entries are restored together, not just the first npm error.
    for name,(version,url) in corrections.items():
        item=packages['node_modules/'+name]
        item['version'],item['resolved']=version,url
    packages['node_modules/@babel/generator']['dependencies']['@jridgewell/gen-mapping']='^0.3.12'
    packages['node_modules/@reduxjs/toolkit']['dependencies']['@standard-schema/utils']='^0.3.0'
    backup=path.with_name('package-lock.before-repair.json')
    if not backup.exists():
        shutil.copy2(path,backup)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    repair(root/'apps/web/package-lock.json')
    print('Frontend lock repaired. Configuration and saved data were not changed.')
