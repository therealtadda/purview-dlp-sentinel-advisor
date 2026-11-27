# Solution plan: Purview DLP recommendations with Microsoft Sentinel

**Status:** Revised design for review, 20 November 2026. The
[operator runbook](sentinel.md) describes the shipped aggregate workflow and
synthetic lab, plus the portal-only case query workflow. Direct production
MCP access is not enabled.

## 1. Architecture and scope

Use GitHub Copilot as the analyst interface for natural-language questions.
**GitHub Copilot CLI is a target interface for both testing and production**;
there is no separate advisor executable. Analysts should use the same
workflow and query shapes in both environments. GitHub Copilot Chat in
VS Code remains the documented setup for Sentinel MCP while CLI-to-Sentinel
Entra sign-in is unverified. Separate two query classes with different
access and disclosure requirements. Use Microsoft-hosted Sentinel MCP data
exploration only where the applicable gate below is met.
There is no ADX backend, custom MCP server, custom authentication, direct Graph
or Purview API client, or PowerShell bridge in the target design.

### Event investigation

Answer case-specific questions about an alert or event: what happened, when,
and which related events corroborate it. Require an explicit investigation
mode, a case reference and purpose recorded before any fetch, an authorized
investigator, and a bounded alert or event scope. In the shipped workflow,
Copilot can help draft a query from placeholders; the analyst executes it
and views authorized record-level details in Sentinel or Defender. Do not
paste raw results into Copilot or write them to this repository. A future
read-only, case-scoped MCP path for approved non-IRM sources is conditional
on the investigation gate in section 2.

Include Insider Risk Management (IRM) in the investigation workflow as a
handoff to [native Microsoft Purview case investigation][irm-investigation].
Keep pseudonymization and access decisions in Purview; only an authorized
investigator may view unmasked details there where tenant policy permits.
This advisor must not fetch, unmask, reconstruct, or ingest IRM user data.
Sentinel access does not confer Purview case authorization. Do not fall
back to a lake table to obtain data masked or denied in Purview.

### Aggregate analysis

Answer recurring questions about control effectiveness and troubling trends:
compare complete sealed weeks within a feed, call out changes in alert bands
or coverage, and recommend a human-reviewed simulation when the evidence
supports it. More matches alone do not prove a control is effective or that
risk increased; qualify findings with coverage and known policy or connector
changes. Do not use this mode to drill down to a person or reconstruct
case-level detail.

An authorized operator runs fixed Sentinel data lake KQL jobs in Defender,
checks coverage, and publishes approved weekly aggregates to a dedicated
destination. The publisher identity is separate from analyst and MCP
identities. For production today, read the results in the portal and submit
only separately approved, contract-checked aggregate rows to Copilot when
policy permits. Keep simulation and promotion separate and human-approved;
the advisor does not change policy, alert tuning, or case state.

This design does not replace Graph membership, SharePoint/Exchange inventory,
identity-risk lookups, Purview audit queries, or Activity Explorer/Content
Explorer. There is no implemented case-mode lookup or parity promise. If needed, use
authorized native administrative workflows outside this repository; do not
copy raw results into Copilot or evidence files.

## 2. Production permission gate

**Production CLI use is distinct from production MCP access.** Analysts can
already use Copilot CLI without Sentinel MCP to analyze approved aggregates
or draft case queries from placeholders for execution in the authorized
portal. Direct production queries from the CLI are a target capability,
not an enabled or approved connection. Microsoft documents that the Microsoft Entra
**Security Reader** role is [needed to list and invoke Sentinel MCP tools][mcp-start],
and that this role can [read across all data lake workspaces][sentinel-roles].
[`query_lake`][mcp-query] takes arbitrary valid KQL and returns the result set
as-is, including raw rows when the caller can read them. A separate destination
workspace, a `workspaceId` parameter, workspace RBAC added alongside Security Reader, a
fixed example query, or a prompt is not an aggregate-only permission boundary.
Do not ship active MCP configuration.

