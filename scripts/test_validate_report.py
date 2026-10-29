import copy
import json
from pathlib import Path
import unittest
from validate_report import InvalidReport, validate

BASE = json.loads((Path(__file__).resolve().parents[1] / 'report.json').read_text())


class ReportTests(unittest.TestCase):
    def test_attributed_example_passes_without_new_execution(self):
        result = validate(BASE)
        self.assertTrue(result['validator_success'])
        self.assertFalse(result['new_runtime_test'])

    def test_rejects_contradictory_execution_or_independence(self):
        for field in ('new_runtime_test', 'independent_account_review'):
            with self.subTest(field=field):
                report = copy.deepcopy(BASE)
                report['attribution'][field] = True
                with self.assertRaises(InvalidReport):
                    validate(report)

    def test_rejects_direct_execution_in_evidence_review(self):
        report = copy.deepcopy(BASE)
        report['checks'][0]['evidence_kind'] = 'executed_directly'
        with self.assertRaises(InvalidReport):
            validate(report)

    def test_rejects_private_or_credential_urls(self):
        for url in ('file:///tmp/report', 'http://github.com/a/b', 'https://user:pass@github.com/a/b', 'https://github.com/a/b?token=secret'):
            with self.subTest(url=url):
                report = copy.deepcopy(BASE)
                report['checks'][0]['evidence_url'] = url
                with self.assertRaises(InvalidReport):
                    validate(report)

    def test_rejects_unknown_fields_booleans_as_integers_and_duplicate_checks(self):
        for change in ('unknown', 'bool', 'duplicate'):
            with self.subTest(change=change):
                report = copy.deepcopy(BASE)
                if change == 'unknown':
                    report['command'] = 'echo untrusted'
                elif change == 'bool':
                    report['schema_version'] = True
                else:
                    report['checks'].append(copy.deepcopy(report['checks'][0]))
                with self.assertRaises(InvalidReport):
                    validate(report)

    def test_rejects_private_paths_and_naive_timestamps(self):
        for field, value in [('limitations', ['/home/private-user/session']), ('observed_at', '2026-10-29T12:00:00')]:
            with self.subTest(field=field):
                report = copy.deepcopy(BASE)
                report[field] = value
                with self.assertRaises(InvalidReport):
                    validate(report)


if __name__ == '__main__':
    unittest.main()
