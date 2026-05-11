# KLING-Director Mobile Wrapper — Plan

> Working name: **kling-mobile**
> Status: Draft v0.2
> Target: iOS + Android wrapper around `KLING-Director` ([repo](https://github.com/BEA-BOLD-EVOLUTION/KLING-Director))
> Tooling lead: `full_web_converter_To_flutter_App` (forked)
> Companion to: `toklytics-liveiq-mobile-wrapper-spec.md`, `kling-director-security-audit-spec.md`

> **Confirmed scope (from README):** KLING-Director is a self-service SaaS — an AI-powered prompt compiler for Kling video generation. Users sign up via Supabase Auth, pay via Stripe subscription ($5.99 Director / $9.99 Director Pro / $0 VIP / $0 BEA Creator partner / 7-day free trial). It uses Claude Sonnet 4 + Gemini 2.0 Flash. Pro tier offers video analysis (up to 100MB uploads). It has its own affiliate program with Stripe Connect Express for 15% commission payouts. The audience is broader than LiveIQ creators — anyone can sign up.

---

## 1. Why this exists

KLING-Director is a self-service SaaS that creators and prompt engineers will use heavily from their phones (videos are watched, generated, and managed mostly on mobile). A native shell delivers three concrete wins:

1. **Push for billing + AI events** — "Trial ending in 2 days", "Video analysis complete", "Affiliate payout posted", "Subscription renewal failed". Each is high-value and time-sensitive.
2. **Native file picker for video uploads** — the `/analyze` Pro feature takes 100MB videos. The native picker (camera roll, files app) is dramatically better UX than a WebView file input.
3. **App store discoverability** — KLING-Director is a paid SaaS aimed at growth. Store listings are a real acquisition channel for "AI video tool" searches.

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

## 3. Key architectural decision: standalone, not unified

v0.1 of this spec recommended folding KLING into a unified `bea-mobile` app with LiveIQ. The README changes that calculus. **Revised recommendation: standalone `kling-mobile` app.**

### Why standalone wins here
- **Different audiences.** LiveIQ is for BEA's contracted creators. KLING-Director is a public SaaS — anyone can sign up. Most KLING users are not BEA creators. Bundling them in one app means most KLING users carry a dead LiveIQ tab they'll never use.
- **Different brand.** KLING-Director has its own product identity, pricing, affiliate program. It's a growth-channel product. LiveIQ is an agency tool. Distinct positioning calls for distinct store listings.
- **Different store category.** KLING fits "AI tools / Creativity" categories where discoverability matters; LiveIQ fits "Business / Productivity". Separate listings each rank in their best category.
- **Different update cadences.** KLING ships features rapidly (the README shows monthly improvements). LiveIQ is more stable. Coupling them slows KLING.
- **App size.** A single SaaS app loads fast. A combined app with two embedded web experiences is heavier and slower to launch.

### Cost of standalone
- Two store listings to manage (manageable — they're separate brands)
- Duplicate native infrastructure (auth shell, push token, deep-link domain) — actual code overhead is ~500 LOC, not significant
- Two install prompts — but only ever to overlapping users (BEA creators), who get a unified onboarding pitch anyway

### Decision
Standalone `kling-mobile` app, branded as "Kling Director" or similar (not "BEA Kling Director" — keep the brand clean for public market).

The LiveIQ mobile wrapper stays separate as `liveiq-mobile`.

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  FLUTTER APP — kling-mobile (single binary)                  │
│  - Native auth shell (biometric on app open + sensitive ops) │
│  - Push notification handler                                 │
│  - Deep link router                                          │
│  - WebView host (flutter_inappwebview) loading KLING web     │
│  - Native file picker bridged to WebView for /analyze upload │
└──────────────────────────────┬───────────────────────────────┘
                               │ JS bridge
                               ↓
              ┌────────────────────────────────┐
              │  KLING-Director (Next.js web)  │
              │  Hosted on Vercel              │
              │  - Detects "in Kling app" UA   │
              │  - Hides web-only chrome       │
              │  - Calls native bridge for     │
              │    upload, biometric, push     │
              └────────────────────────────────┘
```

**WebView lifecycle:**
- Single WebView, kept warm across app lifecycle
- Session cookies persist (Supabase Auth)
- Hard reload on tier-change webhook (so feature gates refresh)

**JS bridge surface:**
- `kling.registerPush()` — register FCM token with backend after sign-in
- `kling.requestBiometric(purpose)` — gated by `purpose` ("view_billing" or "manage_subscription" or "open_affiliate_dashboard")
- `kling.openExternal(url)` — opens non-app URLs in system browser
- `kling.requireFreshAuth(threshold_seconds)` — KLING calls before showing billing/payout screens
- `kling.pickFile(constraints)` — opens native file picker for `/analyze` 100MB video upload. Returns a temp URL the WebView can POST. Critical UX win.
- `kling.lockApp()` — forces re-auth on resume if anomaly detected

The `pickFile` bridge is the single biggest UX value-add over plain web — WebView file inputs are notoriously janky for large video files. Going native here is worth the 50-100 LOC.

---

## 5. Module breakdown

### 5.1 Flutter shell
- Built from `full_web_converter_To_flutter_App`
- Replace generic WebView with `flutter_inappwebview` for the JS bridge
- Add `firebase_messaging` for push
- Add `local_auth` for biometrics
- Add `app_links` for deep linking
- Add `file_picker` + `image_picker` packages for native upload picker

### 5.2 KLING-Director web app additions
- Detect UA: `Kling-Mobile/1.0`
- Apply `.in-app` CSS class to hide browser back, footer, marketing chrome
- Replace `<input type="file">` on `/analyze` with `kling.pickFile()` bridge call when in-app
- Call `kling.requireFreshAuth(...)` before rendering `/billing` and affiliate dashboard
- Expose `kling.registerPush()` after first sign-in
- Stripe Checkout: render in-app for subscription purchase; verify the redirect-back from Stripe lands on a route the WebView intercepts cleanly (this is the #1 spike risk)
- Test mode visual indicator that's prominent on mobile (banner across the top, distinct color)

### 5.3 Push notification backend
- Worker / Edge Function (likely Vercel Edge or Railway service per stack)
- Receives events from:
  - Stripe subscription webhooks → "Trial ending", "Payment failed", "Subscription renewed"
  - Stripe Connect webhooks → "Affiliate payout posted"
  - AI service callbacks → "Video analysis complete"
- Looks up user's FCM tokens (stored on sign-in)
- Sends push with deep-link target

**Push payload rules (privacy):**
- Never include dollar amounts in cleartext (lock-screen preview = info disclosure on a shared device)
- Use "Payout posted — tap to view" pattern
- Affiliate-specific events never expose other affiliates' info
- Trial-ending push lands on the billing page deep-link, not a generic URL

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

### Phase 0 — Spike (3-5 days)

Goal: Prove the WebView UX works for KLING's three trickiest paths.

- Clone fork
- Configure with KLING staging URL
- **Test 1 (most critical): Stripe Checkout subscription flow inside WebView.** Subscribe to Director tier, return to app, confirm session and tier reflected. If this breaks, fall back to opening Checkout in a Custom Tab (Android) / SFSafariViewController (iOS).
- **Test 2: Stripe Connect Express affiliate onboarding.** This is the highest-risk WebView path — Connect onboarding redirects through Stripe-hosted screens and back, and historically breaks inside WebViews. Confirm the affiliate onboard-and-return works cleanly.
- **Test 3: 100MB video upload via `/analyze`.** Use the native `kling.pickFile()` bridge. Confirm a real 90MB MP4 uploads, the analysis completes, results render. Verify the WebView doesn't OOM during upload progress.
- Side tests: biometric re-prompt timing, deep-link return paths, test-mode banner visibility.

**Decision gates:**
- Stripe Checkout works cleanly in WebView with redirect-back, OR fallback to Custom Tabs works → continue.
- Stripe Connect Express onboarding works → continue. If it breaks: design a "complete onboarding on desktop" out-of-band flow as a hard fallback.
- 100MB video upload completes without crash → continue.

If any of the three fails and has no clean fallback, this spike is the decision gate that ends the project — kling-mobile would be hampered without these flows.

---

### Phase 1 — MVP (3-4 weeks)

- [ ] Single WebView host for KLING staging then prod URL
- [ ] Kling Director brand theming (logo, splash, app icon)
- [ ] Native auth shell with biometric lock
- [ ] `requireFreshAuth` enforced on `/billing` and affiliate dashboard
- [ ] Native `pickFile` bridge for `/analyze` video upload
- [ ] FCM push for subscription + Connect + AI completion events
- [ ] Deep linking (subscription emails / referral codes)
- [ ] Offline screen
- [ ] Test/live mode visual indicator
- [ ] Stripe Checkout fallback (Custom Tabs / SFSafariViewController) if Phase 0 says needed

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
| Stripe Checkout breaks in WebView | Phase 0 spike answers this. Fallback: Custom Tabs (Android) / SFSafariViewController (iOS). |
| Stripe Connect Express onboarding breaks in WebView | Phase 0 spike answers this. Fallback: send affiliates to a desktop-only onboarding URL via email — degraded but functional. |
| 100MB video upload OOM / crash | Use native picker + chunked upload, never load full file into WebView memory. |
| Push payload leaks info on lock screen | "Tap to view" pattern; no amounts in payload. |
| App store rejection for "minimum functionality" | Native push, biometric, file picker, deep links = enough native value to clear the bar. |
| Apple/Google scrutinize subscription apps more | Pre-built compliance: clear privacy policy, subscription terms on the listing, no dark patterns, easy cancel from in-app billing portal link. |
| Trial-ending push annoyance | Limit to one per trial, send 48 hours before expiry, allow disable from settings. |

**Open questions:**

Most prior v0.1 questions are now answered by the README. Remaining:

1. Is KLING-Director already live with active subscriptions and affiliate payouts, or pre-launch / soft-launch?
2. Is mobile launch a v1 priority, or wait until web is stable / past N MRR threshold?
3. Domain for mobile deep links — `m.kling-director.com`? Or use the existing domain with Universal Links?
4. App name on stores — "Kling Director" or branded distinctly?
5. Is there a desktop-style admin panel that wouldn't translate well to mobile? (If yes, scope it out and show a "view on desktop" message in the app for those routes.)

---

## 10. Concrete next steps

1. Phase 0 spike — 3-5 days, focused on the three critical WebView paths in §7.
2. Decision after spike — go / fall back to Custom Tabs / pivot to native-only billing screens.
3. If go: create `kling-mobile` repo (separate from `liveiq-mobile`), scaffold per §4.
4. Coordinate Phase 0 timing with the LiveIQ mobile spike — same engineer, same week, saves setup time.
5. Cross-reference the audit spec — items in §8 of this doc go into the audit's Phase 3 checklist before mobile launch.
