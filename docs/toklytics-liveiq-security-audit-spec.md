# Toklytics-LiveIQ Pre-Launch Security Audit — Plan

> Working name: **toklytics-liveiq-security-audit**
> Status: Draft v0.2
> Target: `Toklytics-LiveIQ` (single repo)
> Tooling lead: `reaper` (forked) + standard SAST/DAST stack

> **Scope correction from v0.1:** The repos `portal-uk`, `portal-us-ca`, and `BEA_Creator_Portal` are **dead** — their functionality was consolidated into `Toklytics-LiveIQ`. The audit now targets one codebase with multi-region tenancy, not three portals. See §10 for cleanup of the dead repos.

---

## 1. Why this exists

`Toklytics-LiveIQ` is now the single asset holding:

- Creator PII (legal name, address)
- Multi-region data subject to GDPR (UK), CCPA (CA — California), PIPEDA (Canada)
- Authentication credentials and session tokens
- Live realtime coaching data (per your existing integration)
- File uploads (CSVs, screenshots feeding into the analytics layer)
- Per-creator historical reports

Stripe payouts live in a separate repo — `KLING-Director` — so payment-flow audit items move to a parallel spec (see §11). The LiveIQ audit still covers any LiveIQ → KLING integration boundary (e.g., displaying payout balances pulled from KLING), but not Stripe webhook handling itself.

Because everything is consolidated into one app, the **blast radius of a breach is larger** than it would have been across three smaller portals. One bug here can expose every creator. A breach would be reputationally fatal for an agency whose value prop depends on creator trust. A pre-launch audit (or pre-next-major-release audit, if LiveIQ is already live) is a fixed-cost, fixed-time investment that reduces this risk.

This is **not** a continuous penetration testing program. It's a one-time gated review with remediation.

---

## 2. Scope

| In scope | Out of scope (this pass) |
|---|---|
| Toklytics-LiveIQ web app + APIs | Cloudflare config audit, full IaC review |
| Authentication + session management | Continuous bug bounty (separate decision, post-launch) |
| Per-region tenancy + data residency handling | Underlying TikTok platform behavior |
| LiveIQ → KLING-Director integration boundary (if any) | Stripe internals (covered in KLING-Director audit — see §11) |
| File uploads (CSV, screenshots) | The dead portal repos (archive them — see §10) |
| Live realtime coaching data path | Social engineering / phishing simulations |
| Role-based access (if staff use the same app) | Full PCI-DSS audit (Stripe Checkout keeps you out of scope by design) |

---

## 3. Threat model (STRIDE shorthand)

| Threat | Concern level | Specific risk |
|---|---|---|
| **S**poofing | High | Account takeover via weak auth, credential stuffing |
| **T**ampering | Medium | Manipulating payout requests, modifying creator metrics |
| **R**epudiation | Medium | Disputed payouts without audit logs |
| **I**nformation disclosure | **Critical** | Cross-tenant data leak between creators; PII exposure |
| **D**enial of service | Low for v1 | Rate limit absence on expensive endpoints |
| **E**levation of privilege | High | Regular creator escalating to admin |

