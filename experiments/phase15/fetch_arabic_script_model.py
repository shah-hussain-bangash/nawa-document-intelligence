"""Download one pinned official Arabic-script model to the local QA folder."""
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
COMMIT = 'e12c65a915945e4c28e237a9b52bc4a8f39a0cec'

def get(url):
    request = urllib.request.Request(url, headers={'User-Agent':'NAWA-synthetic-OCR-QA'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()

def main():
    target = HERE / 'tessdata-best-e12c65a' / 'script'
    target.mkdir(exist_ok=False)
    name = 'Arabic.traineddata'
    metadata = json.loads(get('https://api.github.com/repos/tesseract-ocr/tessdata_best/contents/script/' + name + '?ref=' + COMMIT))
    data = get('https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/' + COMMIT + '/script/' + name)
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if blob != metadata['sha']:
        raise ValueError('Downloaded model did not match the upstream Git blob')
    (target / name).write_bytes(data)
    provenance = {'commit':COMMIT, 'path':'script/' + name, 'git_blob':blob,
                  'sha256':hashlib.sha256(data).hexdigest(), 'size':len(data)}
    (target / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print('Downloaded and verified official Arabic-script model:', len(data), 'bytes')

if __name__ == '__main__':
    main()
