from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
import subprocess
import sys
from unittest.mock import patch

from nawa_demo.intake_jobs import IntakeJobs
from nawa_demo.intake_pipeline import SyntheticIntakePipeline
from nawa_demo.intake_store import LocalIntakeStore
from nawa_demo.intake_worker import process_one
from nawa_demo.intake_parser import is_synthetic_arabic_pdf, encode_result
from nawa_demo.intake_limits import MAX_PARSER_RESULT_BYTES


def synthetic_fixture(name):
    """Read an existing bundled fixture without changing it."""
    path = Path(__file__).resolve().parents[1] / 'samples' / 'pdf' / name
    return path.read_bytes()


class IntakeWorkerTests(unittest.TestCase):
    def test_parser_output_limit_counts_encoded_bytes(self):
        self.assertEqual(encode_result({'value':'valid'}), b'{"value": "valid"}')
        with self.assertRaises(ValueError):
            encode_result({'value':'\u0627' * MAX_PARSER_RESULT_BYTES})

    def test_oversized_result_is_not_written_or_promoted(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = (b'Supplier: ' + b'x' * (MAX_PARSER_RESULT_BYTES // 2)
                      + b'\nCurrency: AED\nSubtotal: 1000\nVAT Rate: 5\n'
                        b'VAT Amount: 50\nGrand Total: 1050\n')
            path = root / 'synthetic.txt'
            path.write_bytes(source)
            parsed = subprocess.run([sys.executable, '-m', 'nawa_demo.intake_parser', str(path)],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20)
            self.assertNotEqual(parsed.returncode, 0)
            self.assertEqual(parsed.stdout, b'')
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            document, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'synthetic.txt', source)
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=1), 'failed')
            self.assertIsNone(jobs.result('a', document))

    def test_arabic_pdf_route_is_exact_fixture_only(self):
        sample=synthetic_fixture('arabic_text_supplier.pdf')
        self.assertTrue(is_synthetic_arabic_pdf(sample))
        self.assertFalse(is_synthetic_arabic_pdf(sample+b' '))

    def test_mixed_arabic_pdf_has_cited_normalized_evidence(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            store=LocalIntakeStore(root/'files')
            jobs=IntakeJobs(root/'jobs.db')
            document,_=SyntheticIntakePipeline(store,jobs).submit(
                'a','arabic.pdf',synthetic_fixture('arabic_text_supplier.pdf'))
            self.assertEqual(process_one(jobs,store,'a'),'completed')
            result=jobs.result('a',document)
            self.assertEqual(result['total'],'945.00')
            self.assertEqual(result['evidence']['total']['page'],1)
            self.assertEqual(result['evidence']['total']['method'],'text_layer')
            self.assertIn('raw_extracted_text',result['evidence']['supplier'])

    def test_arabic_pdf_fallback_is_synthetic_opt_in(self):
        sample=synthetic_fixture('arabic_text_supplier.pdf')+b'\n'
        self.assertFalse(is_synthetic_arabic_pdf(sample))
        for mode,flag,enabled in (('synthetic','0',False),('other','1',False),('synthetic','1',True)):
            with self.subTest(mode=mode,flag=flag), TemporaryDirectory() as folder:
                root=Path(folder)
                store=LocalIntakeStore(root/'files')
                jobs=IntakeJobs(root/'jobs.db')
                document,_=SyntheticIntakePipeline(store,jobs).submit('a','arabic.pdf',sample)
                env={'NAWA_INTAKE':mode,'NAWA_EXPERIMENTAL_ARABIC_PDF':flag}
                with patch.dict(os.environ,env):
                    state=process_one(jobs,store,'a',max_attempts=1)
                self.assertEqual(state,'completed' if enabled else 'failed')
                if enabled:
                    result=jobs.result('a',document)
                    self.assertEqual(result['total'],'945.00')
                    self.assertIn('raw_extracted_text',result['evidence']['supplier'])
                else:
                    self.assertIsNone(jobs.result('a',document))

    def test_arabic_pdf_fallback_does_not_enable_ocr(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            store=LocalIntakeStore(root/'files')
            jobs=IntakeJobs(root/'jobs.db')
            document,_=SyntheticIntakePipeline(store,jobs).submit(
                'a','scan.pdf',synthetic_fixture('image_only.pdf'))
            with patch.dict(os.environ,{'NAWA_INTAKE':'synthetic','NAWA_EXPERIMENTAL_ARABIC_PDF':'1'}):
                self.assertEqual(process_one(jobs,store,'a',max_attempts=1),'failed')
            self.assertIsNone(jobs.result('a',document))

    def test_parser_timeout_returns_retry_without_result(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'x.txt', b'synthetic')
            with patch('nawa_demo.intake_worker.subprocess.run', side_effect=subprocess.TimeoutExpired('parser', 1)):
                self.assertEqual(process_one(jobs, store, 'a', timeout=1), 'retry-pending')
            self.assertIsNone(jobs.result('a', doc))

    def test_selectable_pdf_result_has_page_evidence(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            sample = synthetic_fixture('second_page_supplier.pdf')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'sample.pdf', sample)
            self.assertEqual(process_one(jobs, store, 'a'), 'completed')
            result = jobs.result('a', doc)
            self.assertEqual(result['input_type'], 'text_layer_pdf')
            self.assertEqual(result['evidence']['supplier']['page'], 2)

    def test_image_only_pdf_is_not_claimed_as_processed(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            sample = synthetic_fixture('image_only.pdf')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'scan.pdf', sample)
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=1), 'failed')
            self.assertIsNone(jobs.result('a', doc))

    def test_extracts_synthetic_arabic_after_reopen(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            sample = (Path(__file__).resolve().parents[1] / 'samples' / 'arabic_quote.txt').read_bytes()
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'arabic.txt', sample)
            self.assertEqual(process_one(jobs, store, 'a'), 'completed')
            result = IntakeJobs(root / 'jobs.db').result('a', doc)
            self.assertEqual(result['total'], '945.00')
            self.assertIsNone(jobs.result('b', doc))
            self.assertIsNone(process_one(jobs, store, 'a'))

    def test_integrity_failure_retries_then_fails_without_result(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = LocalIntakeStore(root / 'files')
            jobs = IntakeJobs(root / 'jobs.db')
            doc, _ = SyntheticIntakePipeline(store, jobs).submit('a', 'x.txt', b'valid utf8')
            (root / 'files' / doc).write_bytes(b'tampered')
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=2), 'retry-pending')
            self.assertEqual(process_one(jobs, store, 'a', max_attempts=2), 'failed')
            self.assertIsNone(jobs.result('a', doc))


if __name__ == '__main__':
    unittest.main()

