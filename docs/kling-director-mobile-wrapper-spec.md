# KLING-Director Mobile Wrapper — Plan

> Working name: **kling-mobile** (placeholder — depends on whether this folds into liveiq-mobile, see §3)
> Status: Draft v0.1
> Target: iOS + Android wrapper around `KLING-Director` ([repo](https://github.com/BEA-BOLD-EVOLUTION/KLING-Director))
> Tooling lead: `full_web_converter_To_flutter_App` (forked)
> Companion to: `toklytics-liveiq-mobile-wrapper-spec.md`, `kling-director-security-audit-spec.md`

> **Working assumptions** (please correct):
> - KLING-Director is a creator-facing TypeScript web app
> - Creators use it to do something involving payments via Stripe (Kling AI video generation? Campaign management? Payout requests?)
> - It has its own authentication, separate from or shared with LiveIQ
> - It's accessed from mobile devices regularly enough that a native wrapper would matter
>
> Several decisions in this spec hinge on these assumptions. The Phase 0 spike + your answers to §10 questions will firm them up.

---

## 1. Why this exists

If KLING-Director is creator-facing and money-handling, a mobile app moves the needle in ways that matter more than for LiveIQ:

1. **Push notifications for payment events** — payout posted, refund issued, dispute opened, account verification needed. Payment events have higher emotional weight for creators than analytics updates, so push delivers outsized value here.
2. **Biometric auth on every money-touching screen** — fingerprint/Face ID friction at the right moment is *desirable* for payment apps. Reduces fraud risk on lost/stolen devices.
3. **App store credibility for a money-handling tool** — creators are more cautious about typing financial info into a browser bookmark than a downloaded app. The store presence directly improves conversion on payment setup.

---

## 2. Scope

### In scope (v1)
- Native shell wrapping KLING-Director
- Biometric prompt before any money-affecting screen (not just app open)
- Native push for payment events (payout, refund, dispute, verification)
- Deep links into specific KLING screens from email / SMS
- Offline screen with explicit "payments unavailable offline" messaging
- iOS + Android distribution

### Out of scope (v1)
- Native payment UI (Apple Pay, Google Pay) — those would force you into the 30% in-app purchase tax. Stick with web/Stripe Checkout for compliance.
- Stored cards in the native shell — Stripe Checkout handles this; the app should never touch card data.
- Native UI replacement (we wrap web)
- Watch / Wear OS companions
- Tablet-optimized layouts

---

## 3. **Key architectural decision: standalone app or fold into LiveIQ mobile?**

This is the highest-leverage decision in this spec.

### Option A: Standalone `kling-mobile` app
**Pros:**
- Cleaner store listing (payments-focused brand vs analytics-focused)
- Different update cadence from LiveIQ
- Failure isolation (a KLING-mobile crash doesn't take down LiveIQ)
- Different audiences if KLING is creator-only and LiveIQ is broader

**Cons:**
- Two store listings to maintain (Apple + Google × 2 = 4 listings)
- Two install prompts to creators ("download our other app too")
- Duplicate native infrastructure (auth shell, push, deep links)
- Higher ongoing maintenance cost
- Apple/Google may scrutinize "another wrapper from same publisher" more

### Option B: Single `bea-mobile` app, tabbed UI hosting both LiveIQ + KLING
**Pros:**
- One install for creators
- Shared auth shell, push token, deep-link domain
- One store listing, simpler ops
- Better creator UX — one place to do everything BEA
- Aligns with "Toklytics-LiveIQ absorbed the portals" consolidation pattern you already chose

**Cons:**
- Larger app size
- Cross-team coordination on releases (whoever owns LiveIQ + whoever owns KLING share the mobile release train)
- One bug can block the other's update

**Recommendation: Option B**, for the same reason you consolidated the three portals into LiveIQ — operational simplicity wins for an agency at your scale. The cons are real but manageable. The mobile shell becomes a routing layer that loads the right web app based on tab selection.

The rest of this spec assumes **Option B**, with a `kling-mobile` repo only if you explicitly choose Option A.

---

## 4. Architecture (assuming Option B)

```
┌──────────────────────────────────────────────────────────────┐
│  FLUTTER APP — bea-mobile (single binary)                    │
│  - Bottom-tab navigator: [LiveIQ] [KLING] [Profile]          │
│  - Native auth shell (biometric on app open + sensitive ops) │
│  - Push notification handler (routes by event source)        │
│  - Deep link router (URLs resolve to a tab + path)           │
│  - Two WebView hosts (one per tab, kept warm)                │
└──────────────────────────────┬───────────────────────────────┘
                               │ JS bridge
                ┌──────────────┴──────────────┐
                ↓                             ↓
   ┌────────────────────────┐   ┌────────────────────────────┐
   │  Toklytics-LiveIQ      │   │  KLING-Director            │
   │  (analytics + coach)   │   │  (payments + ?)            │
   └────────────────────────┘   └────────────────────────────┘
```

**WebView lifecycle:**
- Two WebViews, kept alive in memory (avoids reload pain when switching tabs)
- Each has its own cookie store (sessions don't leak across tabs)
- App brings the foreground tab's WebView to the front, suspends the other after N minutes inactive

**JS bridge surface (extends the LiveIQ-only bridge):**
- `bea.registerPush()` — shared
- `bea.requestBiometric(purpose)` — gated by `purpose`; the WebView passes "view_payout" or "trigger_payout" so the native shell can decide if a fresh prompt is needed
- `bea.openExternal(url)` — shared
- `bea.lockApp()` — KLING calls this if it detects unusual activity (forces re-auth on resume)
- `bea.requireFreshAuth(threshold_seconds)` — KLING requests a re-prompt if last biometric is older than N seconds before showing a money-affecting screen

The `requireFreshAuth` mechanism is the security teeth: even with a valid session cookie, the app re-prompts biometric before showing payout balances or initiating new payouts.

---

## 5. Module breakdown

### 5.1 Flutter shell additions vs the LiveIQ-only spec
- Tab navigation
- Per-tab WebView management
- Push routing logic (event payload determines which tab opens)
- Bridge surface extended with `requireFreshAuth` and `lockApp`

### 5.2 KLING-Director web app additions
- Detect UA: `BEA-Mobile/1.0`
- Apply `.in-app` CSS class
- Call `bea.requireFreshAuth(...)` before rendering money-affecting screens
- Expose `bea.registerPush()` after first sign-in
- Test mode visual indicator that's bigger than usual (mobile screen real estate makes test/live confusion riskier)

### 5.3 Push notification backend
- Worker / Edge Function that receives payment events from KLING (via Stripe webhooks or internal events)
- Looks up creator's FCM tokens
- Sends push with deep-link target

**Critical:** push payloads must never contain financial amounts in cleartext (notification preview on locked screen = info disclosure). Use "Payout posted" with a "Tap to view" pattern instead.

---

## 6. Distribution

Same as LiveIQ mobile spec, with payment-specific additions:

### iOS
- App Store guideline §3.1.1: physical goods / services *outside* the app can be paid for outside Apple's IAP. Payouts to creators (money flowing *out*) are clearly out of IAP scope — Apple won't take a cut. Document this in the submission notes.
- Privacy nutrition labels must declare financial data category
- Age rating likely 17+ stays the same

### Android
- Play Console "financial services" category may apply — verify
- Data Safety form: financial data declared

### Both
- **Stripe-specific compliance note**: if Stripe Connect is used and creator KYC happens in your app, the privacy policy needs to explicitly cover identity verification data (passport scans, etc.) and retention thereof.

---

## 7. Phased rollout

### Phase 0 — Spike (3-5 days, longer than LiveIQ spike)

Goal: Prove the WebView UX works for KLING's specific screens — especially Stripe Checkout flows, KYC document uploads, and any test-vs-live mode indicators.

- Clone fork
- Configure with KLING staging URL
- Test: Stripe Checkout redirect-and-return inside WebView
- Test: file upload (KYC docs if applicable)
- Test: deep-link return from external auth (e.g., Stripe Connect onboarding)
- Test: payment confirmation flow round-trip

**Decision gates:**
- Does Stripe Checkout work cleanly in the WebView, including the redirect back? (Common failure mode: redirect drops the session.)
- Does the biometric re-prompt fire at the right moments?
- Does the deep-link return-from-Stripe-Connect work? (Notorious for breaking inside WebViews.)

---

### Phase 1 — MVP (3-4 weeks)

- [ ] LiveIQ tab functional (per existing mobile spec)
- [ ] KLING tab functional
- [ ] BEA brand theming (shared)
- [ ] Native auth shell with biometric lock
- [ ] `requireFreshAuth` enforced on money-screens
- [ ] FCM push for payment events
- [ ] Deep linking with tab routing
- [ ] Offline screen
- [ ] Test/live mode visual indicator coordinated with KLING web

**Deliverable:** TestFlight + Play Internal Testing builds.

---

### Phase 2 — Store submission (2-4 weeks)

Same as LiveIQ spec, plus payment-specific submission notes.

---

### Phase 3 — Post-launch

- Add Apple Pay / Google Pay only if business case justifies the 30% tax (almost never for payouts-out)
- Add saved payment methods only if it stays compliant (Stripe Elements via webview is fine)

---

## 8. Security cross-cut

This wrapper inherits all of `kling-director-security-audit-spec.md`'s findings plus the WebView-specific items from `toklytics-liveiq-mobile-wrapper-spec.md §8`. Additionally:

- [ ] The JS bridge surface for KLING is reviewed line-by-line; nothing exposes capabilities beyond what the web origin already has
- [ ] `requireFreshAuth` cannot be bypassed by JS (the native shell decides, not the web app)
- [ ] Push notification payloads scrubbed of financial amounts
- [ ] Test mode: app shows a giant banner when running against Stripe test mode to prevent staff confusion when handling real creator support cases
- [ ] Biometric data never leaves the device (Apple/Google handle this by default, but verify your bridge code doesn't accidentally serialize biometric results)

---

## 9. Risks & open questions

| Risk | Mitigation |
|---|---|
| Stripe Checkout breaks in WebView | Phase 0 spike answers this. Fallback: open Checkout in external browser via SFSafariViewController / Custom Tabs. |
| Push payload leaks info on lock screen | "Tap to view" pattern; no amounts in payload. |
| One bug blocks both tabs' updates | Mitigated by careful release management; LiveIQ + KLING teams sync on mobile release schedule. |
| Apple/Google scrutinize money-handling apps more | Lean into compliance: clear privacy policy, transparent fee structure, no dark patterns. |
| Creators confuse test mode for live | Giant visual indicator in test mode (banner, color band). |

**Open questions:**

1. **Confirm KLING-Director's purpose.** I'm guessing payments orchestration; if it's something else (campaign management, AI video generation orchestration), some scope items shift.
2. **Standalone app or unified bea-mobile app?** §3 recommendation is unified — confirm or override.
3. Is KLING-Director creator-facing, staff-only, or both?
4. Does KLING-Director share auth/sessions with LiveIQ, or are they separate logins? (Affects the bridge design.)
5. Stripe Connect, standard Charges, or both? (Affects the WebView flow for onboarding screens.)
6. Test mode used regularly, or only for development? (Affects the visual-indicator requirement.)

---

## 10. Critical questions to answer for both KLING specs

To refine both `kling-director-security-audit-spec.md` and this mobile spec, please share:

1. **One-paragraph description of what KLING-Director does** for the agency
2. **Who uses it** — creators, internal staff, both
3. **Whether it shares a session with LiveIQ** or has separate auth
4. **Stripe usage pattern** — Connect for creator payouts, standard Charges for billing, both, or other
5. **Is it live yet** with real money flowing
6. **Does it integrate with Kling AI** (the video gen tool) or is "KLING" branding-only

Even short bullet answers will firm up both specs significantly.

---

## 11. Concrete next steps

1. Answer §10 — these are the highest-leverage clarifications for both KLING specs.
2. Phase 0 spike — 3-5 days, focused on Stripe Checkout / Connect WebView compatibility.
3. Architectural decision on §3 (standalone vs unified app).
4. Coordinate Phase 0 timing with the LiveIQ mobile spike — same engineer, same week, saves setup time.
