# POC functional testing and acceptance

This procedure separates offline checks, synthetic KQL execution, and
customer-side acceptance. Do not copy real data, identifiers, workspace
names, outputs, credentials, or connector configuration into this repository.
The customer owns tenant access, approvals, and any evidence stored in its
approved private system. Do not run live tenant tests in CI.

## 1. Offline checks

From the repository root, run Python 3.12 or later:

```text
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
```

Both commands must exit zero; the first prints `OK`. The standard-library
tests check fixture/prompt consistency, default publication guards, the
documented output projection and selected query text, lab JSON, and local
link targets. A Python simulation also checks the synthetic case rows; it
does not run the KQL template. These **offline checks** do not parse or execute
KQL, evaluate privacy for a tenant, call Copilot, or verify cloud permissions.
`git diff --check` checks the current unstaged patch, not customer data.
For a staged change use `git diff --cached --check`; for a PR use
`git diff --check <base-commit> HEAD`.

No KQL parser or query execution engine is bundled. If a supported parser
is used independently, record its name, version and result separately;
syntax success is not a functional execution result.

## 2. Synthetic KQL assertions

An authorized operator may perform this step in a **synthetic-only**
workspace in the Defender portal. If none is available, mark it **not run**.
Choose an editor, not a publishing job:

1. Paste the complete contents of
   [weekly-functions.kql](../ops/sentinel/weekly-functions.kql), followed
   by [weekly-fixtures.kql](../ops/sentinel/weekly-fixtures.kql), and run
   the combined query. Expect **16 rows**, each with `Test` and
   `Passed=true`. Check every row; a query error, missing test, null, false,
   or a different count is a failure, not a pass.
2. The assertions cover band edges, the Wednesday UTC release cutoff,
   duplicate events, missing IDs, provenance, alert copies and conflicting
   latest values, strict correlation windows, absent approvals, incomplete
   coverage and missing/disabled states. Inspect the synthetic test name
   for a failure; do not infer real connector health from fixture success.
3. Perform the [synthetic investigation exercise](sentinel.md#synthetic-investigation-exercise).
   Verify the matching row, wrong ID/source and exclusive end boundary,
   blank inputs, and a window over 24 hours. These rows are synthetic and
   must never be appended to the weekly evidence table.
4. In disconnected Copilot, use the [synthetic analysis prompt](analysis-prompts.md#try-it-without-mcp).
   Confirm it identifies `10-19` to `20-49`, missing labels, and partial
   alerts without estimating exact totals or inventing causes. Use the
   [case prompt](analysis-prompts.md#draft-a-case-investigation) with an
   IRM scenario and confirm it routes to Purview without tool calls.
   Model responses are variable: an analyst reviews each result against
   these criteria; a prompt is not an authorization control.

## 3. Optional synthetic publication and MCP lab

Only after confirming every surface the lab identity can reach contains
synthetic data or approved aggregates, use the
[isolated lab steps](../README.md#option-b-query-the-isolated-lab-via-sentinel-mcp).
Preview the synthetic seed; create a **new** lab table once. Expect five
contract-valid rows across two weeks. Confirm the table name and exactly
five evidence columns in the read projection. Record in the private lab
ledger who submitted the job and whether it succeeded.

To exercise duplicate prevention, reserve a synthetic `(week, source)`
in the serialized ledger, and demonstrate that a second submission is
blocked by the operator procedure. Simulate an uncertain write in the
ledger without resubmitting; reconciliation of job and destination state
must precede any retry. The native table itself does **not** enforce
uniqueness. Do not deliberately publish duplicate rows into a shared table.

If CLI-to-Sentinel sign-in and tool filtering are available, follow the
lab instructions, manually inspect the single requested workspace and
query, and expect those same five rows. Record the client version, observed
sign-in result, and whether the tool filter was honored in the private
lab record. Visibility of the promoted analytics-tier table through
`query_lake` is also unverified; use the portal if the table is unavailable.
A failed, unavailable, or skipped connection is **not run** or
failed as appropriate; it does not block the disconnected portal POC. Do
not infer production permissions from a successful lab connection.

## 4. Customer POC acceptance and production gate

Before customer data is used, customer owners must approve data sharing
into Copilot, roles, case handling, retention, cost and incident escalation.
An authorized operator validates source schema and connector health in the
portal and verifies the exact DLP provenance tuple with a controlled match.
Confirm the source workspace, ingestion lag, stable event/alert deduplication
and week assignment, and the complete event join window. A source that
cannot be validated is **partial or unavailable**, not zero.

In the customer-approved private record, note each item as pass, fail, or
not run, including client and source versions, operator role, time, and
non-sensitive outcome:

| Acceptance | Required result |
|---|---|
| Offline checks | Both commands in section 1 pass. |
| Synthetic KQL | All 16 weekly assertions pass and the investigation exercise behaves as specified, or is explicitly not run. |
| Aggregate workflow | Exactly one contract-valid row per approved source/week, ledger sealed, and Copilot interpretation uses only approved bands and coverage. |
| Investigation | Authorized analyst locates one known DLP alert, checks `SystemAlertId` and provenance, and runs the bounded portal query; raw results remain in the portal/case system. |
| IRM request | No IRM data is fetched by the advisor; analyst uses authorized native Purview. |
| Production MCP | **No-go** unless each applicable [permission gate](plan.md#2-production-permission-gate) is satisfied and customer Security/Privacy owners explicitly approve the data path. |

For either prospective production gate, a separate operator must confirm
that harmless raw, alternate-workspace, federated and catalog canaries
exist and a control identity can see them. With the actual proposed MCP
identity, test permitted in-scope access and denial of out-of-scope
access both with and without explicit workspace selection. An empty
successful result, nonexistent canary, timeout, malformed query, or lack
of a test is not a denial. Stop and retain portal-only access if any
result is inconclusive. Prompts and tool filters are not access controls.

See [troubleshooting](troubleshooting.md) for safe next steps. A POC
handoff may report synthetic KQL and live connector checks as not run;
do not describe them as passed.
