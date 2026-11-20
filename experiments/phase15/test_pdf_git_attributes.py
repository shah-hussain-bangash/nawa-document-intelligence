"""Verify that the repository PDF fixture rule preserves bytes on checkout."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ATTRIBUTES = Path(os.environ.get('NAWA_ATTRIBUTES_PATH',
    str(Path(__file__).resolve().parents[2] / '.gitattributes')))

class PdfGitAttributesTests(unittest.TestCase):
    def test_pdf_bytes_survive_windows_style_checkout(self):
        with tempfile.TemporaryDirectory(prefix='nawa_pdf_attributes_') as directory:
            repo = Path(directory)
            def git(*args):
                return subprocess.run(['git', '-c', 'core.autocrlf=true', *args], cwd=repo,
                    check=True, capture_output=True).stdout
            git('init', '-q')
            (repo / '.gitattributes').write_bytes(ATTRIBUTES.read_bytes())
            pdf = repo / 'demo' / 'samples' / 'pdf' / 'fixture.pdf'
            pdf.parent.mkdir(parents=True)
            original = b'%PDF-1.3\nSynthetic sample only\n%%EOF\n'
            pdf.write_bytes(original)
            git('add', '.gitattributes', 'demo/samples/pdf/fixture.pdf')
            self.assertEqual(git('show', ':demo/samples/pdf/fixture.pdf'), original)
            pdf.unlink()
            git('checkout', '--', 'demo/samples/pdf/fixture.pdf')
            self.assertEqual(pdf.read_bytes(), original)

if __name__ == '__main__':
    unittest.main()
