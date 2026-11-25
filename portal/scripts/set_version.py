"""Change application release metadata without rewriting dependency versions."""
import json
from pathlib import Path
import re


def set_version(root, version):
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version):
        raise ValueError("Use a numeric major.minor.patch release version")
    for name in ['apps/web/package.json', 'apps/web/package-lock.json']:
        path = root / name
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        data['version'] = version
        if name.endswith('package-lock.json'):
            data['packages']['']['version'] = version
        path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    for name, pattern, replacement in [
        ('pyproject.toml', r'^version = "[^"]+"$', f'version = "{version}"'),
        ('backend/src/uae_ai/__init__.py', r'^__version__ = "[^"]+"$', f'__version__ = "{version}"'),
    ]:
        path = root / name
        text, count = re.subn(pattern, replacement, path.read_text(encoding='utf-8'), flags=re.M)
        if count != 1:
            raise ValueError(f'Expected exactly one release version in {name}')
        path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    args=parser.parse_args()
    set_version(Path(__file__).resolve().parents[1], args.version)
