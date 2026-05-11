# KLING-Director Pre-Launch Security Audit — Plan

> Working name: **kling-director-security-audit**
> Status: Draft v0.1
> Target: `KLING-Director` (the repo holding the Stripe integration)
> Tooling lead: `reaper` (forked) + standard SAST/DAST stack + Stripe-specific checks
> Companion to: `toklytics-liveiq-security-audit-spec.md`

> **Working assumption (please correct if wrong):** KLING-Director is a TypeScript service that handles payments / payouts for the agency — possibly orchestrating Kling AI video-gen runs with creator billing, or managing creator payouts independently of LiveIQ. Audit scope adapts based on confirmed role.

---

## 1. Why this exists — and why it's separate from the LiveIQ audit

Payment-handling code carries a fundamentally different risk profile than analytics code:

| Risk dimension | LiveIQ (analytics) | KLING-Director (payments) |
|---|---|---|
| Worst-case bug | Data leak | Direct financial loss + chargeback liability |
| Regulator interest | GDPR / CCPA | PCI-DSS scope check, anti-money-laundering posture, payout reporting |
| Recovery from breach | Apologize, rotate creds, notify | Reverse transactions, refund creators, possibly legal exposure |
| Bug bounty value (post-launch) | High | Very high |

A separate audit pass keeps the threat model focused. Two specs > one mega-spec because the auditor's mindset is different per pass.

---

## 2. Scope

| In scope | Out of scope (this pass) |
|---|---|
| KLING-Director web app + APIs | Cloudflare config audit, full IaC review |
| Stripe webhook handler | Underlying Stripe platform behavior |
| Stripe API key handling + rotation posture | Full PCI-DSS certification (Stripe Checkout / Elements keeps you out of scope by design) |
| Stripe Connect flow (if used for creator payouts) | Social engineering / phishing simulations |
| Payout authorization flow (who can trigger a payout, when, for how much) | Continuous bug bounty (separate post-launch decision) |
| Refund / dispute / chargeback handling | |
| Audit log of every state-changing payment event | |
| Authentication on payment-affecting endpoints | |
| Idempotency posture across all webhook + payout paths | |
| Service-to-service integration boundary with LiveIQ (if any) | |
| If Kling AI video-gen is wired up: API key handling for that too | |

---

## 3. Threat model (payment-flavored STRIDE)

| Threat | Concern level | Specific risk |
|---|---|---|
| **S**poofing | **Critical** | Forged Stripe webhook (no signature verification) triggers fake payout |
| **T**ampering | **Critical** | Client-side amount manipulation in payout requests |
| **R**epudiation | High | Disputed payout with no audit log |
| **I**nformation disclosure | High | Stripe customer/account IDs leaked, payout history exposed cross-creator |
| **D**enial of service | Medium | Replay attacks creating duplicate payouts (idempotency) |
| **E**levation of privilege | Critical | Regular creator triggers admin-only refund / payout endpoints |

**The two highest-priority audit findings for any payment service** are almost always:

1. **Unverified webhook signatures** — the textbook bug. Anyone who can POST to your webhook URL can manufacture payment events. Stripe's docs make this trivially fixable; the bug appears in ~30% of new Stripe integrations.
2. **Client-trusted amounts** — UI sends `{ amount: 5000 }`, server doesn't recompute. Attacker sends `{ amount: 5_000_000 }`, server pays.

Allocate the most time to those two.

---

## 4. Audit phases

### Phase 1 — Recon (1 day)

- [ ] Inventory every endpoint, distinguishing payment-affecting vs read-only
- [ ] Locate the Stripe webhook handler(s) — confirm signature verification call is present and not just a no-op
- [ ] Inventory every place a Stripe key is read from env / config / secrets manager
- [ ] Document the payout flow end-to-end (sequence diagram): creator action → KLING decision → Stripe call → webhook → state update → notification
- [ ] Document the refund / dispute / chargeback flows similarly
- [ ] Map service-to-service auth between KLING and any other internal services (LiveIQ, training engine, etc.)

**Deliverable:** Payment surface map + key flow diagrams.

---

### Phase 2 — Automated scanning (1 day)

Same tool stack as LiveIQ audit, plus payment-specific:

