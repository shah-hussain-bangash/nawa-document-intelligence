import copy
import unittest

from synthetic_dataset_manifest import validate_manifest


class SyntheticDatasetManifestTests(unittest.TestCase):
    def setUp(self):
        self.sample = {'sample_id': 'page-a', 'source_id': 'document-a',
                       'content_sha256': 'a' * 64, 'split': 'development',
                       'language': 'ar', 'creator_id': 'creator-a',
                       'reviewer_id': 'reviewer-b', 'license_ref': 'synthetic-license'}
        self.manifest = {'scope': 'synthetic-only', 'samples': [self.sample]}

    def test_valid_metadata_is_not_quality_approval(self):
        result = validate_manifest(self.manifest)
        self.assertEqual(result['status'], 'metadata_valid_only')
        self.assertTrue(result['human_review_required'])

    def test_rejects_empty_or_non_synthetic_scope(self):
        for value in ({'scope': 'synthetic-only', 'samples': []},
                      {'scope': 'real', 'samples': [self.sample]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_manifest(value)

    def test_requires_distinct_declared_reviewer_and_valid_hash(self):
        for field, value in [('reviewer_id', 'creator-a'), ('content_sha256', 'not-a-hash'),
                             ('license_ref', ''), ('split', []), ('language', 'fr')]:
            sample = dict(self.sample, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_manifest({'scope': 'synthetic-only', 'samples': [sample]})

    def test_rejects_duplicate_sample_id(self):
        second = dict(self.sample, source_id='document-b', content_sha256='b' * 64)
        with self.assertRaises(ValueError):
            validate_manifest({'scope': 'synthetic-only', 'samples': [self.sample, second]})

    def test_rejects_source_or_hash_across_splits(self):
        for source, digest in [('document-a', 'b' * 64), ('document-b', 'a' * 64)]:
            second = dict(self.sample, sample_id='page-b', source_id=source,
                          content_sha256=digest, split='evaluation')
            with self.subTest(source=source), self.assertRaises(ValueError):
                validate_manifest({'scope': 'synthetic-only', 'samples': [self.sample, second]})

    def test_pages_from_same_source_may_share_split(self):
        second = dict(self.sample, sample_id='page-b', content_sha256='b' * 64)
        result = validate_manifest({'scope': 'synthetic-only', 'samples': [self.sample, second]})
        self.assertEqual(result['sample_count'], 2)

    def test_rejects_unexpected_fields_and_does_not_mutate_input(self):
        original = copy.deepcopy(self.manifest)
        validate_manifest(self.manifest)
        self.assertEqual(self.manifest, original)
        self.sample['ground_truth'] = 'private text is not accepted here'
        with self.assertRaises(ValueError):
            validate_manifest(self.manifest)


if __name__ == '__main__':
    unittest.main()
