---
applyTo: "policies/**,evidence/**,promotions/**"
---
- Policy files never contain a mode field. They are proposals, not deployment inputs.
- Use only approved sensitive information type (SIT) names, verified by authorized reviewers.
- Every policy file has a matching evidence file that follows the template in docs/plan.md Appendix A.
- Evidence and promotion files contain aggregates only: no names, UPNs, email addresses, user object IDs, pseudonymous IDs or individual risk levels.
- For risk-based controls, use the Adaptive Protection insider risk level condition. Never list individual users.