| Tool | What it checks |
|---|---|
| **`reaper`** | Live validation proxy — replay payment requests with mutated amounts, currencies, recipients |
| **Semgrep** | SAST — secrets, OWASP patterns. Add Stripe-specific rules (catch raw `req.body` passed to webhook handler) |
| **gitleaks** | Scan git history specifically for Stripe live keys (`sk_live_*`, `rk_live_*`) |
| **`npm audit`** | Dependency CVEs (especially the `stripe` package version — older versions had signature verification bugs) |
| **GitHub secret scanning** | Already enabled; verify Stripe partner integration is active for early-warning |

**Deliverable:** Findings tagged by severity. Any Stripe key in git history = immediate Critical, regardless of whether it's been rotated.

---

### Phase 3 — Manual review (2-4 days)

The highest-leverage phase. Focus on what scanners can't see.

#### Stripe webhook handling — the #1 audit area
- [ ] Webhook handler uses `stripe.webhooks.constructEvent()` (or equivalent) with the raw request body, *not* a parsed JSON body
- [ ] Body parser middleware (Express `body-parser` etc.) is *not* applied to the webhook route — signature verification needs the raw bytes
- [ ] Webhook signing secret loaded from secret store, not from env file in repo
- [ ] Each webhook event has an idempotency check: `if (already_processed(event.id)) return 200` — required because Stripe retries on non-200
- [ ] Handler returns 200 quickly; expensive work goes to a queue (Stripe times out at 10s and considers slow handlers as failures, triggering retries)
- [ ] Handler does *not* trust `event.data` to determine what happened — re-fetches via `stripe.charges.retrieve()` if the event has security implications (defense in depth against signature-bypass bugs)
- [ ] Failed verifications are logged but do *not* leak whether the secret is "close" or "far off" (no error-message gradient)

#### API key handling
- [ ] No `sk_live_*` keys in any repo (including git history — check with gitleaks)
- [ ] Production uses restricted keys with least-privilege scopes, not full secret keys
- [ ] Key rotation procedure documented + tested at least once
- [ ] Separate keys per environment (dev, staging, prod); no shared keys
- [ ] Keys loaded from secrets manager (Cloudflare secrets, AWS Secrets Manager, etc.), not env files in deploys
- [ ] If LiveIQ or other services call KLING: they use service tokens, not Stripe keys directly

#### Amount integrity
- [ ] Every payout/charge amount computed server-side from authoritative data (database state, business logic), never from client input
- [ ] Currency code validated against an allowlist
- [ ] Maximum-amount safety cap enforced server-side (e.g., no single payout > $X without manual approval)
- [ ] Negative or zero amounts handled correctly (and logged as suspicious)

#### Authorization on payment-affecting endpoints
- [ ] Every "trigger payout" endpoint requires fresh authentication (re-prompt for credentials or MFA, not just session check)
- [ ] Payout destination cannot be changed by anyone other than the account owner, and the change has a cooling-off period
- [ ] Admin-only endpoints (manual refunds, force payouts, account reset) require MFA + audit log entry per action
- [ ] No "elevated session" pattern that grants admin powers via a flag set client-side
- [ ] Cross-creator IDOR tests: Creator A cannot trigger Creator B's payout via path/param tampering

