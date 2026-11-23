"""Field-level accounting for synthetic labels and predictions, not a benchmark."""

FIELDS = ('supplier', 'reference', 'currency', 'subtotal', 'vat_rate', 'vat_amount', 'total')
LANGUAGES = ('ar', 'en', 'mixed')


def _valid_value(value):
    return value is None or (isinstance(value, str) and bool(value.strip()) and len(value) <= 256)


def score_cases(cases, *, normalization_policy):
    """Count exact canonical matches; caller supplies normalization and labels.

    A missing expected field is represented explicitly by None. A missing
    prediction is None or an omitted key. Results contain no source text.
    """
    if (not isinstance(cases, list) or not 1 <= len(cases) <= 10000
            or not isinstance(normalization_policy, str) or not normalization_policy.strip()
            or len(normalization_policy) > 100):
        raise ValueError('Invalid synthetic field evaluation')
    blank = lambda:{'expected':0, 'correct':0, 'missing':0, 'incorrect':0,
                    'expected_absent':0, 'spurious':0}
    groups = {language:{field:blank() for field in FIELDS} for language in LANGUAGES}
    ids, draft = set(), 0
    required = {'id','language','source_type','label_status','expected','predicted'}
    for case in cases:
        if (not isinstance(case, dict) or set(case) != required
                or not isinstance(case['id'], str) or not case['id'].strip() or len(case['id']) > 64
                or case['id'] in ids or case['language'] not in LANGUAGES
                or case['source_type'] != 'synthetic' or case['label_status'] not in ('draft','reviewed')
                or not isinstance(case['expected'], dict) or set(case['expected']) != set(FIELDS)
                or not isinstance(case['predicted'], dict) or not set(case['predicted']) <= set(FIELDS)
                or not all(_valid_value(v) for v in case['expected'].values())
                or not all(_valid_value(v) for v in case['predicted'].values())):
            raise ValueError('Invalid synthetic field case')
        ids.add(case['id'])
        draft += case['label_status'] == 'draft'
        for field in FIELDS:
            expected, actual = case['expected'][field], case['predicted'].get(field)
            row = groups[case['language']][field]
            if expected is None:
                row['expected_absent'] += 1
                row['spurious'] += actual is not None
            else:
                row['expected'] += 1
                if actual is None:
                    row['missing'] += 1
                elif actual == expected:
                    row['correct'] += 1
                else:
                    row['incorrect'] += 1
    for language in LANGUAGES:
        for row in groups[language].values():
            row['exact_match_rate'] = row['correct'] / row['expected'] if row['expected'] else None
    return {'scope':'Synthetic, self-declared labels; not independent quality evidence.',
            'normalization_policy':normalization_policy, 'case_count':len(cases),
            'cases_with_draft_labels':draft, 'by_language_and_field':groups}
