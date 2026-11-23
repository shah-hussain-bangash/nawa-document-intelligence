import unittest

from injection_probe import prepare_cases


class InjectionProbeTests(unittest.TestCase):
    def test_prepares_evidence_without_exposing_labels_as_evidence(self):
        raw = [{'id':'x','category':'attack','claim':'claim','evidence':'source','supported':False}]
        cases, corpus = prepare_cases(raw)
        self.assertEqual(cases[0]['supported'], False)
        self.assertEqual(corpus['x'].text, 'source')
        with self.assertRaises(ValueError):
            prepare_cases(raw + raw)


if __name__ == '__main__':
    unittest.main()