#### Stripe Connect (if used for creator payouts)
- [ ] Onboarding link uses `account_links` with short expiration, single-use
- [ ] Each connected account is tied to exactly one creator in your DB; no shared accounts
- [ ] Application fee structure is server-defined, not client-tunable
- [ ] Connected account capabilities are minimum-needed (e.g., `transfers` only, not `card_payments` if you don't need it)
- [ ] Reverse charge / refund flow tested end-to-end

#### Refunds / disputes / chargebacks
- [ ] Refund endpoint authorization same rigor as payout
- [ ] Dispute webhook handler updates internal state (so a disputed payout doesn't get re-triggered)
- [ ] Chargeback alerting wired up (Slack / email to the right humans)
- [ ] Refund amount cannot exceed original charge

#### Audit logging
- [ ] Every state-changing payment operation writes an immutable log entry (DB row or append-only log)
- [ ] Log includes actor (who), action (what), target (creator/account), amount, timestamp, IP, user agent
- [ ] Logs retained per regulatory requirement (7 years is a safe default for financial records)
- [ ] Logs scrubbed of secrets but *not* of identifiers — the trail must be complete

#### Common payment-service bugs
- [ ] Race conditions: same payout triggered twice in parallel (DB transaction + idempotency key prevents)
- [ ] TOCTOU on payout: balance checked, then payout processed seconds later (recheck inside the transaction)
- [ ] Webhook event ordering: handler tolerates out-of-order delivery (Stripe doesn't guarantee order)
- [ ] Test mode vs live mode confusion: no test-mode keys can be used to manipulate live data

**Deliverable:** Findings doc with reproduction steps, severity, suggested fix per finding. Any Critical here is a launch-blocker.

---

### Phase 4 — Remediation (varies; budget 1-3 weeks)

- [ ] Triage: Critical/High block launch; Medium scheduled; Low/Info backlog
- [ ] Each finding gets a ticket, owner, target date
- [ ] Re-test after fix before closing
- [ ] **Special case:** any "key in git history" finding requires immediate key rotation (regardless of remediation status of the bug that allowed it)

---

### Phase 5 — Final gate (1 day)

- [ ] No Critical or High findings open
- [ ] Webhook signature verification confirmed working via deliberate-bad-signature test
- [ ] Key rotation drill completed within last 90 days
- [ ] Incident response runbook for payment incidents drafted (different from generic IR — includes Stripe support contact path, refund-pause procedure, creator-comms template)
- [ ] Disaster recovery: can you reconstruct payment state from Stripe + your audit log if your DB is lost?

**Deliverable:** Go/no-go memo.

---

## 5. `reaper` role for payment audits

Same proxy-record-replay-mutate pattern as the LiveIQ audit, but the mutation set is payment-specific:

- Swap recipient account IDs (cross-creator IDOR on payouts)
- Tamper with amounts (5000 → 5_000_000, 5000 → -5000)
- Swap currency codes (USD → JPY: different decimal handling, common bug)
- Strip MFA challenge tokens
- Replay webhook bodies with valid signatures but stale timestamps (idempotency check)
- Replay webhook bodies with tampered signatures (must reject)

Most of these need ~5-line additions to `reaper`'s replay config. Worth investing the time — payment IDOR is the single highest-value bug class here.

---

## 6. Estimated effort

| Phase | Effort |
|---|---|
| Phase 1 Recon | 1 day |
| Phase 2 Automated scans | 1 day |
| Phase 3 Manual review | 2-4 days |
| Phase 4 Remediation | 1-3 weeks (depends on findings) |
| Phase 5 Final gate | 1 day |
| **Total elapsed** | **2-4 weeks** |

Shorter than LiveIQ because the surface area is narrower (payment-focused). Higher density of Critical findings is normal for first-time payment audits.

---

## 7. External audit recommendation

A self-audit using `reaper` + Semgrep + this checklist is appropriate for v1 launch. **Before scaling past ~$100k/month in processed payment volume, get a 3rd-party pen test from a firm with payments experience** (e.g., NCC Group, Bishop Fox, Doyensec). The third-party validation matters for:

- Future business insurance underwriting
- Larger creator partnerships requiring vendor security review
- Investor due diligence
- Genuine independent perspective (you've been staring at the code for months; they haven't)

Budget ~$15-30k for a focused payment pen test from a reputable firm. Cheaper than the cost of one undetected critical bug.

---

## 8. Open questions

1. **What does KLING-Director actually do?** I'm guessing payments orchestration based on the Stripe confirmation. Confirming the actual purpose changes some checklist items.
2. Does KLING-Director call Stripe directly, or via a wrapped library?
3. Is Stripe **Connect** in use (for creator payouts), or just standard Charges (for one-way billing)?
4. Is KLING-Director the only repo with Stripe access, or do other services hold keys?
5. Is KLING-Director already processing real money, or is this truly pre-launch?
6. Does LiveIQ display data sourced from KLING (payouts shown in dashboard)? If so, the LiveIQ → KLING service boundary needs the integration tests called out in §3 of the LiveIQ audit spec.
7. Bug bounty program plan post-launch?

---

## 9. Concrete next steps

1. Answer §8 Q1 + Q3 — these shape the checklist.
2. Phase 0: deliberately submit a bad-signature webhook to staging KLING. If it returns anything other than 400/401/403, that's an immediate Critical and a launch-blocker. Two-line test, settles a lot.
3. Run Phase 1 Recon.
4. Coordinate with the LiveIQ audit if both are happening in parallel — share `reaper` infra and Semgrep config.

---

## 10. Coordination with LiveIQ audit

Same engineer can run both audits sequentially (KLING first, since it's tighter and the highest-density-Critical area) OR two engineers in parallel.

Shared infrastructure:

- One `reaper` setup, two replay configs
- Shared Semgrep config (extended with payment rules for KLING)
- Shared remediation tracker
- Shared final-gate process

If running sequentially, allow 1-week gap so the team isn't context-switching between data-protection mode and payments mode mid-audit.
