# Purview DLP Advisor: Sentinel edition

This is an independent community project and is not affiliated with or
endorsed by Microsoft.

Use Microsoft Sentinel data lake weekly evidence to draft Microsoft Purview
Data Loss Prevention (DLP) recommendations. An authorized operator runs native
KQL jobs in the Defender portal. The advisor uses only approved aggregate
rows, not raw events. There is no ADX backend or custom MCP server.

**Production stays portal-only for data access.** Microsoft-hosted Sentinel
MCP is not approved for production: its required Security Reader role can
read across the lake, and its query tool returns KQL results as-is. The
[permission gate](docs/sentinel.md#production-permission-gate) explains why.
This is a POC, not a replacement for Sentinel or Purview investigation
workflows. The only investigation query looks up a known DLP alert's metadata;
raw events remain in the portal, and IRM investigations stay in Purview.
The KQL fixtures and CLI-to-Sentinel sign-in have not been executed or
verified by this repository. An authorized operator must validate them in
the customer environment before relying on the affected workflow.
On 27 November 2026, the CLI command-line flags below were checked against
Copilot CLI 1.0.115-7, and the linked GitHub and Microsoft setup references
were reviewed. This does not verify CLI authentication to Sentinel; consult
the current product documentation because preview behavior can change.

## Customer POC prerequisites

Before sharing data or running a query, the customer should designate a
POC owner, Sentinel publisher, analyst, and Security/Privacy approver.
They must confirm:

1. A Copilot subscription and organization policy permitting the CLI; an
   approved data-sharing and retention policy for the selected Copilot
   experience and its stored conversations.
2. Sentinel data lake onboarding, the intended workspaces and native query
   and KQL-job permissions, plus an analytics-tier destination. The publisher
   and analyst use separate roles; ask the customer's administrator to
   validate the [documented permissions][roles] rather than granting a
   broad role by default.
3. Relevant DLP alert and event connectors, expected workloads and health;
   the operator must validate actual source schemas, DLP action types,
   event IDs, provenance and ingestion delay before declaring coverage.
4. Ownership of data retention and query, job and analytics-tier costs;
   a private, serialized release ledger; case handling and escalation; and
   a rollback/stop procedure. A query result or Copilot proposal does not
   authorize a policy change.

The customer should review the [functional acceptance guide](docs/poc-validation.md)
before the POC. An isolated synthetic tenant is recommended but not required
for the disconnected workflow. Real raw data and case identifiers stay in
authorized portals and case systems; only separately approved weekly
aggregate rows may be shared with Copilot.

## Install GitHub Copilot CLI

Use the same [GitHub Copilot CLI][cli-install] for testing and production.
You need an active Copilot subscription and, for organization-managed
access, permission to use Copilot CLI. There is no separate advisor
executable or repository runtime to install. Open or clone this repository
to get the query templates and prompts; run Copilot from a separate folder.

| Platform | Install command |
|---|---|
| Windows (PowerShell 6+) | `winget install GitHub.Copilot` |
| macOS or Linux with Homebrew | `brew install --cask copilot-cli` |
| Any supported platform with Node.js 22+ | `npm install -g @github/copilot` |

Run `copilot --version` to confirm installation. On first launch, use
`/login` if prompted and sign in with your approved GitHub account. Copilot
sign-in is separate from Sentinel's Microsoft Entra sign-in.

## Configure a disconnected analyst session

Use this setup for both production workflows and for a synthetic dry run.
In a dedicated terminal, use a fresh, empty folder outside this repository
and a separate Copilot configuration directory. For example, on PowerShell:

```powershell
$env:COPILOT_HOME = Join-Path $HOME 'copilot-advisor-disconnected'
New-Item -ItemType Directory -Force -Path $env:COPILOT_HOME | Out-Null
$work = Join-Path $HOME 'copilot-advisor-analyst'
New-Item -ItemType Directory -Force -Path $work | Out-Null
Set-Location $work
copilot mcp list
```

In Bash or Zsh, the equivalent is:

```bash
export COPILOT_HOME="$HOME/copilot-advisor-disconnected"
mkdir -p "$COPILOT_HOME" "$HOME/copilot-advisor-analyst"
cd "$HOME/copilot-advisor-analyst"
copilot mcp list
```

Do not continue if a user-, workspace-, or plugin-supplied server is
configured. With no such servers configured, start the interactive session:

```text
copilot --disable-builtin-mcps --available-tools=view
```

Keep the folder empty of tenant files. Do not attach files or approve tool
calls. VS Code Copilot Chat **Ask** mode with no tenant connectors is an
alternative for these disconnected workflows.

## Aggregate analysis: Trends and recommendations

1. For a dry run, paste the [synthetic prompt](docs/analysis-prompts.md#try-it-without-mcp)
   into the disconnected session. Expect it to identify a higher DLP band,
   missing label coverage, and a partial alert week without estimating
   exact counts.
2. For production, open the Defender portal's **Advanced hunting** KQL editor
   for the approved analytics-tier destination, paste
   [read-weekly.kql](ops/sentinel/read-weekly.kql), set the first Monday and
   exclusive end Monday for the sealed weeks, and run it. If the editor has
   a time filter, ensure it does not exclude rows based on when they were written.
3. Check the results against the [weekly schema](docs/sentinel.md#read-and-interpret).
   Do not share duplicate or malformed rows. If policy permits, paste only
   the five approved columns and approved coverage statuses directly into
   Copilot, not into a repository file or shell arguments.
4. Use the [trend prompt](docs/analysis-prompts.md#assess-coverage-and-change)
   or [recommendation prompt](docs/analysis-prompts.md#draft-a-policy-recommendation).
   Review the result before proposing any simulation; a higher match band
   alone does not establish a policy's effectiveness or increased risk.

## Event investigation: Draft in Copilot, run in the portal

1. Record case authorization, reference, and purpose in the approved case
   system before fetching data. Paste the
   [case prompt](docs/analysis-prompts.md#draft-a-case-investigation) into
   disconnected Copilot using placeholders only.
2. In the approved Sentinel workspace, [find the alert's `SystemAlertId`](docs/sentinel.md#find-the-sentinel-alert-id).
   Open the [alert template](ops/sentinel/investigate-alert.kql) in the
   portal query editor and fill in `alert_id`, the verified Purview DLP
   vendor/product/provider tuple, and a
   UTC start and exclusive end no more than 24 hours apart. Review the
   query before running it. Do not broaden scope automatically on no match.
3. Review details in the portal and keep results in the approved case
   workflow. Do not send raw results back to Copilot. For Insider Risk
   Management (IRM), use the [native Purview handoff](docs/sentinel.md#event-investigation)
   instead of this query.

## Option B: Query the isolated lab via Sentinel MCP

Test the disconnected workflows first in the same CLI used for production.
The optional lab below additionally tests direct MCP transport; it does not
approve a production connection. [Copilot CLI supports remote HTTP MCP][cli-mcp],
but Sentinel's Entra flow in that client is still unverified in this project.

1. **Check isolation first.** Use a nonproduction tenant and an approved
   lab-only Entra identity. Confirm every workspace, table, federated source
   and catalog reachable by that identity contains only synthetic data or
   approved aggregates. A dedicated workspace in a production tenant is
   not enough. If you cannot prove isolation, use the disconnected aggregate
   workflow with synthetic data.
2. **Seed the fixture.** An authorized lab operator can preview
   [lab-seed.kql](ops/sentinel/lab-seed.kql) and run it once as a native
   [Sentinel KQL job][jobs] into a new analytics-tier lab table. Use the base
   name `AdvisorWeeklyEvidenceV1` (the portal appends `_KQL_CL`). Verify five
   rows and the five evidence columns in the portal's Advanced hunting editor with the
   [read query](ops/sentinel/read-weekly.kql); set the exclusive end to
   `datetime(2026-01-19)` for both fixture weeks. Don't append a second seed
   or run this against a shared or production table.
3. **Configure only the lab workspace.** To try the CLI, use a separate
   OS/browser profile and clean `COPILOT_HOME` outside the repo. In an
   empty folder use `copilot --disable-builtin-mcps`, then `/mcp add` with
   HTTP, name `sentinel-lab`, the official endpoint below, and **Tools**
   set to `query_lake` before saving. Alternatively, use the provided
   [CLI JSON example](#example-lab-mcp-configuration). Set `COPILOT_HOME`
   as in the disconnected example, but use a different directory such as
   `copilot-advisor-lab`; never reuse it for production. Do not persist
   approvals. If user sign-in or tool
   filtering does not work, stop the CLI connection attempt and use the
   documented VS Code lab path.

   For VS Code, use a separate OS/browser profile
   or lab host for the lab identity. Open an empty VS Code folder outside
   the repo. Follow [Microsoft's VS Code setup][vscode-mcp]: choose
   **MCP: Add Server > HTTP**, enter
   `https://sentinel.microsoft.com/mcp/data-exploration`, name it
   `sentinel-lab`, and save it to the current workspace only. Alternatively,
   use the [example JSON](#example-lab-mcp-configuration). Do not paste a
   token into HTTP headers, chat, or config.
4. **Verify before querying.** Confirm the lab tenant and account at the
   Microsoft Entra sign-in prompt. If it does not appear and the identity
   cannot be verified, do not approve a query. In CLI, check
   `/mcp show sentinel-lab` and select `/permissions manual`. In
   VS Code Copilot Chat, choose **Agent** and use
   **Configure Tools** to select only `query_lake`; deselect catalog, entity,
   write, and terminal tools. Require review of each call and do not save
   approvals. If sign-in or tool restriction does not work, stop and use
   the disconnected workflow.
5. **Run one read.** Use the [lab prompt](docs/analysis-prompts.md#query-the-isolated-lab).
   Supply the lab workspace ID to `query_lake` and inspect the proposed
   workspace and exact KQL before approving a single call. Do not approve
   catalog lookup, entity analysis, shell use, writes, or follow-up queries.
   The project's lab has not verified that the promoted analytics-tier table
   is accessible to `query_lake`; if it is not, stop the MCP exercise and
   use the portal read instead.
   Expect five rows: the DLP band changes from `10-19` to `20-49`, the second
   label week is missing, and the second alert week is partial. Afterward,
   remove the lab server with `/mcp delete sentinel-lab` in CLI, or
   stop the server with **MCP: List Servers** and remove the lab
   workspace configuration in VS Code.

The client tool filter and manual approval control the workflow, not what
Sentinel authorizes. Never use this lab workflow against production.

### Example lab MCP configuration

For CLI, copy into `mcp-config.json` under the isolated `COPILOT_HOME`.

```json
{
  "mcpServers": {
    "sentinel-lab": {
      "type": "http",
      "url": "https://sentinel.microsoft.com/mcp/data-exploration",
      "tools": ["query_lake"]
    }
  }
}
```

For VS Code, copy this into `.vscode/mcp.json` in
the isolated lab folder, outside the repo. Use it only after confirming
lab isolation. The JSON registers the collection; select only `query_lake`
in Copilot Chat's tool picker before use.

```json
{
  "servers": {
    "sentinel-lab": {
      "type": "http",
      "url": "https://sentinel.microsoft.com/mcp/data-exploration"
    }
  }
}
```

The endpoint is Microsoft-hosted and has no tenant-specific URL to edit.
Verify the lab tenant and account at Microsoft Entra sign-in. Pass the lab
workspace ID as `workspaceId` in the query call, not in this file. This
example does not enforce aggregate-only access; follow step 4 before querying.

## Prebuilt KQL queries and when to use them

| File | What it does | When to use it |
|---|---|---|
| [weekly-functions.kql](ops/sentinel/weekly-functions.kql) | Shared publication logic for sealed UTC weeks, deduplication, volume bands, and alert linkage. It does not return a result by itself. | Paste it before exactly one weekly job fragment or the weekly synthetic assertions. |
| [job-dlp.kql](ops/sentinel/job-dlp.kql) | Deduplicates validated `CloudAppEvents` DLP rule matches by report ID and emits one weekly band when coverage is complete. | Compare comparable weeks for increased rule-match volume. It does not measure all DLP activity or distinct people. |
| [job-labels.kql](ops/sentinel/job-labels.kql) | Bands deduplicated label and label-policy audit activity from `MicrosoftPurviewInformationProtection`. | Check whether label activity changed alongside DLP trends. It is context, not proof of encryption or a linkage to an alert. |
| [job-alerts.kql](ops/sentinel/job-alerts.kql) | Filters `SecurityAlert` by the tenant-validated Purview provenance tuple and bands unique alerts. It separately reports whether a documented, time-bounded join to `CloudAppEvents` can be disclosed. | Compare Purview alert volume with DLP rule-match trends without combining the counts. Use `unverified` and `withheld` to qualify conclusions, not as evidence of no relationship. |
| [read-weekly.kql](ops/sentinel/read-weekly.kql) | Reads the five published evidence columns for a bounded range of sealed weeks. It does not read raw source tables. | Use in the production portal to prepare approved input for trend and simulation prompts, or in the isolated lab to verify the seed. |
| [investigate-alert.kql](ops/sentinel/investigate-alert.kql) | Read-only lookup for one known Purview DLP alert and exact provenance within a UTC window of at most 24 hours; returns up to 25 rows. | Use in the authorized portal to confirm an alert's timing and type before reviewing related events. Do not submit to MCP, publish as a job, or use for IRM. |
| [investigate-alert-fixture.kql](ops/sentinel/investigate-alert-fixture.kql) | Synthetic input for the investigation template, including a different alert, wrong provider, and exclusive end-boundary row. | Replace the template's `CaseAlerts` binding and follow the [synthetic exercise](docs/sentinel.md#synthetic-investigation-exercise); expect one matching row with the supplied inputs. |
| [weekly-fixtures.kql](ops/sentinel/weekly-fixtures.kql) | Sixteen synthetic assertions covering bands, missing IDs, deduplication, provenance, correlation timing, and coverage states. | Prefix with the shared functions and run in a synthetic editor session after editing the weekly logic. Expect 16 rows with `Passed=true`; do not publish them. |
| [lab-seed.kql](ops/sentinel/lab-seed.kql) | Produces five fixed synthetic aggregate rows for the two lab weeks. | Seed a new isolated lab destination once to exercise the read query and Copilot interpretation without real data. |

### Publish weekly evidence as an operator

1. Select the approved source workspace in Defender's data lake query editor.
   Paste `weekly-functions.kql` followed by **one** `job-*.kql` fragment.
   Set `week` to the intended Monday at 00:00 UTC. Keep the example
   approval and readiness flags disabled until the checks in the
   [operator runbook](docs/sentinel.md#publish-a-sealed-week) pass.
2. After reserving the source/week and confirming coverage and disclosure
   approval, preview the output. Expect one row for that source/week with
   only the five evidence columns. For a partial release, `Volume` and
   `Correlation` must be blank.
3. Create a **one-time** KQL job into the approved analytics-tier table
   `AdvisorWeeklyEvidenceV1_KQL_CL` (use base name `AdvisorWeeklyEvidenceV1`
   when creating it). Reconcile completion and verify exactly one row before
   sealing the release. Do not rerun or edit a job with an unknown write
   outcome; see the runbook for retry rules.

## Repository guide

- [Operator runbook and aggregate schema](docs/sentinel.md)
- [KQL job fragments and synthetic assertions](ops/sentinel/)
- [Copilot analysis prompts](docs/analysis-prompts.md)
- [Functional tests and customer acceptance](docs/poc-validation.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Public-release checklist](docs/public-release.md)
- [Edition plan and policy evidence templates](docs/plan.md)

Raw investigations and policy administration stay in the authorized Microsoft
portals. This repository does not deploy policies, install tools, or ship
active MCP configuration.

For offline verification, run from the repository root:

```text
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
```

These structural checks do **not** parse or execute KQL. See the functional
test guide for expected results, synthetic execution and customer acceptance.

[cli-install]: https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli
[cli-mcp]: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers
[jobs]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/kql-jobs
[roles]: https://learn.microsoft.com/en-us/azure/sentinel/roles
[vscode-mcp]: https://learn.microsoft.com/en-us/azure/sentinel/datalake/sentinel-mcp-use-tool-visual-studio-code
