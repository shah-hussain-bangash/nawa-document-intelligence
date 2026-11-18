"""Fetch pinned official tessdata_best files for an isolated local experiment."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
API = 'https://api.github.com/repos/tesseract-ocr/tessdata_best'

def get(url):
    request = urllib.request.Request(url, headers={'User-Agent':'NAWA-synthetic-OCR-QA'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()

def main():
    commit = json.loads(get(API + '/commits/main'))['sha']
    target = ROOT / ('tessdata-best-' + commit[:7])
    target.mkdir(exist_ok=False)
    entries = {}
    for name in ('ara.traineddata', 'eng.traineddata', 'LICENSE'):
        metadata = json.loads(get(API + '/contents/' + name + '?ref=' + commit))
        data = get('https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/' + commit + '/' + name)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != metadata['sha']:
            raise ValueError('Downloaded file did not match GitHub object: ' + name)
        (target / name).write_bytes(data)
        entries[name] = {'git_blob':blob, 'sha256':hashlib.sha256(data).hexdigest(), 'size':len(data)}
        print(name, len(data), 'bytes, verified')
    with (target / 'provenance.json').open('x', encoding='utf-8') as stream:
        json.dump({'repository':API, 'commit':commit, 'files':entries}, stream, indent=2)
    print('Model commit:', commit)

if __name__ == '__main__':
    main()
