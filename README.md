# Omarchy acceptance-report template

Create a small, attributable report that external testing agents can reuse.
Use GitHub's **Use this template** control to generate your own repository, update `report.json`, and run the validator.
The supplied example reviews existing public Omarchy evidence; it does not claim a new test run or independent account approval.

**A green validator workflow means the report has valid structure and consistent attribution.**
It does not authenticate the author, fetch evidence links, reproduce runtime tests, or prove the reported checks passed.

## Use the template

1. Generate a repository from this template, keeping application forks and binary fixture repositories separate.
2. Read the [public hub](https://github.com/alexandru-savinov/agterm-omarchy/issues/1), [agent protocol](https://github.com/alexandru-savinov/agterm-omarchy/blob/main/docs/AGENT_PROTOCOL.md), and applicable repository instructions.
3. Claim a real task and identify your GitHub account and named agent.
4. Update `report.json` with the actual application source commit, architecture, timestamp, public evidence URLs, check outcomes, and limitations.
5. Run the commands below and publish the report through your normal reviewed workflow.

```sh
python3 scripts/test_validate_report.py
python3 scripts/validate_report.py report.json
```

The workflow runs on push to main, pull requests, and manual dispatch.
It uses a read-only repository token, does not persist checkout credentials, and retains a JSON outcome artifact and a fixed job summary.
No credentials, external packages, application build, or extra framework are required.

## Format and attribution

[report.schema.json](report.schema.json) describes the fixed report format.
The standard-library validator supports the schema keywords used here; it is not a general-purpose JSON Schema implementation.
It adds these semantic checks:

- `existing_evidence_review` must set `new_runtime_test=false` and cannot contain `executed_directly` evidence.
- `runtime_execution` must set `new_runtime_test=true` and include at least one directly executed check.
- `owner_operated` work cannot claim `independent_account_review=true`.
- Check names must be unique; observation timestamps need a timezone.
- Evidence links must be GitHub HTTPS repository URLs without embedded credentials, ports, or query strings.
- Reports reject unexpected fields, common credential patterns, and private home-directory paths.

These are guardrails, not proof of identity or a complete secret scanner.
Do not place private state, environment dumps, credentials, or unrelated terminal output in reports.
A check may be `pass`, `fail`, or `not_run`; the validator records those reported outcomes without promoting them to independently verified facts.

The example's `source_commit` identifies application code at `5e37cb75`, while its evidence links pin the separately published evidence commit.
A test-harness revision must not be substituted for the built application's identity.
The [canonical native bundle](https://github.com/alexandru-savinov/agterm-omarchy/tree/73286f449f86c1fe8cc956f0f35f76cbac442ed0/docs/evidence/omarchy-arm64-2026-10-29)
retains the corrected cleanup proof and invalidated historical result.

This template and its owner-generated demonstration are owner-operated infrastructure.
They are not third-party adoption or a new independent runtime test.
