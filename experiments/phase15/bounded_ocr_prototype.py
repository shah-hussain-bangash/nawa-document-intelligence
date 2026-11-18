"""Local single-image OCR prototype; not an application worker or sandbox."""
import hashlib
import io
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_PIXELS = 12_000_000
MAX_OUTPUT_BYTES = 256 * 1024
MAX_MODEL_BYTES = 64 * 1024 * 1024
TIMEOUT_SECONDS = 20
ALLOWED_LANGUAGES = {'eng', 'ara', 'ara+eng', 'eng+ara'}

class OCRLimitError(RuntimeError):
    pass

def bounded_process(command, timeout=TIMEOUT_SECONDS, max_output=MAX_OUTPUT_BYTES):
    """Cap captured stdout and execution time; discard stderr to avoid leaks."""
    if timeout <= 0 or max_output <= 0:
        raise ValueError('Limits must be positive')
    deadline = time.monotonic() + timeout
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, shell=False)
    chunks = []
    state = {'size':0, 'overflow':False}
    def reader():
        try:
            while True:
                chunk = process.stdout.read(8192)
                if not chunk:
                    return
                state['size'] += len(chunk)
                if state['size'] > max_output:
                    state['overflow'] = True
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                    return
                chunks.append(chunk)
        finally:
            process.stdout.close()
    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        process.wait(timeout=max(0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait()
        thread.join(timeout=0.1)
        if not thread.is_alive():
            process.stdout.close()
        raise OCRLimitError('OCR timed out') from exc
    thread.join(timeout=max(0, deadline - time.monotonic()))
    if thread.is_alive():
        # An inherited pipe may still be held by a descendant. Never block
        # indefinitely waiting for it; this prototype cannot kill that tree.
        raise OCRLimitError('OCR output stream did not close before timeout')
    process.stdout.close()
    if state['overflow']:
        raise OCRLimitError('OCR output exceeds limit')
    if process.returncode:
        raise OCRLimitError('OCR process failed')
    return b''.join(chunks)

def recognize_synthetic_png(path, executable, model_dir, languages):
    """OCR one PNG with explicit configuration; output always requires review."""
    if languages not in ALLOWED_LANGUAGES:
        raise ValueError('Unsupported languages')
    path = Path(path)
    with path.open('rb') as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise OCRLimitError('Input exceeds limit')
    try:
        with Image.open(io.BytesIO(data), formats=['PNG']) as image:
            if image.width * image.height > MAX_PIXELS:
                raise OCRLimitError('Image dimensions exceed limit')
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise OCRLimitError('Invalid image') from exc
    # Use the same bounded bytes that were validated and hashed, instead of
    # passing the original path (which might change after it was checked).
    # This does not sandbox Tesseract or defend against a hostile local user.
    with tempfile.TemporaryDirectory(prefix='nawa_ocr_prototype_') as directory:
        copied_image = Path(directory) / 'input.png'
        copied_image.write_bytes(data)
        output = bounded_process([str(executable), str(copied_image), 'stdout', '--tessdata-dir',
                                  str(model_dir), '-l', languages, '--psm', '6'])
    try:
        text = output.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise OCRLimitError('OCR returned invalid UTF-8') from exc
    return {'status':'human_review_required', 'source_sha256':hashlib.sha256(data).hexdigest(),
            'language':languages, 'extracted_text_untrusted':text}

def recognize_with_model_provenance(path, executable, model_dir, languages, expected_models):
    """Run the local prototype only when supplied model hashes match."""
    if languages not in ALLOWED_LANGUAGES:
        raise ValueError('Unsupported languages')
    names = {name + '.traineddata' for name in languages.split('+')}
    if set(expected_models) != names:
        raise ValueError('Expected hashes must cover exactly the requested models')
    def check_models():
        hashes = {}
        for name in sorted(names):
            digest = hashlib.sha256()
            count = 0
            with (Path(model_dir) / name).open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    count += len(chunk)
                    if count > MAX_MODEL_BYTES:
                        raise OCRLimitError('Model exceeds size limit')
                    digest.update(chunk)
            hashes[name] = digest.hexdigest()
            if hashes[name] != expected_models[name]:
                raise OCRLimitError('Model hash does not match expected value')
        return hashes
    hashes = check_models()
    try:
        engine_version = bounded_process([str(executable), '--version'], timeout=10,
                                         max_output=8192).decode('utf-8').splitlines()[0]
    except (UnicodeDecodeError, IndexError) as exc:
        raise OCRLimitError('Cannot identify OCR engine version') from exc
    result = recognize_synthetic_png(path, executable, model_dir, languages)
    check_models()
    result.update({'engine_version_unverified':engine_version, 'model_sha256':hashes,
                   'page_segmentation_mode':6})
    return result
