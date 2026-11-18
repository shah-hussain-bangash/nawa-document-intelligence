"""Two-document synthetic OCR baseline, not a production OCR worker."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import unicodedata

HERE=Path(__file__).resolve().parent
TESSERACT=Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
TESSDATA=HERE/'tessdata-8741641'
MODEL_HASHES={'ara.traineddata':'e3206d3dc87fd50c24a0fb9f01838615911d25168f4e64415244b67d2bb3e729',
              'eng.traineddata':'7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'}
SAMPLES=[
    {'id':'english','image':'english-scan.png',
     'sha256':'b88a4be58fa8868003788d20d217117be8e3a6d995e8e6d57e37c1411880a649',
     'language':'eng','reference':[
         'Supplier: Example English Supplies','Currency: AED','Subtotal: 1000.00',
         'VAT Rate: 5','VAT Amount: 50.00','Grand Total: 1050.00'],
     'fields':{'supplier':'Example English Supplies','currency':'AED','subtotal':'1000.00',
               'vat_rate':'5','vat_amount':'50.00','total':'1050.00'}},
    {'id':'arabic_labels','image':'arabic-label-scan.png',
     'sha256':'1b4e376e15feab5c2f35a1cfc2d613e853c0b259b3566e2c7a4a8361d938f05f',
     'language':'ara+eng','reference':[
         'عرض سعر تجريبي','اسم المورد: شركة المثال للتوريدات','العملة: AED',
         'المجموع الفرعي: ٩٠٠٫٠٠','نسبة الضريبة: ٥','قيمة الضريبة: ٤٥٫٠٠',
         'الإجمالي شامل الضريبة: ٩٤٥٫٠٠','بيانات تجريبية فقط'],
     'fields':{'supplier':'شركة المثال للتوريدات','currency':'AED','subtotal':'900.00',
               'vat_rate':'5','vat_amount':'45.00','total':'945.00'}},
]
LABELS={'supplier':('supplier','اسم المورد'), 'currency':('currency','العملة'),
        'subtotal':('subtotal','المجموع الفرعي'), 'vat_rate':('vat rate','نسبة الضريبة'),
        'vat_amount':('vat amount','قيمة الضريبة'), 'total':('grand total','الإجمالي شامل الضريبة')}


def normalize(text):
    text=unicodedata.normalize('NFKC',text)
    return ' '.join(''.join(c for c in text if unicodedata.category(c)!='Cf').split())


def distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):
            current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]


def rates(reference,recognized):
    reference,recognized=normalize(reference),normalize(recognized)
    if not reference:
        raise ValueError('Reference is empty')
    return {'cer':distance(reference,recognized)/len(reference),
            'wer':distance(reference.split(),recognized.split())/len(reference.split())}


def field_results(text,expected):
    digit_map=str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬','01234567890123456789.,')
    def value(text):
        return normalize(text).translate(digit_map).replace(',','').strip().casefold()
    fields={}
    for line in text.splitlines():
        line=normalize(line)
        if ':' not in line:
            continue
        label,raw=(part.strip() for part in line.split(':',1))
        match=next((key for key,variants in LABELS.items() if label.casefold() in variants),None)
        if match:
            fields.setdefault(match,[]).append(raw)
    return {key:len(fields.get(key,[]))==1 and value(fields[key][0])==value(expected[key])
            for key in expected}


def verify(path,digest):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:
        raise ValueError('Synthetic input or OCR language data changed')


def run():
    for name,digest in MODEL_HASHES.items():
        verify(TESSDATA/name,digest)
    version=subprocess.run([str(TESSERACT),'--version'],check=True,capture_output=True,
                           timeout=10).stdout.decode('utf-8').splitlines()[0]
    rows=[]
    for sample in SAMPLES:
        image=HERE/sample['image']
        verify(image,sample['sha256'])
        start=time.perf_counter()
        result=subprocess.run([str(TESSERACT),str(image),'stdout','--tessdata-dir',str(TESSDATA),
                               '-l',sample['language'],'--psm','6'],
                              check=True,capture_output=True,timeout=30)
        elapsed=time.perf_counter()-start
        output=result.stdout.decode('utf-8')
        measured=rates('\n'.join(sample['reference']),output)
        fields=field_results(output,sample['fields'])
        rows.append({'id':sample['id'],'language':sample['language'],
                     'image_sha256':sample['sha256'],'cer':measured['cer'],'wer':measured['wer'],
                     'fields_correct':sum(fields.values()),'fields_total':len(fields),
                     'field_matches':fields,'elapsed_seconds_single_run':round(elapsed,3),
                     'ocr_text_synthetic':output})
    return {'scope':'Two local synthetic samples; not a representative or independently reviewed benchmark.',
            'engine':version,'model_commit':'87416418657359cb625c412a48b6e1d6d41c29bd',
            'model_sha256':MODEL_HASHES,'render_dpi':200,'page_segmentation_mode':6,
            'normalization':'NFKC, strip Unicode format marks, collapse whitespace; no reordering or digit conversion in CER/WER.',
            'status':'human_review_required','cases':rows}


def main():
    parser=argparse.ArgumentParser(description='Run local synthetic OCR baseline')
    parser.add_argument('--output',type=Path,required=True,help='New result file; existing files are not overwritten')
    args=parser.parse_args()
    result=run()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print('Synthetic OCR results saved; both cases require human review.')


if __name__=='__main__':
    main()

