#!/usr/bin/env python3
"""Validate this repository's fixed report schema and attribution rules; never fetch URLs."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'report.schema.json').read_text())


class InvalidReport(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidReport(message)


def shape(value, rule, path='report'):
    kind = rule['type']
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool}
    require(type(value) is types[kind], path + ': invalid type')
    if 'enum' in rule:
        require(value in rule['enum'], path + ': invalid choice')
    if kind == 'object':
        require(set(value) == set(rule['required']), path + ': missing or unknown fields')
        for key, child in rule['properties'].items():
            shape(value[key], child, path + '.' + key)
    elif kind == 'array':
        require(rule.get('minItems', 0) <= len(value) <= rule.get('maxItems', 100), path + ': invalid item count')
        for index, child in enumerate(value):
            shape(child, rule['items'], path + '[' + str(index) + ']')
    elif kind == 'string':
        require(rule.get('minLength', 0) <= len(value) <= rule.get('maxLength', 2000), path + ': invalid length')
        if 'pattern' in rule:
            require(re.fullmatch(rule['pattern'], value) is not None, path + ': invalid format')


def github_url(value):
    url = urlsplit(value)
    require(url.scheme == 'https' and url.hostname in ('github.com', 'raw.githubusercontent.com'), 'Evidence must use a public GitHub HTTPS URL')
    require(url.username is None and url.password is None and url.port is None and not url.query, 'Credentials, query strings, and ports are forbidden in evidence URLs')
    require(len([part for part in url.path.split('/') if part]) >= 2, 'Evidence URL needs a repository path')


def validate(report):
    shape(report, SCHEMA)
    stamp = datetime.datetime.fromisoformat(report['observed_at'].replace('Z', '+00:00'))
    require(stamp.utcoffset() is not None, 'Observation timestamp needs a timezone')
    attribution = report['attribution']
    runtime = attribution['activity'] == 'runtime_execution'
    require(attribution['new_runtime_test'] == runtime, 'Activity contradicts new_runtime_test')
    require(attribution['account_relationship'] != 'owner_operated' or not attribution['independent_account_review'], 'Owner-operated work cannot claim independent account review')
    direct = any(check['evidence_kind'] == 'executed_directly' for check in report['checks'])
    require(direct == runtime, 'Activity contradicts direct-execution evidence')
    require(len({check['name'] for check in report['checks']}) == len(report['checks']), 'Check names must be unique')
    github_url(report['subject']['repository'])
    for check in report['checks']:
        github_url(check['evidence_url'])
    serialized = json.dumps(report)
    require(not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|/Users/|/home/', serialized), 'Possible credential or private local path; sanitize the report')
    return {'validator_success': True, 'report_id': report['report_id'], 'activity': attribution['activity'],
            'new_runtime_test': runtime, 'check_count': len(report['checks']),
            'reported_results': {status: sum(c['result'] == status for c in report['checks']) for status in ('pass', 'fail', 'not_run')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', nargs='?', default=str(ROOT / 'report.json'))
    args = parser.parse_args()
    output = ROOT / 'artifacts' / 'validation.json'
    output.parent.mkdir(exist_ok=True)
    try:
        with Path(args.report).open('rb') as source:
            data = source.read(65537)
        require(len(data) <= 65536, 'Report exceeds 64 KiB')
        result = validate(json.loads(data))
        result['report_sha256'] = hashlib.sha256(data).hexdigest()
        result['workflow_source_commit'] = os.environ.get('GITHUB_SHA')
        result['workflow_run_id'] = os.environ.get('GITHUB_RUN_ID')
    except (InvalidReport, ValueError, OSError):
        result = {'validator_success': False, 'error': 'Report failed format, attribution, or privacy validation; run local validation tests for the rules.'}
    output.write_text(json.dumps(result, indent=2) + '\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as summary:
            summary.write('Report validation ' + ('passed' if result['validator_success'] else 'failed') + '.\n\nThis validates report structure and attribution, not the linked runtime claims.\n')
    print('PASS: report validation' if result['validator_success'] else 'FAIL: report validation')
    return 0 if result['validator_success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
