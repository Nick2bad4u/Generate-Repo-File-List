# Portal Pre-Launch Security Audit — Plan

> Working name: **portal-security-audit**
> Status: Draft v0.1
> Targets: `portal-uk`, `portal-us-ca`, `BEA_Creator_Portal`
> Tooling lead: `reaper` (forked) + standard SAST/DAST stack

---

## 1. Why this exists

The three creator portals will hold:

- Creator PII (legal name, address, payout details)
- Region-specific data subject to GDPR (UK), CCPA (CA — California), PIPEDA (Canada)
- Authentication credentials and session tokens
- Payout integration (Stripe, if integrated per the Stripe-node recommendation)
- File uploads (CSVs, screenshots feeding into Toklytics)

A breach in any one would be reputationally fatal for an agency whose value prop depends on creator trust. A pre-launch audit is a fixed-cost, fixed-time investment that reduces this risk before the portals ever see a real user.

This is **not** a continuous penetration testing program. It's a one-time gated review with remediation, before each portal goes live.

---

## 2. Scope per portal

| Portal | Region | In scope | Out of scope (this pass) |
|---|---|---|---|
| `portal-uk` | UK | App + APIs + Stripe webhooks (if present) + auth | Cloudflare config audit, full IaC review |
| `portal-us-ca` | US + Canada | Same | Same |
| `BEA_Creator_Portal` | Global / internal? | Same — plus role-based access if used by staff | Internal-only tools beyond the portal |

If `BEA_Creator_Portal` turns out to be staff-only / admin, broaden the auth model review (privilege escalation, audit logs).

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

The two critical risks for this kind of portal are almost always (a) cross-tenant data leak (creator A sees creator B's data) and (b) auth bypass. Allocate the most audit time there.

---

## 4. Audit phases

### Phase 1 — Recon (1-2 days)

- [ ] Inventory every endpoint (REST/GraphQL/tRPC) per portal
- [ ] Inventory every public-facing route
- [ ] Map all third-party integrations (Stripe, TikTok API, Cloudflare, Supabase, etc.)
- [ ] Document the auth flow end-to-end (sequence diagram)
- [ ] List every place PII flows (input → storage → display → logs)

**Deliverable:** Per-portal attack surface map (markdown + diagram).

---

### Phase 2 — Automated scanning (1-2 days)

| Tool | What it checks |
|---|---|
| **`reaper`** (your fork) | Live validation proxy — record portal usage, replay with mutations to test auth/IDOR/injection |
| **Semgrep** (cloud free tier) | SAST — secrets, OWASP patterns in code |
| **OWASP ZAP** baseline scan | DAST — passive scan against staging |
| **npm audit** / **pnpm audit** / **pip-audit** | Dependency CVEs |
| **GitHub secret scanning** (already enabled) | Leaked credentials in history |
| **Trivy** | Container image CVEs (if portals ship Docker) |
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

#### Authorization (the #1 portal risk — IDOR)
- [ ] Every `/api/creators/:id/*` endpoint checks `id == session.userId` server-side
- [ ] Every list endpoint filters by tenant, not just by `WHERE NOT deleted`
- [ ] Admin-only endpoints fully blocked for non-admin sessions
- [ ] Test with two real creator accounts in parallel: account B should never see account A's data even with manipulated IDs

#### Data handling
- [ ] PII fields encrypted at rest (Supabase column-level encryption or pgcrypto)
- [ ] Logs scrubbed of PII (no full request bodies with personal data)
- [ ] Data export endpoint exists (GDPR Article 20 — UK portal)
- [ ] Data deletion endpoint exists (GDPR Article 17, CCPA right to delete)
- [ ] Retention policy documented and enforced (auto-purge inactive accounts after N years)

#### Payments (if Stripe wired up)
- [ ] Stripe webhook signature verified (not just IP allowlist)
- [ ] Webhook idempotency (no duplicate payouts on retry)
- [ ] Amounts always computed server-side, never trusted from client
- [ ] PCI: no card data ever touches your servers (Stripe Elements / Checkout only)

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

**Deliverable:** Go/no-go memo per portal.

---

## 5. `reaper` role in detail

Your fork: live validation proxy for testing web app vulnerabilities.

**How we use it:**

1. Stand up portal in staging with seeded test data (Creator A, Creator B, Admin).
2. Route browser traffic through `reaper` while exercising every feature as Creator A.
3. `reaper` captures the full request/response set.
4. Replay captured requests with mutations:
   - Swap `:id` in URLs to Creator B's ID
   - Strip `Authorization` header
   - Replay with Creator B's session cookie
   - Tamper with body params (amounts, dates, role flags)
5. Flag any non-403/401 response on a tampered request.

This catches the IDOR class of bugs efficiently — the single highest-value bug class for multi-tenant SaaS portals.

**Setup steps:**

```bash
git submodule add https://github.com/BEA-BOLD-EVOLUTION/reaper.git tools/reaper
# Configure reaper to record from staging.portal-uk.bea.com (etc.)
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
| **Total elapsed** | **3-5 weeks per portal**, runnable in parallel across the three |

A single competent security engineer can run all three portals in parallel because the codebases likely share substantial code. If they share a codebase, this drops dramatically (5-7 days total).

---

## 8. Open questions

1. Do the three portals share a codebase / monorepo, or are they independent? (Massive impact on effort.)
2. Are they live yet with real creator data, or is this truly pre-launch?
3. Is Stripe (or any payment processor) integrated yet?
4. Internal vs external auditor — running it yourself with `reaper` + Semgrep is fine for a v1 launch; a paid 3rd-party pen test before scaling to thousands of creators is recommended.
5. Bug bounty program plan post-launch?

---

## 9. Next concrete steps

1. Confirm answers to §8 question 1 (shared codebase?) — this determines whether we plan 1 audit or 3.
2. Stand up `reaper` against `portal-uk` staging as a Phase 0 trial run.
3. Run Phase 1 Recon on the highest-priority portal first.
