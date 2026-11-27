---
applyTo: ".github/workflows/**"
---
- Use `contents: read`. CI must not sign in to Azure or any tenant service.
- Use the current major versions of actions. Don't invent commit SHAs.
- Never echo secrets, tokens or certificate material. Don't use pull_request_target.
- Do not add deployment jobs or tenant integration checks.
