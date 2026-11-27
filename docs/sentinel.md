# Sentinel operator runbook

## Publish a sealed week

Use the [Defender portal's native KQL jobs][kql-jobs]. Only an authorized
operator runs source queries. Confirm data lake onboarding, feed availability
and permissions; the [Sentinel role reference][roles] distinguishes read
roles from roles that publish job results. Keep the publisher separate from
the analyst and never enable MCP for the publisher. Confirm applicable
licensing, data location, customer retention policy and query/job/storage
charges with the customer before starting; this repository cannot determine
the cost or grant the required permissions.

1. Select the single approved source workspace in **Microsoft Sentinel >
   Data lake exploration**. Do not select multiple workspaces: the editor
   can union same-name tables across the selection. Check that the time
   picker does not clip the explicit query window, including the alert
   lookaround.
2. Reserve a `(WeekStart, Source)` in a private, serialized operator ledger.
   Record the intended scope, connector health and lag, coverage, approval,
   job status and whether a destination row is visible. The same source
   scope and query definition apply throughout the series. Use only a
   Monday 00:00 UTC for `week`. The earliest seal is Wednesday 00:00 UTC
   after the week closes; wait longer if data is delayed. Do not infer
   completeness from nonempty rows. If coverage is known incomplete, use
   `ready=false` to emit a partial row if publication is approved; if the
   table is absent or access is denied, do not manufacture a row.
3. Paste [weekly-functions.kql](../ops/sentinel/weekly-functions.kql)
   followed by **one** job fragment below in the same query. Replace the
   example Monday and review readiness locally. `approved_for_release=false`
   returns no release rows. After coverage and disclosure review set it to
   `true` in the operator's copy and preview the one-row aggregate in the
   portal. Never publish or copy intermediate data. A small band may still
   disclose information about a concentrated cohort; leave `ready=false`
   or do not publish when even the band is unsafe.
4. Choose **Create job**, select the approved destination workspace and
   **One time**. Use an analytics-tier custom table and the base name
   `AdvisorWeeklyEvidenceV1` when creating it; the portal adds `_KQL_CL`.
   Check the resulting name and schema. Creation can require workspace
   permission for the data lake managed identity: Microsoft documents
   Log Analytics Contributor on the destination Log Analytics workspace
   for creating new analytics-tier custom tables. The customer's administrator
   must review and assign any approved permissions; follow the [native job
   prerequisites][kql-jobs]. Append subsequent jobs to that existing table.
   Editing a one-time job can trigger another execution. Do not edit,
   automatically retry, schedule recurring writes, or resubmit an uncertain
   run. This table does not enforce uniqueness.
5. Before any write, confirm no row and no in-flight or uncertain job exists
   for that key. After completion, confirm exactly one contract-valid row;
   only then seal the ledger record and release the band. Retry only after
   a definitive failure without a write, reconciled against both job and
   destination state. On a duplicate, unexpected schema or unknown write
   outcome, stop release and escalate privately. Never silently deduplicate,
   amend, or issue overlapping/supplemental releases.

### Source jobs

| Fragment | Operator acceptance before setting `ready=true` |
|---|---|
| [DLP rule matches](../ops/sentinel/job-dlp.kql) | Validate `DlpRuleMatch`, `ReportId` uniqueness, and the event timestamp in the authorized Sentinel workspace. The [Defender schema][cloud-apps] uses `Timestamp`; the Sentinel adapter assumes `TimeGenerated`. Validate the connector mapping rather than substituting a column blindly. This count measures rule matches, not all DLP activity. |
| [Label/protection context](../ops/sentinel/job-labels.kql) | Validate `Id` and the selected documented [audit activities][purview-activity] against the [table schema][purview-schema]. These label-change and policy-match signals are contextual, not proof of encryption. Do not export label names, protection metadata, or actor data. |
| [Purview alert overlay](../ops/sentinel/job-alerts.kql) | Match a fresh Defender Purview DLP alert to Sentinel and privately record the exact connector-emitted vendor/product/provider tuple. Prove the tuple excludes unrelated alerts; an empty or ambiguous allowlist cannot support a complete release. Never match by title. Verify a `SystemAlertId` has a single publication week across connector copies. If not, stop until an approved stable canonical assignment can be verified without rewriting prior weeks. |

Use `link_ready=true` only after a controlled match confirms
the [documented DLP correlation][dlp-sentinel] and full CloudAppEvents
coverage across the bounded lookaround. `AlertType` must equal
`RawEventData.Data.cid`; `CreationTime` must be strictly inside the alert
window. The query confines alert windows, source timestamps and payload
timestamps to the interval from seven days before week start to eight days
after it (exclusive upper limit for events). It collapses exact copies,
counts each alert once, and treats conflicting latest versions as unverified
linkage. The label feed is not joined. An unverified link does not suppress
verified alert volume.

`DataSecurityEvents` is **disabled by default**. No raw job or fallback is
provided. Only an independently approved existing upstream aggregate can be
considered, and it must meet the same disclosure, schema and single-release
requirements. Do not query or stage IRM or user-level data.

## Read and interpret

Use [read-weekly.kql](../ops/sentinel/read-weekly.kql) in the Defender
portal's Advanced hunting KQL editor for the approved analytics-tier
destination and a fixed range of sealed UTC weeks. Update the table name
only if it differs from the verified native
name. Ensure the UI time filter does not hide rows based on when they were
written. Never reference raw tables in the read query.

| Column | Type | Allowed values |
|---|---|---|
| `WeekStart` | `datetime` | Monday 00:00 UTC |
| `Source` | `string` | `CloudAppEvents`, `MicrosoftPurviewInformationProtection`, `SecurityAlert`, optionally `DataSecurityEvents` |
| `Coverage` | `string` | `complete` or `partial` |
| `Volume` | `string` | `zero`, `suppressed` (1–9), `10-19`, `20-49`, `50-99`, `100+`; blank for partial |
| `Correlation` | `string` | On a complete alert row: `observed`, `withheld`, or `unverified`; otherwise `not_applicable` for complete or blank for partial |

`observed` requires at least 10 linked alerts and 10 others. `withheld`
does not attest that any match exists. Never release partition counts.
Only the five projected columns are approved for disclosure review;
do not include platform-managed timestamps, workspace metadata, or any
additional properties. Reject malformed, out-of-scope or duplicate rows.

Use the approved feed register and expected publish cadence to record
status separately from the table:

| State | Interpretation |
|---|---|
| Zero | A valid `complete` row with `Volume=zero`. |
| Missing | A successful read has no row for a requested enabled source/week. |
| Stale | A newer release is overdue, and the latest available row is from an older week. Show the older week explicitly, not as current evidence. |
| Partial | The published row says `partial`; it has no band or link evidence. |
| Denied | The reader cannot access the destination or required metadata. Do not recast authorization errors as missing evidence. |
| Disabled | The feed register says the source is off; do not query or report it as zero. |

Other read errors are failures, not any of these states. Don't sum feed
volumes, reconstruct exact totals, or use bands to infer impact on a person.
Review raw evidence only in the authorized portals.

## Event investigation

Use the [case drafting prompt](analysis-prompts.md#draft-a-case-investigation)
in a disconnected Copilot session. Before any fetch, record the case
reference, purpose, investigator authorization, approved source and time
range in the access-controlled case system. Do not copy the case reference
or tenant details into Copilot.

### Find the Sentinel alert ID

The template's `alert_id` expects **`SecurityAlert.SystemAlertId`**, the
internal Sentinel alert ID. Do not use the incident number, alert name,
`AlertType`, or the originating product's `VendorOriginalId` in its place.
See the [Sentinel alert schema][alert-schema] for the distinction.

1. In the approved workspace, open the incident's **Alerts** list and
   select the specific Microsoft Purview DLP alert. Check its source and
   timestamp against the case. If the matching `SecurityAlert` record
   shows `SystemAlertId`, copy that exact value.
2. If you have only the originating alert ID from Defender, match it
   against `VendorOriginalId` in the same workspace's `SecurityAlert`
   table. Use the known alert's case-approved time range and exact,
   verified vendor/product/provider tuple. For example, paste this lookup
   into the portal query editor and replace the example values there only:

   ```kusto
   SecurityAlert
   | where TimeGenerated >= datetime(2026-01-05T00:00:00Z)
       and TimeGenerated < datetime(2026-01-06T00:00:00Z)
   | where VendorOriginalId == "example-originating-alert-id"
       and VendorName == "example-vendor"
       and ProductName == "example-product"
       and ProviderName == "example-provider"
   | where isnotempty(SystemAlertId)
   | summarize FirstSeenUtc=min(TimeGenerated), LastSeenUtc=max(TimeGenerated) by SystemAlertId
   | take 2
   ```

3. If the lookup returns one distinct `SystemAlertId` and the timing matches
   the case, paste it into `let alert_id = "...";` in the investigation
   template. Use a UTC query window that includes the matching
   `SecurityAlert.TimeGenerated`. If there is no match or more than one
   distinct ID, stop and verify the workspace, connector, source, and time
   range; don't guess or broaden the query automatically. Keep real IDs and
   results in the authorized portal and case system, not Copilot or the repo.

### Run the investigation query

For a known Purview DLP alert, an authorized analyst can run the
[interactive alert template](../ops/sentinel/investigate-alert.kql) in the
Sentinel portal after confirming the approved source workspace and the
connector's DLP provenance tuple. Fill in the single alert ID, exact
vendor/product/provider values, and an exclusive UTC end time in the portal,
not in the repository. The template permits a window no longer than 24 hours,
returns at most 25 matching records, and omits payloads and entity details.
These query limits are not authorization controls. Use the native alert
story or related events view for authorized corroboration. No match means
only that this query returned no record within scope; verify scope and
coverage in the portal rather than broadening automatically. Keep results
and case notes in the approved native case workflow.

For Insider Risk Management (IRM), or when the source cannot be established,
do not use this template to search for user details. Route IRM requests to
[Purview's native investigation workflow][irm]. Only authorized investigators
may view unmasked details there where policy permits. Do not use Sentinel
to work around masking or denial.

### Synthetic investigation exercise

In an authorized lab query editor, replace the `let CaseAlerts = SecurityAlert;`
line in the template with [the synthetic binding](../ops/sentinel/investigate-alert-fixture.kql).
Set `alert_id` to `fixture-case-alert`, use the `fixture-vendor`,
`fixture-product`, and `fixture-provider` tuple, and use the UTC window from
`2026-01-05T00:00:00Z` to `2026-01-06T00:00:00Z` (exclusive). Expect one
`fixture-alert` row, not the other alert, wrong-provider copy, or exact
end-boundary row. With the default blank inputs or a window longer than
24 hours, expect no rows. Separately try the case drafting prompt with an
IRM scenario: expect a Purview handoff and no tool calls. Keep the synthetic
case results out of the aggregate evidence table.

## Production permission gate

**No production MCP.** Microsoft's [setup guide][mcp-start] requires Entra
Security Reader to list and invoke Sentinel MCP tools. [Sentinel
permissions][roles] grant that role read across all data lake workspaces,
and [data exploration][mcp-tools] exposes `query_lake` for arbitrary valid
KQL with results returned as-is. The aggregate table, optional workspace
argument, Azure workspace RBAC and prompts do not narrow that role.

Reconsider only with a documented, supported aggregate-only permission
model and an authorized canary test using the effective MCP identity.
Have an independent operator verify that harmless raw, alternate-workspace,
federated and catalog canaries actually exist and are visible to a control
identity. Verify the approved aggregate read succeeds and the restricted
canaries are denied or their metadata is not disclosed through either
explicit or omitted workspace selection. An empty successful query,
nonexistent table, timeout, or bad query is not a denied read. Record the
results without canary payloads. Until then use the portal only for data
access; hand Copilot only separately approved aggregate rows.

Optional **isolated synthetic lab only**: inventory all reachable workspaces,
raw and system tables, federated sources and catalog. Use the lab only if
everything reachable contains synthetic data or approved aggregates. In an
untracked lab-only VS Code workspace, follow [Microsoft's VS Code guide][mcp-vscode]:
use **MCP: Add Server > HTTP** and the [official data exploration endpoint][mcp-endpoints]
`https://sentinel.microsoft.com/mcp/data-exploration`. Use only the lab
identity, and use **Configure Tools** to select only `query_lake` for
analysis (catalog tools only for separately controlled canary validation).
The collection can expose additional tools by default; do not use it if the
client cannot deselect entity/graph or other unrelated tools. Don't add
triage, custom tools or write capabilities, or commit the client settings.
Tool selection is a lab workflow guard, not an authorization boundary.
Remove the lab configuration when done. A lab pass does not clear
production access.

For the GitHub Copilot Chat walkthrough and synthetic seed fixture, see the
[lab setup](../README.md#option-b-query-the-isolated-lab-via-sentinel-mcp),
which also documents the Copilot CLI trial. A working connection is not
proof that production data is safe to expose. The
[investigation gate](plan.md#2-production-permission-gate) additionally
requires enforceable case scope, separate access, auditability, and written
approval for the Copilot data path before any non-IRM record-level pilot.

## Manual Defender alert tuning

[Microsoft's DLP guide][dlp-defender] notes that the built-in DLP alert tuning
rule can route signals to `BehaviorInfo` and `BehaviorEntities` instead of
alerts. Only an authorized operator, with change approval, should test
disabling that specific rule in **Settings > Microsoft Defender XDR >
Alert tuning**. Before a pilot verify Purview alert generation, connector
health and expected triage load. Generate a fresh controlled match, filter
**Service/detection sources > Microsoft Data Loss Prevention**, then verify
the Sentinel alert and corresponding event in the portal. Re-enable the
same rule to roll back and verify volumes. No historical backfill is
assumed. Behaviors alone cannot establish complete or zero alert coverage.

## Validation and retired coverage

For an authorized synthetic-only run, paste the shared functions followed
by [weekly-fixtures.kql](../ops/sentinel/weekly-fixtures.kql) in an editor,
not into a publishing job. Expect 16 result rows and all `Passed=true`.
Parser or structural checks alone do not execute the assertions. Source
schema, connector timing and provenance, destination/append semantics,
retry reconciliation and effective permissions need separate operator tests.

The retired runtime's Graph audit queries, user reachability and risk,
SharePoint/Exchange inventory enrichment, and Purview policy/rule, sensitive
information type and Activity/Content Explorer tooling are not replaced.
Use approved native portal workflows if necessary; this edition neither
provides equivalent coverage nor permits raw exports to Copilot.

[kql-jobs]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-jobs
[roles]: https://learn.microsoft.com/en-us/azure/sentinel/roles
[cloud-apps]: https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-cloudappevents-table
[purview-activity]: https://learn.microsoft.com/en-us/azure/sentinel/microsoft-purview-record-types-activities
[purview-schema]: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/microsoftpurviewinformationprotection
[dlp-sentinel]: https://learn.microsoft.com/en-us/defender-xdr/dlp-investigate-alerts-sentinel
[alert-schema]: https://learn.microsoft.com/en-us/azure/sentinel/security-alert-schema
[dlp-defender]: https://learn.microsoft.com/en-us/defender-xdr/dlp-investigate-alerts-defender
[mcp-start]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-get-started
[mcp-tools]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-data-exploration-tool
[mcp-vscode]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-use-tool-visual-studio-code
[mcp-endpoints]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-tools-overview
[irm]: https://learn.microsoft.com/en-us/purview/insider-risk-management-activities