**Aggregate gate.** Revisit only when a supported permission model confines
the effective MCP caller to the approved aggregate table and its metadata.
Verify that an approved read succeeds and that harmless canaries in raw
tables, other workspaces, federated sources, and restricted catalogs cannot
be read or discovered. Check explicit and omitted workspace selection.

**Investigation gate.** Do not reuse the aggregate session or its grants.
For any future non-IRM record-level MCP pilot, require Security and Privacy
approval for the Copilot data path (including model context, transcripts,
logging, access and retention). Require supported enforcement of the
investigator's approved source, workspace and case scope, minimum fields,
bounded time and result size, and auditable, revocable read-only access.
Verify that in-scope canaries can be retrieved and out-of-scope cases and
sources are denied, including cross-workspace, federated, and catalog access.
Do not treat a prompt, manual tool approval, or query parameter as enforcement.
If these controls cannot be demonstrated, continue native investigations.
IRM user-level queries remain outside the advisor.

For either gate, an absent canary, timeout, malformed query, or empty
successful result is not proof of denial. Record the supported permission
model and test outcomes before any production change.

**Recommended testing mode.** Use the same CLI and analyst workflow against
a separate synthetic environment with a lab identity. This validates sign-in,
client behavior, query shape and result handling without exposing real
investigation records. Testing mode is an environment and identity choice,
not a client flag or authorization boundary. The query tool can read more
than the example query, so the lab
must isolate what the identity can reach, not just where the example table
lives. Use the [official hosted data exploration collection][mcp-start] in
a supported client outside repo configuration only if all reachable data and
catalog entries are synthetic or approved aggregates. A production workspace
on its own is not isolation. A passing lab is not proof of production
authorization. For direct production use, keep the same CLI and workflow,
but switch to a separately approved production identity and access policy
only after the applicable gate passes. Never promote lab credentials or
broaden a lab connection into production.

## 3. Weekly evidence contract

The destination table exposes only `WeekStart:datetime`, `Source:string`,
`Coverage:string`, `Volume:string`, and `Correlation:string`. The portal job
may add platform-managed fields; do not include those in released evidence.

- Use disjoint Monday 00:00 UTC weeks, with event-assignment windows of
  `[WeekStart, WeekStart + 7d)`. Verify completeness after ingestion lag and
  seal each `(WeekStart, Source)` once. Native job output is append-oriented;
  require a serialized operator release record and reconcile job and
  destination state before retrying. Do not resubmit if a prior write is
  present or its outcome is uncertain. No amendments or overlapping cuts.
- For a verified complete week, use `zero`, `suppressed` (1–9), `10-19`,
  `20-49`, `50-99`, or `100+`. A `partial` row has blank `Volume` and
  `Correlation`. Distinguish complete zero, missing publication, stale last
  release, partial coverage, denied access, and disabled source. Never
  interpret the latter five as zero or infer completeness from row presence.
- Never release exact totals, identifiers (including pseudonyms), labels,
  titles, free text, payloads, drill-down links, or breakdowns that allow
  differencing. Suppress the whole source/week if concentration makes even a
  band unsafe. Record counts are not counts of distinct people. Do not sum
  different feed measures or infer exact changes from bands.

| Source | Measure and limits |
|---|---|
| `CloudAppEvents` | Deduplicate locally validated DLP rule-match events. Validate action type and event ID with the connector; rule matches do not represent all DLP activity. |
| `MicrosoftPurviewInformationProtection` | Deduplicate documented, tenant-validated label/protection audit operations. Context only: no alert join or inference that a file was encrypted. |
| `SecurityAlert` | Separate overlay. Filter by a tenant-validated Purview `(VendorName, ProductName, ProviderName)` provenance tuple, never title. Withhold if the tuple cannot exclude unrelated alerts. Deduplicate `SystemAlertId` and use a stable assignment if connector copies straddle weeks. |
| `DataSecurityEvents` | Disabled by default. Accept only separately approved upstream aggregates that meet this contract; never query, stage, or fall back to raw IRM or user-level data. |

