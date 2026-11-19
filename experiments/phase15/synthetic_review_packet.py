"""Create a human-review packet for fixed synthetic image regions only."""
import argparse
import hashlib
import html
import io
import json
from pathlib import Path
from PIL import Image
import ocr_benchmark as bench
from numeric_crop_experiment import REGIONS

def create_packet(image_path, expected_sha256, regions, output_dir):
    image_path, output_dir = Path(image_path), Path(output_dir)
    data = image_path.read_bytes()
    source_hash = hashlib.sha256(data).hexdigest()
    if source_hash != expected_sha256:
        raise ValueError('Synthetic source image does not match the expected hash')
    if not regions:
        raise ValueError('No review regions provided')
    with Image.open(io.BytesIO(data), formats=['PNG']) as image:
        for label, box in regions:
            if not isinstance(label, str) or not label or len(box) != 4:
                raise ValueError('Invalid review region')
            x1, y1, x2, y2 = box
            if not (0 <= x1 < x2 <= image.width and 0 <= y1 < y2 <= image.height):
                raise ValueError('Review region is outside the source image')
        output_dir.mkdir(parents=False, exist_ok=False)
        (output_dir / 'source.png').write_bytes(data)
        entries = []
        for index, (label, box) in enumerate(regions, 1):
            crop_path = output_dir / f'region-{index}.png'
            image.crop(box).save(crop_path)
            entries.append({'label':label, 'source_page':1, 'box_pixels':list(box),
                            'crop_file':crop_path.name,
                            'crop_sha256':hashlib.sha256(crop_path.read_bytes()).hexdigest(),
                            'status':'human_review_required'})
    packet = {'scope':'Fixed synthetic image and manually selected regions; not a general document review tool.',
              'status':'human_review_required', 'source_image_sha256':source_hash, 'source_file':'source.png',
              'note':'Inspect the complete original image and each crop. No number or approval has been inferred.',
              'regions':entries}
    (output_dir / 'review-packet.json').write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding='utf-8')
    cards = ''.join('<section class="region" data-label="' + html.escape(item['label'], quote=True) +
        '" data-crop="' + item['crop_file'] + '" data-crop-sha="' + item['crop_sha256'] +
        '" data-box="' + html.escape(json.dumps(item['box_pixels']), quote=True) +
        '"><h2>' + html.escape(item['label']) + '</h2><img src="' +
        item['crop_file'] + '" alt="Synthetic source crop for ' + html.escape(item['label'], quote=True) +
        '"><p>Human review required. Source page 1; crop pixels ' +
        html.escape(str(item['box_pixels'])) + '.</p><label>Reviewer transcription '
        '<input maxlength="80" autocomplete="off" placeholder="Enter what you see"></label></section>' for item in entries)
    page = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Synthetic OCR review</title>'
            '<style>body{font:16px system-ui;max-width:850px;margin:40px auto;padding:0 20px;color:#102336}'
            'section{border:1px solid #ccc;border-radius:8px;margin:16px 0;padding:16px}'
            'img{width:400px;max-width:100%;image-rendering:auto}code{overflow-wrap:anywhere}</style>'
            '<h1>Synthetic OCR: human review required</h1><p>Compare these manually selected regions with '
            'the <a href="source.png">original synthetic image</a>. No value or approval has been inferred.</p>'
            '<p>Original image SHA-256: <code>' + source_hash + '</code></p>' + cards +
            '<p>Entries stay on this page until you download them. They do not approve the quotation.</p>'
            '<button id="download" type="button">Download review JSON</button>'
            '<script>document.getElementById("download").addEventListener("click",()=>{'
            'const regions=Array.from(document.querySelectorAll(".region"),el=>({'
            'label:el.dataset.label,source_page:1,box_pixels:JSON.parse(el.dataset.box),'
            'crop_file:el.dataset.crop,crop_sha256:el.dataset.cropSha,'
            'reviewer_transcription:el.querySelector("input").value}));'
            'const result={scope:"synthetic image; reviewer transcription only",'
            'status:"human_review_required",source_image_sha256:"' + source_hash + '",regions};'
            'const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:"application/json"}));'
            'const a=document.createElement("a");a.href=url;a.download="nawa-synthetic-review.json";'
            'document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);'
            '});</script></html>')
    (output_dir / 'review.html').write_text(page, encoding='utf-8')
    return packet

def main():
    parser = argparse.ArgumentParser(description='Create a fixed synthetic review packet')
    parser.add_argument('--output-dir', type=Path, required=True, help='New empty output directory')
    args = parser.parse_args()
    sample = bench.SAMPLES[1]
    regions = [(name.replace('_', ' ').title(), box) for name, box, _ in REGIONS]
    packet = create_packet(bench.HERE / sample['image'], sample['sha256'], regions, args.output_dir)
    print('Created', len(packet['regions']), 'synthetic review regions; human review required.')

if __name__ == '__main__':
    main()
