# KLING-Director Pre-Launch Security Audit — Plan

> Working name: **kling-director-security-audit**
> Status: Draft v0.2
> Target: `KLING-Director` ([repo](https://github.com/BEA-BOLD-EVOLUTION/KLING-Director))
> Tooling lead: `reaper` (forked) + standard SAST/DAST stack + Stripe-specific checks
> Companion to: `toklytics-liveiq-security-audit-spec.md`

> **Confirmed scope (from README):** KLING-Director is a self-service SaaS web app — an AI-powered prompt compiler for Kling video generation. Users sign up via Supabase Auth, pay via Stripe subscription ($5.99 Director / $9.99 Director Pro / $0 VIP / $0 BEA Creator partner / 7-day free trial). The app uses Claude Sonnet 4 + Gemini 2.0 Flash for prompt analysis. **Two distinct Stripe surfaces:** (a) subscription billing (incoming) and (b) Stripe Connect Express for affiliate payouts at 15% commission (outgoing). Tech stack: Next.js 16, React 19, tRPC 11, Supabase (Auth + Storage + Postgres), Prisma 5, hosted on Vercel (web) + Railway (api).

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
| KLING-Director web app + tRPC API | Cloudflare config audit, full IaC review |
| **Subscription billing** — Stripe Checkout, webhook handler, trial/upgrade/cancel flows | Underlying Stripe platform behavior |
| **Affiliate payouts** — Stripe Connect Express onboarding, attribution, commission calc, transfers | Full PCI-DSS certification (Stripe Checkout / Elements keeps you out of scope by design) |
| Stripe API key handling + rotation posture | Social engineering / phishing simulations |
| Stripe coupon / promotion code usage (`STRIPE_COUPON_VIP`, `STRIPE_COUPON_BEA_CREATOR`) | Continuous bug bounty (separate post-launch decision) |
| Refund / dispute / chargeback handling | Vercel / Railway platform configs (separate IaC audit) |
| Audit log of every state-changing payment event | |
| Authentication on payment-affecting endpoints | |
| Idempotency posture across all webhook + payout paths | |
| **Tier-gating enforcement** — daily AI quotas, element/preset limits, Pro-only features, retention windows | |
| **AI cost abuse** — Anthropic + Gemini API key handling, rate limits, quota enforcement | |
| **File upload** — 100MB videos, 4 formats, Supabase Storage abuse vectors | |
| Affiliate fraud — self-referral, attribution-window manipulation, cookie/click stuffing | |

---

## 3. Threat model

| Threat | Concern level | Specific risk |
|---|---|---|
| **S**poofing | **Critical** | Forged Stripe webhook triggers fake subscription state change or affiliate payout |
| **T**ampering | **Critical** | Affiliate self-refers and earns commission on own subscription; user manipulates tier via client-side flag |
| **R**epudiation | High | Disputed transfer to affiliate with no audit log; missing trail for subscription tier changes |
| **I**nformation disclosure | High | Stripe customer/account IDs leaked cross-user; affiliate dashboard exposes other affiliates' codes/earnings |
| **D**enial of service | **High for AI** | Trial user burns through Anthropic/Gemini quota costing thousands in API fees; webhook replay creating duplicate transfers |
| **E**levation of privilege | **Critical** | Trial/Director user accesses Pro-only features (video analysis, API, white-label) via client tampering |

**The four highest-priority audit findings for KLING specifically** are:

1. **Unverified Stripe webhook signatures** — the textbook bug. Stripe's docs make this trivially fixable; the bug appears in ~30% of new integrations. KLING has subscription webhooks AND Connect webhooks — both must be verified.
2. **Client-trusted tier / feature flag** — UI sends `{ tier: "pro" }` instead of server reading the subscription state from Supabase. Attacker bypasses paywalls.
3. **AI cost abuse** — no per-user daily quota enforcement on Anthropic / Gemini calls means one bad actor can drain thousands in API spend before you notice.
4. **Affiliate self-referral** — same email / payment method / device / IP as the referrer earning 15% commission on their own subscription. Common pattern, hard to catch retroactively.

Allocate the most audit time to those four.

---

## 4. Audit phases

### Phase 1 — Recon (1-2 days)

- [ ] Inventory every tRPC route, distinguishing payment-affecting vs read-only vs AI-calling
- [ ] Locate the Stripe webhook handler(s) — confirm signature verification call is present and not just a no-op. Note: subscription webhooks and Connect webhooks may be separate endpoints — both need separate verification.
- [ ] Inventory every place a Stripe key is read from env / config / secrets manager (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, plus 4 product IDs and 4 price IDs and 2 coupon IDs from `.env`)
- [ ] Inventory every place `ANTHROPIC_API_KEY` and Gemini keys are loaded — these are the AI cost-exposure vectors
- [ ] Document the **subscription lifecycle** end-to-end: signup → trial → checkout → active → tier change → cancel → past_due → terminated
- [ ] Document the **affiliate flow**: application → approval → referral code generation → click attribution → 30-day window → conversion → commission calc → Stripe Connect Express transfer
- [ ] Document the **coupon flow** — how `STRIPE_COUPON_VIP` and `STRIPE_COUPON_BEA_CREATOR` are applied (URL? admin grant? invitation code?)
- [ ] Map all tier-gated features and where each is enforced (server-side, client-side, both)
- [ ] Confirm `apps/api/src/services/` Stripe service is the *only* place Stripe SDK is called (no duplicate code paths)

**Deliverable:** Three flow diagrams (subscription, affiliate, coupon) + tier-gating matrix + Stripe surface map.

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

#### Stripe Connect Express (affiliate payouts — confirmed in use)
- [ ] Onboarding link uses `account_links` with short expiration, single-use, tied to a session
- [ ] Each connected account is tied to exactly one affiliate in your DB; no shared accounts
- [ ] **Self-referral check** — at attribution time, verify the converting user is not the same as the affiliate (same email domain, same payment method fingerprint, same IP/device within reason)
- [ ] Commission rate (15%) is server-side constant, never read from client request
- [ ] 30-day attribution window is enforced server-side on the conversion event, not on the click event
- [ ] Referral codes are normalized (case-insensitive, trimmed) so `YOURNAME2024` and `yourname2024` don't both attribute
- [ ] Connected account capabilities are minimum needed (`transfers` only, not `card_payments`)
- [ ] Transfer creation is idempotent (same subscription period can't be paid out twice)
- [ ] Refunded subscriptions claw back the commission (otherwise affiliates can collude with users for refund-fraud)
- [ ] Connect webhook (account.updated, transfer.failed) handled separately from subscription webhook, with its own signature verification

#### Subscription billing
- [ ] Trial creation rate-limited per email + per IP + per payment method fingerprint (prevents trial farming)
- [ ] Subscription tier read from Supabase / Stripe server-side on every request — never trust a client-side `user.tier` flag
- [ ] Tier change (upgrade/downgrade) goes through Stripe, then webhook updates DB — not direct DB write from client
- [ ] Cancel-with-refund and cancel-at-period-end paths both tested
- [ ] Past-due / dunning state correctly degrades access (no Pro features for an unpaid Pro subscription)
- [ ] Subscription create webhook (`customer.subscription.created`) and tier-change webhook (`customer.subscription.updated`) both update tier atomically with the user record

#### Coupon abuse
- [ ] `STRIPE_COUPON_VIP` and `STRIPE_COUPON_BEA_CREATOR` cannot be applied via URL parameter or self-service — admin grant only OR redemption code with single-use enforcement
- [ ] Coupon application is logged with actor (admin user) and reason
- [ ] If redemption codes exist: each code is single-use, time-bound, and tied to a specific email at issue time
- [ ] No coupon stacking that produces negative subscription cost

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

#### Tier-gating enforcement (Pro vs Director vs Trial vs VIP vs BEA Creator)
- [ ] Every Pro-only endpoint (`/analyze` video analysis, API access, white-label) checks tier server-side from current Supabase user state
- [ ] Daily AI prompt quota (10/day for Trial) enforced with a server-side counter that resets atomically — not a JS countdown
- [ ] Element library limits (100 for Director, unlimited for Pro) enforced at write time, not just at display time
- [ ] Preset library limits (25 for Director) same
- [ ] Retention policy (14/30/90 days based on tier) actually purges expired content — verify the cron / worker exists and runs
- [ ] Tier-gating is checked in tRPC middleware, not per-procedure (consistency)
- [ ] Switching tier mid-period correctly updates limits (downgrade from Pro to Director immediately re-enforces 100-element cap)
- [ ] No public tier-bypass via API access endpoint (Pro feature — paradox if a Trial user could call it)

#### AI cost abuse — Anthropic + Gemini
- [ ] `ANTHROPIC_API_KEY` and Gemini keys loaded from secrets manager, never logged
- [ ] Per-user daily token budget enforced (not just per-request) — a single user shouldn't be able to spend $X/day on AI without you knowing
- [ ] Per-user concurrent-request limit (prevents parallel-flooding within rate limit)
- [ ] 100MB video upload to `/analyze` carries the largest cost-per-call risk — confirm Pro/VIP/BEA-Creator tier check happens *before* the file uploads, not after
- [ ] Failed AI calls are retried with backoff — not infinite-loop retry on a 5xx (which could rack up cost)
- [ ] Cost monitoring + alerting wired up (Anthropic + Google Cloud billing alerts, daily spike alerts)
- [ ] If video analysis caches results: cache key is content-hash, not user-chosen filename (prevents one user paying for analysis another user can read)

#### File upload abuse (Element Library + Video Analysis)
- [ ] Server-side MIME + magic byte validation on every upload, not just extension (claimed MP4/WebM/QuickTime/AVI for video; images and PDFs separately)
- [ ] 100MB hard cap enforced server-side
- [ ] Supabase Storage bucket configured with no public listing
- [ ] Signed URLs for downloads, short expiry
- [ ] Files served from a different origin than the app (prevents stored-XSS via uploaded SVG, HTML, etc.)
- [ ] PDF uploads validated (server-side parse or pdf-magic-byte check) to prevent malicious-PDF distribution via your CDN
- [ ] Auto-expiration job (7 days, extendable) actually runs and removes files from Supabase Storage, not just DB rows (orphaned files = ongoing storage cost + retention liability)
- [ ] Per-tier storage quotas enforced before upload accepted

#### AI prompt injection (KLING-specific)
- [ ] User-supplied prompt text fed to Claude/Gemini cannot exfiltrate system prompt or other users' data
- [ ] Video analysis prompts treat the video content as untrusted input — model output is rendered as text, not parsed as instructions
- [ ] Generated Kling payloads are validated server-side against the schema in `packages/director-knowledge/schemas/` before being shown to user (defense vs prompt-injection that produces malformed payloads claiming to be legitimate)
- [ ] No tool-use capability exposed to the AI that would let it call internal APIs

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

## 5. `reaper` role for the KLING audit

Same proxy-record-replay-mutate pattern as the LiveIQ audit, with the KLING-specific mutation set:

**Subscription path:**
- Replay subscription webhook with valid signature but stale timestamp (idempotency check)
- Replay with tampered signature (must reject)
- Tamper with tRPC payloads that claim to set user tier (`{ tier: "pro" }` from a Trial session)
- Apply `STRIPE_COUPON_VIP` via every imaginable channel (URL param, request body, header) to confirm it's rejected outside admin grant

**Affiliate path:**
- Self-refer: sign up as affiliate with one email, sign up as user with similar email and use own referral code — confirm commission is *not* paid out
- Submit conversion with `referral_code` that doesn't exist — confirm rejected, not silently dropped
- Manipulate the attribution timestamp to extend the 30-day window
- Tamper with commission rate in any request body (must be ignored, recomputed server-side at 15%)
- Replay transfer webhook to test double-payout protection

**AI cost path:**
- Hit `/analyze` 200 times in a minute as a Trial user — confirm rate limit + tier check
- Upload 100MB video as a non-Pro user — confirm rejection happens before processing cost
- Submit a prompt-injection payload aimed at extracting the system prompt — confirm filtered

**File upload:**
- Upload `.svg` with embedded JS, renamed `.png` — confirm rejected
- Upload `.pdf` claiming to be an image — confirm rejected
- Upload 101MB file — confirm rejected at gateway, not after full upload

Most of these need ~5-10 line additions to `reaper`'s replay config. The self-referral test in particular has high payoff — it's a class of bug that's almost never caught by scanners.

---

## 6. Estimated effort

| Phase | Effort |
|---|---|
| Phase 1 Recon | 1-2 days |
| Phase 2 Automated scans | 1 day |
| Phase 3 Manual review | 4-6 days |
| Phase 4 Remediation | 2-4 weeks (depends on findings) |
| Phase 5 Final gate | 1 day |
| **Total elapsed** | **3-5 weeks** |

Revised up from v0.1's 2-4 weeks. The README revealed the surface area is broader than initially scoped: subscription billing **plus** Stripe Connect Express **plus** tier-gating **plus** AI cost exposure **plus** file uploads. Each adds its own threat surface. Higher density of Critical findings is normal for first-time SaaS+billing audits.

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

Most v0.1 questions answered by the README. Remaining:

1. Is KLING-Director already processing real money (active subscriptions + affiliate payouts running), or pre-launch / soft-launch?
2. How are `STRIPE_COUPON_VIP` and `STRIPE_COUPON_BEA_CREATOR` actually granted — admin UI? Database flag? Self-applied via URL? (Determines coupon-abuse threat surface size.)
3. Bug bounty program plan post-launch?
4. Has any AI cost spike or anomalous spending event occurred? (If yes, audit prioritizes that vector higher.)
5. Is there an admin panel? If yes, it needs its own threat model (admin-only endpoints, admin role escalation).
6. Are the Anthropic + Gemini keys per-environment, or shared across dev/staging/prod?

---

## 9. Concrete next steps

1. **5-minute pre-audit smoke tests** — settle critical questions before committing the full audit:
   - Submit a bad-signature webhook to staging — confirm 400/401/403, not 200.
   - Try to apply `STRIPE_COUPON_VIP` via every URL/header/body channel as an unauth user — confirm rejected.
   - As a Trial user, set `tier: "pro"` in any request body — confirm tier is recomputed server-side.
   - Sign up as affiliate, sign up as user with same payment method, use own code — confirm conversion is flagged.
2. Run Phase 1 Recon — full surface mapping.
3. Coordinate with the LiveIQ audit if both happen in parallel — share `reaper` infra and Semgrep config.

---

## 10. Coordination with LiveIQ audit

Same engineer can run both audits sequentially (KLING first, since it's tighter and the highest-density-Critical area) OR two engineers in parallel.

Shared infrastructure:

- One `reaper` setup, two replay configs
- Shared Semgrep config (extended with payment rules for KLING)
- Shared remediation tracker
- Shared final-gate process

If running sequentially, allow 1-week gap so the team isn't context-switching between data-protection mode and payments mode mid-audit.