The two critical risks for this kind of app are almost always (a) cross-tenant data leak (creator A sees creator B's data) and (b) auth bypass. Allocate the most audit time there.

**Consolidation amplifies these risks** — when three portals were separate, an IDOR bug in one didn't expose the others. In LiveIQ, a single IDOR could expose every region's creator data. Multi-region tenancy enforcement deserves extra audit time beyond a typical multi-tenant SaaS review.

---

## 4. Audit phases

### Phase 1 — Recon (1-2 days)

- [ ] Inventory every endpoint (REST/GraphQL/tRPC)
- [ ] Inventory every public-facing route
- [ ] Map all third-party integrations (TikTok API, Cloudflare, Supabase, NotebookLM if connected, etc.)
- [ ] Map all internal-service integrations — especially LiveIQ → KLING-Director if LiveIQ surfaces payout data
- [ ] Document the auth flow end-to-end (sequence diagram)
- [ ] Document the tenancy model — how the app distinguishes UK vs US vs CA creators at the DB / API layer
- [ ] List every place PII flows (input → storage → display → logs)
- [ ] Trace the Live realtime coaching data path (websocket / SSE / poll? where does the data sit?)

**Deliverable:** Attack surface map (markdown + diagram).

---

### Phase 2 — Automated scanning (1-2 days)

| Tool | What it checks |
|---|---|
| **`reaper`** (your fork) | Live validation proxy — record app usage, replay with mutations to test auth/IDOR/injection |
| **Semgrep** (cloud free tier) | SAST — secrets, OWASP patterns in code |
| **OWASP ZAP** baseline scan | DAST — passive scan against staging |
| **npm audit** / **pnpm audit** / **pip-audit** | Dependency CVEs |
| **GitHub secret scanning** (already enabled) | Leaked credentials in history |
| **Trivy** | Container image CVEs (if LiveIQ ships Docker) |
| **gitleaks** | Pre-commit secrets check (install if missing) |

**Deliverable:** Raw findings exported per tool. Tagged severity (Critical / High / Medium / Low / Info).

---

### Phase 3 — Manual review (3-5 days, the highest-value phase)

Focus on what scanners miss:

#### Authentication & session
- [ ] Password reset flow can't be abused (no user enumeration, tokens single-use, time-bound)
- [ ] Session fixation / re-use after logout
- [ ] MFA enforced for high-value actions (changing payout info)
- [ ] OAuth/social-login state parameter validated
- [ ] JWT signing key rotation possible; algorithm pinned

#### Authorization (the #1 risk — IDOR + tenant isolation)
- [ ] Every `/api/creators/:id/*` endpoint checks `id == session.userId` server-side
- [ ] Every list endpoint filters by tenant *and region*, not just by `WHERE NOT deleted`
- [ ] Admin-only endpoints fully blocked for non-admin sessions
- [ ] Test with two real creator accounts in parallel: account B should never see account A's data even with manipulated IDs
- [ ] Test cross-region access — a UK creator should not be able to read US creator data via path/param tampering
- [ ] Live coaching feed scoped to the creator's own LIVE session — no eavesdropping on other creators' streams

#### Data handling
- [ ] PII fields encrypted at rest (Supabase column-level encryption or pgcrypto)
- [ ] Logs scrubbed of PII (no full request bodies with personal data)
- [ ] Data export endpoint exists (GDPR Article 20)
- [ ] Data deletion endpoint exists (GDPR Article 17, CCPA right to delete)
- [ ] Retention policy documented and enforced (auto-purge inactive accounts after N years)
- [ ] Data residency: UK/EU creator data stored in EU region if claimed in privacy policy

#### LiveIQ → KLING-Director integration (Stripe is in KLING, not here)
- [ ] If LiveIQ calls KLING for payout data: server-to-server auth uses a service token, not a creator session token
- [ ] LiveIQ never displays raw Stripe payout IDs or full account numbers
- [ ] Amounts displayed in LiveIQ always come from KLING's API, never computed client-side
- [ ] If a creator can trigger a payout from LiveIQ UI: that endpoint is rate-limited and tied to the authenticated creator's KLING account, with cross-creator IDOR tests applied
- [ ] *(Stripe internals — webhook signatures, idempotency, Connect flows, PCI — covered in the KLING-Director audit spec, §11)*

#### File uploads (CSVs, screenshots)
- [ ] Server-side MIME type + magic byte validation, not just extension
- [ ] Max size enforced before parse
- [ ] CSV parsing uses a streaming parser, not whole-file load
- [ ] No SSRF via uploaded URLs
- [ ] Uploaded files served from a different origin than the app (prevent XSS via uploaded SVG/HTML)

#### Common web bugs
- [ ] CSRF tokens on all state-changing same-origin POSTs (or SameSite=Lax+ cookies)
- [ ] CSP header set, no `unsafe-inline` scripts
- [ ] XSS: every user-rendered string escaped (React handles most, but `dangerouslySetInnerHTML` audit)
- [ ] Clickjacking: `X-Frame-Options: DENY` or CSP `frame-ancestors`
- [ ] Open redirect on login/logout redirect params

**Deliverable:** Findings doc with reproduction steps, severity, suggested fix per finding.

---

### Phase 4 — Remediation (varies; budget 1-3 weeks)

- [ ] Triage findings: Critical/High block launch; Medium scheduled; Low/Info backlog
- [ ] Each finding gets a ticket with owner and target date
- [ ] Re-test after fix before closing

**Deliverable:** Findings closed, retest evidence attached.

---

### Phase 5 — Final gate (1 day)

- [ ] No Critical or High findings open
- [ ] All Medium findings have scheduled fix dates
- [ ] Penetration test report signed off
- [ ] Privacy policy + DPA in place (UK + EU creators especially)
- [ ] Incident response runbook drafted (who gets paged, how breach is communicated)

**Deliverable:** Go/no-go memo for LiveIQ.

---

## 5. `reaper` role in detail

Your fork: live validation proxy for testing web app vulnerabilities.

**How we use it:**

1. Stand up Toklytics-LiveIQ in staging with seeded test data covering all regions (Creator-UK, Creator-US, Creator-CA, Admin).
2. Route browser traffic through `reaper` while exercising every feature as Creator-UK.
3. `reaper` captures the full request/response set.
4. Replay captured requests with mutations:
   - Swap `:id` in URLs to other creators' IDs (same region, then cross-region)
   - Strip `Authorization` header
   - Replay with another creator's session cookie
   - Tamper with body params (amounts, dates, role flags, region codes)
5. Flag any non-403/401 response on a tampered request.

This catches the IDOR class of bugs efficiently — the single highest-value bug class for multi-tenant SaaS. The cross-region mutation pass is the highest-value addition here, given that LiveIQ now serves all regions from one codebase.

**Setup steps:**

```bash
git submodule add https://github.com/BEA-BOLD-EVOLUTION/reaper.git tools/reaper
# Configure reaper to record from staging.liveiq.bea.com
# Use the replay script in tools/reaper/scripts/
```

If the upstream `reaper` doesn't have a replay-with-mutation feature, that's a small custom script (~100 LOC) on top of its captured-request format.

---

## 6. Out of scope (this pass)

- Infrastructure penetration testing (Cloudflare, Supabase configs — separate audit)
- Social engineering / phishing simulations
- Full PCI-DSS audit (Stripe Checkout keeps you out of scope by design)
- Continuous bug bounty program (recommended *after* launch, separate decision)

---

## 7. Estimated effort

| Phase | Effort |
|---|---|
| Phase 1 Recon | 1-2 days |
| Phase 2 Automated scans | 1-2 days |
| Phase 3 Manual review | 3-5 days |
| Phase 4 Remediation | 1-3 weeks (depends on findings) |
| Phase 5 Final gate | 1 day |
| **Total elapsed** | **2-4 weeks** for one engineer |

Single codebase = single audit. The "3-5 weeks per portal × 3" estimate from v0.1 collapses to one pass.

---

## 8. Open questions

1. Is Toklytics-LiveIQ already live with real creator data, or is this truly pre-launch? *(If already live, this becomes a "first-pen-test of an in-production app" — same plan, but Phase 4 remediation needs coordinated deploys.)*
2. Internal vs external auditor — running it yourself with `reaper` + Semgrep is fine for a v1 launch; a paid 3rd-party pen test before scaling to thousands of creators is recommended.
3. Bug bounty program plan post-launch?
4. Data residency claim — does the privacy policy promise UK data stays in EU? If yes, the audit must verify this is enforced in infrastructure.

---

## 9. Next concrete steps

1. Confirm whether LiveIQ is pre-launch or live (§8 Q1).
2. Stand up `reaper` against LiveIQ staging as a Phase 0 trial run.
3. Run Phase 1 Recon.

---

## 10. Cleanup — dead portal repos

The repos `portal-uk`, `portal-us-ca`, and `BEA_Creator_Portal` are confirmed dead (their functionality was absorbed into Toklytics-LiveIQ). Recommended actions:

- [ ] Archive each repo on GitHub (Settings → Archive). Preserves history, prevents accidental clones, signals "do not use".
- [ ] Add a final commit to each with a `README.md` line: *"Archived. Functionality consolidated into Toklytics-LiveIQ as of YYYY-MM-DD."*
- [ ] Remove any CI / deploy jobs still wired to them.
- [x] ~~Revoke any service-account credentials those repos held~~ **Confirmed rotated.**

The remaining items are housekeeping — the security-critical step (credential rotation) is done.

---

## 11. Adjacent audit candidate: KLING-Director

`KLING-Director` holds the Stripe integration. Payment-handling code carries fundamentally different risk than analytics code: financial loss, chargeback liability, PCI scope, regulatory exposure. It deserves its own audit pass with a tighter focus than the LiveIQ pass.

**Suggested scope for a KLING-Director audit (separate spec, draft TBD):**

- Stripe webhook signature verification (the #1 most commonly-missed payment bug)
- Webhook idempotency (no duplicate payouts on retry)
- Amounts always computed server-side
- Stripe Connect flow if used for creator payouts (separate threat model)
- API key handling, key rotation, restricted-key usage
- Audit log of every state-changing payment event
- Disputes / chargebacks handling
- Refund flow authorization
- PCI scope verification (Stripe Checkout / Elements only — no PAN ever in your servers)

Recommend running this audit in parallel with the LiveIQ audit, with a single engineer if the codebases are small enough, or two engineers in parallel otherwise. Same `reaper` setup, same Semgrep config, different threat model.

If useful, I can draft a `kling-director-security-audit-spec.md` companion doc — just ask.
