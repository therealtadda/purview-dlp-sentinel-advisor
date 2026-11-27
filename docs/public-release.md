# Public-release readiness

This checklist guides review of public snapshots. When exporting from a
private repository, use a **new public repository with fresh history** rather
than changing the private source's visibility. It does not itself authorize
publication.

## Owner decisions

- Confirm the license and rights to all included material.
- Confirm maintainers and support scope before relying on review routing.
  Confirm whether issues and contributions are accepted and add contribution
  guidance appropriate to that decision.
- Confirm that private vulnerability reporting or another approved,
  reachable confidential reporting channel is enabled and reflected in
  [SECURITY.md](../SECURITY.md). Obtain Security/Privacy and publication approval.

## Review the export, not just the current branch

1. Review the intended exact files, generated output, examples, comments,
   configuration, issue templates, commit metadata, links and dependencies.
   Scan for credentials, tenant/workspace IDs, real alert IDs, customer data,
   private endpoints, personal information, internal names, and confidential
   instructions. A scan is a supplement to human review, not proof of safety.
2. Preserve only synthetic fixtures and tenant-independent documentation.
   Do not include an active MCP configuration, local session state, private
   ledger, logs, tenant exports, secrets, or customer-specific connector
   values. Verify that copied or referenced third-party material can be
   redistributed under its terms.
3. Prepare the approved snapshot with a new root commit in a new public
   repository, without prior branches, commits, tags, issues, pull requests,
   attachments, LFS objects, or other private history. Review author and
   committer metadata and release artifacts. Do not rely on deleting a
   secret from the latest commit to sanitize older history.
4. Run the [offline checks](poc-validation.md#1-offline-checks) on the
   exact snapshot, review links and documentation, and verify CI on a
   runner available to the public repository. Record any unexecuted KQL,
   customer validation and production MCP gates plainly.
5. Obtain explicit owner and security approval of the snapshot and license
   before a separate publication action. After publication, monitor issues,
   update dependency and reference checks, and keep tenant operations out of CI.
