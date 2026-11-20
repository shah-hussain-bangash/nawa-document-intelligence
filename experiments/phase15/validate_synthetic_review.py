"""Check a synthetic review export against its local packet; not authentication."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
from PIL import Image

MAX_JSON_BYTES = 64 * 1024

def read_json(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError('Review JSON exceeds limit')
    return json.loads(data.decode('utf-8'))

def validate_export(packet_dir, export_path, *, expected_source_sha256, expected_regions):
    packet_dir = Path(packet_dir)
    packet = read_json(packet_dir / 'review-packet.json')
    export = read_json(export_path)
    if not isinstance(packet, dict) or not isinstance(export, dict):
        raise ValueError('Review data must be JSON objects')
    if packet.get('status') != 'human_review_required' or export.get('status') != 'human_review_required':
        raise ValueError('Invalid review status')
    source = (packet_dir / 'source.png').read_bytes()
    source_sha = hashlib.sha256(source).hexdigest()
    if (source_sha != expected_source_sha256 or source_sha != packet.get('source_image_sha256')
            or source_sha != export.get('source_image_sha256')):
        raise ValueError('Source image hash mismatch')
    expected, reviewed = packet.get('regions'), export.get('regions')
    if not isinstance(expected, list) or not isinstance(reviewed, list) or not 1 <= len(expected) <= 20 or len(expected) != len(reviewed):
        raise ValueError('Review region count mismatch')
    if len(expected) != len(expected_regions):
        raise ValueError('Trusted region count mismatch')
    used_labels, used_files = set(), set()
    with Image.open(io.BytesIO(source), formats=['PNG']) as original:
        for region, entry, trusted in zip(expected, reviewed, expected_regions):
            if not isinstance(region, dict) or not isinstance(entry, dict):
                raise ValueError('Invalid region')
            label, name, box = region.get('label'), region.get('crop_file'), region.get('box_pixels')
            if (label, box) != (trusted[0], list(trusted[1])):
                raise ValueError('Review region differs from trusted fixture')
            if (not isinstance(label, str) or not label or label in used_labels or
                    not isinstance(name, str) or not re.fullmatch(r'region-[1-9][0-9]*\.png', name) or name in used_files):
                raise ValueError('Invalid or duplicate region identity')
            used_labels.add(label)
            used_files.add(name)
            if (not isinstance(box, list) or len(box) != 4 or
                    any(not isinstance(v, int) or isinstance(v, bool) for v in box) or
                    not (0 <= box[0] < box[2] <= original.width and 0 <= box[1] < box[3] <= original.height)):
                raise ValueError('Invalid crop coordinates')
            for field in ('label', 'source_page', 'box_pixels', 'crop_file', 'crop_sha256'):
                if region.get(field) != entry.get(field):
                    raise ValueError('Review region metadata mismatch')
            if region.get('source_page') != 1 or region.get('status') != 'human_review_required':
                raise ValueError('Invalid source page or region status')
            crop_bytes = (packet_dir / name).read_bytes()
            if hashlib.sha256(crop_bytes).hexdigest() != region.get('crop_sha256'):
                raise ValueError('Crop hash mismatch')
            with Image.open(io.BytesIO(crop_bytes), formats=['PNG']) as crop:
                expected_crop = original.crop(tuple(box))
                if crop.mode != expected_crop.mode or crop.size != expected_crop.size or crop.tobytes() != expected_crop.tobytes():
                    raise ValueError('Crop does not match source coordinates')
            value = entry.get('reviewer_transcription')
            if not isinstance(value, str) or len(value) > 80:
                raise ValueError('Invalid reviewer transcription')
    return {'status':'human_review_required', 'regions':len(reviewed),
            'with_transcription':sum(bool(item['reviewer_transcription'].strip()) for item in reviewed),
            'scope':'Synthetic local consistency check; no reviewer authentication or approval.'}

def main():
    import ocr_benchmark as bench
    from numeric_crop_experiment import REGIONS
    parser = argparse.ArgumentParser(description='Check a synthetic review export')
    parser.add_argument('--packet-dir', type=Path, required=True)
    parser.add_argument('--export', type=Path, required=True)
    args = parser.parse_args()
    regions = [(name.replace('_', ' ').title(), box) for name, box, _ in REGIONS]
    print(json.dumps(validate_export(args.packet_dir, args.export,
        expected_source_sha256=bench.SAMPLES[1]['sha256'], expected_regions=regions), indent=2))

if __name__ == '__main__':
    main()