For the overlay, use only the [documented DLP correlation][dlp-sentinel]:
`SecurityAlert.AlertType` equals `CloudAppEvents.RawEventData.Data.cid`,
with payload `CreationTime` strictly inside `(StartTime, EndTime)` and a
finite lookaround that bounds both event and connector timestamps. Count
an alert at most once despite duplicate or multiple matching events. Alert
volume includes all approved unique alerts, not just linked alerts.
Correlation is `unverified` until the key, time bounds, and connector coverage
are validated; use `observed` only when both linked and unlinked partitions
contain at least 10 alerts, otherwise `withheld`. Other complete feeds use
`not_applicable`. No other joins or partitions are published.

## 4. Delivery and acceptance

1. Remove inherited ADX and custom MCP code, credentials, config, setup
   instructions and CI references from this sibling edition. Preserve
   runtime-independent policy, evidence and promotion scaffolding.
2. Provide operator-run [native KQL job][jobs] definitions, the aggregate
   schema and read guide, permission go/no-go checks, and Copilot analysis
   prompts that admit only approved aggregate evidence. No tenant operations,
   live reads, deployment, or tool installation are part of repository delivery.
3. Provide synthetic fixtures for band boundaries, duplicate events and
   alerts, provenance exclusion, strict correlation time bounds, missing
   versus zero, and partial or disabled coverage. Distinguish offline
   syntax/parser checks from executed assertions. Connector behavior,
   job publication/retry handling, and effective permissions require
   separate operator validation.
4. Document [Defender alert tuning][dlp-defender] as a manual-only pilot
   change. The built-in DLP tuning rule can route signals to behaviors
   rather than alerts. An authorized operator verifies rule and connector
   configuration, obtains change approval, tests a fresh controlled match
   and checks rollback. Behavior-only telemetry is not proof of zero
   alerts, and historical behavior backfill is not assumed.
5. Before any future investigation pilot, validate the two modes separately
   with synthetic cases: verify case authorization and scope, ensure the
   aggregate mode never sees raw records, and show that an IRM request routes
   to Purview without fetching data. Do not enable a production path until
   its gate is met.
   The [synthetic investigation exercise](sentinel.md#synthetic-investigation-exercise)
   covers the portal query boundary and IRM handoff without using real cases.

## Appendix A: Policy evidence and simulation review

Keep one proposed JSON policy under `policies/`, without a deployment mode.
Use approved sensitive information type names. Pair it with
`evidence/<policy-name>.md`:

```markdown
# Evidence: <policy-name>

- Question and sealed UTC weeks:
- Approved feed names, coverage states, volume bands, and correlation states:
- Signal, caveats, and what cannot be inferred:
- Proposed control and rationale:
- Expected impact, likely false positives, and simulation criteria:
- Disclosure review: approved aggregates only; no identifiers or raw data
```

For a separate simulation review, keep `promotions/<policy-name>.md`:

```markdown
# Promotion: <policy-name>

- Simulation period:
- Approved aggregate outcomes and coverage limitations:
- False-positive review and tuning:
- Decision: promote / extend simulation / retire; approval role:
- Disclosure review: approved aggregates only; no identifiers or raw data
```

[mcp-start]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-get-started
[sentinel-roles]: https://learn.microsoft.com/en-us/azure/sentinel/roles
[mcp-query]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-data-exploration-tool
[jobs]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-jobs
[dlp-sentinel]: https://learn.microsoft.com/en-us/defender-xdr/dlp-investigate-alerts-sentinel
[dlp-defender]: https://learn.microsoft.com/en-us/defender-xdr/dlp-investigate-alerts-defender
[irm-investigation]: https://learn.microsoft.com/en-us/purview/insider-risk-management-activities
