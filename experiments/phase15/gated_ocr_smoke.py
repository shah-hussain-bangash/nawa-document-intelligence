"""Windows-only gated OCR smoke tests on two hash-pinned synthetic PNGs."""
import importlib.util
import subprocess
from pathlib import Path
import ocr_benchmark as baseline
from windows_gated_launcher_experiment import start_gated

SOURCE = Path(r'C:\UAE-Sovereign-Agentic-AI\nawa-workspace\scripts\process_control.py')

def run_sample(module, sample, expected_matches):
    image = baseline.HERE / sample['image']
    baseline.verify(image, sample['sha256'])
    for language in sample['language'].split('+'):
        name = language + '.traineddata'
        baseline.verify(baseline.TESSDATA / name, baseline.MODEL_HASHES[name])
    job = module.WindowsJob()
    parent = None
    try:
        parent = start_gated(job, [str(baseline.TESSERACT), str(image), 'stdout',
            '--tessdata-dir', str(baseline.TESSDATA), '-l', sample['language'], '--psm', '6'])
        # For this fixed synthetic smoke test only, output is expected to be
        # small; this path is not suitable for untrusted documents.
        parent.wait(timeout=20)
        if parent.returncode:
            raise RuntimeError('Synthetic OCR failed')
        # End any remaining job descendants before draining their inherited pipe.
        job.close()
        output = parent.stdout.read(256 * 1024 + 1)
        if len(output) > 256 * 1024:
            raise RuntimeError('Synthetic OCR output exceeds the test limit')
        text = output.decode('utf-8')
        fields = baseline.field_results(text, sample['fields'])
        if sum(fields.values()) != expected_matches:
            raise AssertionError('The synthetic OCR field count changed')
        print(f"Gated {sample['id']} OCR: {sum(fields.values())}/6 fields matched; human review required.")
    finally:
        job.close()
        if parent is not None:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            parent.stdout.close()

def main():
    spec = importlib.util.spec_from_file_location('nawa_local_process_control', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for sample, expected in zip(baseline.SAMPLES, (6, 2)):
        run_sample(module, sample, expected)

if __name__ == '__main__':
    main()
