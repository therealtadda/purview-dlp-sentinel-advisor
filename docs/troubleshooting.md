# Troubleshooting the customer POC

Use the approved portal and private support channel for tenant diagnostics.
Never paste credentials, tenant or workspace IDs, alert IDs, personal data,
raw query results, or full tool traces into an issue, Copilot, or this
repository. Do not widen a query or grant permissions to make a test pass.

| Symptom | Safe checks and next action |
|---|---|
| `copilot` is unavailable or `/login` fails | Confirm the documented install method, `copilot --version`, subscription, and organization policy. GitHub sign-in is separate from Sentinel Entra sign-in. Contact the Copilot administrator; don't paste authentication tokens. |
| A server appears in disconnected mode | Run `copilot mcp list` in the intended isolated profile and folder; inspect user, workspace and plugin sources. Stop if any tenant server is configured. `--disable-builtin-mcps` does not disable custom servers. |
| Lab Entra sign-in is absent, fails, or selects an unexpected identity | Stop before querying. Verify lab profile, tenant and client policy with the administrator. CLI/Sentinel Entra compatibility is unverified; use the documented VS Code lab option or disconnected workflow. Do not add bearer tokens to files or command history. |
| `query_lake` missing or unexpected tools are listed | Confirm the official endpoint and tool filter in the isolated lab profile. Do not approve other tools. If filtering cannot be confirmed, remove the connection and use the disconnected workflow. |
| Permission denied | Record denial as **denied**, not zero or missing. Check the intended identity, approved workspace, customer role and published permission model with an administrator. Do not grant broad roles merely to pass. |
| Table or column not found | Confirm data lake onboarding, selected source/destination workspace, connector, table tier and current schema in the portal. The `CloudAppEvents` timestamp mapping may differ. Keep the affected feed unavailable until validated. |
| A query returns no alert | Verify the case-approved UTC window, `SystemAlertId` versus `VendorOriginalId`, exact validated provenance, workspace, connector and time picker. Stop if ambiguous; do not substitute title or expand the time range automatically. |
| An aggregate is zero, missing, stale, partial or disabled | Only a complete row with `Volume=zero` is zero. Compare the approved source register, sealed weeks and ledger with the [state table](sentinel.md#read-and-interpret). Do not derive zero from an empty read or a failed job. |
| Alert linkage is `unverified` or `withheld` | Check the documented key, strictly bounded event time, complete connector coverage and controlled match. `withheld` does not establish a match or its absence. Never expose partition counts. |
| Job produces no row | Check the example week is a Monday, the Wednesday UTC seal cutoff has passed, `approved_for_release` is set only after approval, and source readiness is understood. Missing table and denied access are errors, not partial rows. |
| Duplicate row or unknown job outcome | Stop publication. Reconcile the serialized ledger, job status and destination with the authorized operator. A one-time job edit can rerun it; do not edit or retry until a prior write is definitively absent. Escalate duplicates privately. |
| Wrong output schema, malformed band, or unexpected column | Withhold the result. Compare destination schema, five-column projection and source adapter to the [contract](sentinel.md#read-and-interpret); obtain owner review before changing a series. Do not copy unexpected data to Copilot. |
| KQL syntax, semantic or fixture failure | Reassemble shared functions and one fragment in order, verify the workspace's actual schema and compare the synthetic test to [functional testing](poc-validation.md). Offline structural tests are not a KQL parser or execution engine. |
| Copilot invents a count, root cause or policy action | Discard the answer; use the documented prompt with approved bands and explicitly request uncertainty. Human review is required. Do not let the model execute queries or policy changes to resolve uncertainty. |

Report software defects through the repository's approved public or private
reporting path only after redacting customer-specific content. The public
repository owner must enable and verify a confidential reporting route
before publication; see [public-release readiness](public-release.md).
