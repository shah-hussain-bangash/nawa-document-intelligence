"""Real synthetic Arabic PDF extraction; no embedding model required."""
from pathlib import Path
import unittest
import nawa_demo

from synthetic_review_demo import parse_arabic_sample

DEMO=Path(nawa_demo.__file__).resolve().parent.parent


class SyntheticArabicParserTests(unittest.TestCase):
    def test_mixed_arabic_fixture_is_extracted_with_page_provenance(self):
        sample=(DEMO/'samples'/'pdf'/'arabic_text_supplier.pdf').read_bytes()
        result=parse_arabic_sample(sample,DEMO)
        self.assertEqual(result['total'],'945.00')
        self.assertEqual(result['evidence']['total']['page'],1)
        self.assertEqual(result['evidence']['total']['page_line'],6)
        self.assertEqual(result['evidence']['total']['source_text'],'Grand Total: 945.00')
        self.assertIn('raw_extracted_text',result['evidence']['supplier'])


if __name__=='__main__':
    unittest.main()

