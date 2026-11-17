import unittest
from types import SimpleNamespace

from semantic_probe import assess, validate_response


class SemanticProbeTests(unittest.TestCase):
    def test_labels_are_withheld_and_outcomes_are_counted(self):
        cases = [{'id':'one', 'claim':'claim', 'passage_id':'p', 'supported':False,
                  'category':'contradiction'}]
        def fake(inputs):
            self.assertEqual(inputs, [{'id':'case-001','claim':'claim','evidence':'source'}])
            return {'results':[{'id':'case-001','verdict':'supported'}]}
        result = assess(cases, {'p':SimpleNamespace(text='source')}, fake)
        self.assertEqual(result['confusion']['fp'], 1)

    def test_rejects_missing_duplicate_and_unknown_verdicts(self):
        with self.assertRaises(ValueError):
            validate_response({'results':[]}, {'one'})
        with self.assertRaises(ValueError):
            validate_response({'results':[{'id':'one','verdict':'supported'}]*2}, {'one'})
        with self.assertRaises(ValueError):
            validate_response({'results':[{'id':'one','verdict':'maybe'}]}, {'one'})


if __name__ == '__main__':
    unittest.main()

