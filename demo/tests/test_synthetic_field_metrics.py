"""Accounting tests for synthetic field scores; not independently reviewed labels."""
from copy import deepcopy
import unittest

from nawa_demo.synthetic_field_metrics import FIELDS, score_cases


def case(identifier, language, *, expected=None, predicted=None, label_status='draft'):
    labels = {name:None for name in FIELDS}
    labels.update(expected or {})
    return {'id':identifier, 'language':language, 'source_type':'synthetic',
            'label_status':label_status, 'expected':labels, 'predicted':predicted or {}}


class SyntheticFieldMetricTests(unittest.TestCase):
    def test_distinguishes_correct_missing_incorrect_and_spurious(self):
        examples = [case('en1','en',expected={'subtotal':'1000.00','total':'1050.00'},
                         predicted={'subtotal':'1000.00','total':'1051.00','vat_amount':'50.00'}),
                    case('ar1','ar',expected={'vat_amount':'45.00'},predicted={},label_status='reviewed')]
        report = score_cases(examples, normalization_policy='synthetic-canonical-v1')
        english = report['by_language_and_field']['en']
        arabic = report['by_language_and_field']['ar']
        self.assertEqual((english['subtotal']['expected'],english['subtotal']['correct'],
                          english['subtotal']['exact_match_rate']), (1,1,1.0))
        self.assertEqual((english['total']['incorrect'],english['total']['exact_match_rate']), (1,0.0))
        self.assertEqual((english['vat_amount']['expected_absent'],english['vat_amount']['spurious']), (1,1))
        self.assertEqual((arabic['vat_amount']['expected'],arabic['vat_amount']['missing']), (1,1))
        self.assertIsNone(report['by_language_and_field']['mixed']['total']['exact_match_rate'])
        self.assertEqual(report['cases_with_draft_labels'], 1)
        self.assertIn('not independent', report['scope'])

    def test_does_not_silently_normalize_amounts(self):
        example = case('x','ar',expected={'total':'945.00'},predicted={'total':'٩٤٥٫٠٠'})
        result = score_cases([example], normalization_policy='provided-by-caller')
        self.assertEqual(result['by_language_and_field']['ar']['total']['incorrect'], 1)

    def test_rejects_unknown_fields_duplicate_ids_and_unlabelled_absence(self):
        base = case('x','en',expected={'total':'1.00'},predicted={'total':'1.00'})
        for change in ('unknown','duplicate','omitted_reference','non_synthetic','bad_value'):
            with self.subTest(change=change):
                cases = [deepcopy(base)]
                if change == 'unknown': cases[0]['predicted']['unexpected'] = 'x'
                if change == 'duplicate': cases.append(deepcopy(base))
                if change == 'omitted_reference': del cases[0]['expected']['reference']
                if change == 'non_synthetic': cases[0]['source_type'] = 'real'
                if change == 'bad_value': cases[0]['predicted']['total'] = 1.0
                with self.assertRaises(ValueError):
                    score_cases(cases, normalization_policy='test')

    def test_requires_a_named_normalization_policy(self):
        with self.assertRaises(ValueError):
            score_cases([case('x','en')], normalization_policy=' ')


if __name__ == '__main__':
    unittest.main()
