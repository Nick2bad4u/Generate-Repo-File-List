# Toklytics-LiveIQ Mobile Wrapper — Plan

> Working name: **liveiq-mobile**
> Status: Draft v0.2
> Target: iOS + Android wrapper around `Toklytics-LiveIQ`
> Tooling lead: `full_web_converter_To_flutter_App` (forked)

> **Scope correction from v0.1:** The repos `portal-uk`, `portal-us-ca`, and `BEA_Creator_Portal` are dead — their functionality was consolidated into `Toklytics-LiveIQ`. The wrapper targets one web app, not three. Region differentiation is already handled inside LiveIQ, so no app-side region picker is needed.

---

## 1. Why this exists

Creators live on their phones. A mobile-installed app changes engagement vs a bookmarked PWA in three concrete ways:

1. **Push notifications** — payout posted, LIVE schedule reminder, new training module, gift milestone hit, realtime coach alerts
2. **Home screen presence** — LiveIQ is one tap away, not three navigation steps
3. **App store credibility** — for an agency, having an iOS+Android app signals legitimacy to new creators

A Flutter wrapper around the existing LiveIQ web app is the fastest path to all three without rebuilding the UI natively. The forked `full_web_converter_To_flutter_App` is designed for exactly this conversion.

---

## 2. Scope

### In scope (v1)
- Single Flutter app wrapping Toklytics-LiveIQ
- Native push notifications
- Biometric / native auth on app open
- Deep linking from emails / SMS into specific LiveIQ screens
- Offline detection + graceful fallback screens
- iOS + Android distribution

### Out of scope (v1)
- Native UI replacement (we wrap web, we don't rewrite)
- Tablet-optimized layouts (portrait phone only)
- Apple Watch / Wear OS companions
- In-app purchases (Apple/Google would take 30% of any payout flow — keep payments web-only)
- Region picker — LiveIQ already routes by creator profile, not by app variant

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FLUTTER APP (single binary)                                │
│  - Native auth shell (biometric, secure storage)            │
│  - Push notification handler                                │
│  - Deep link router                                         │
│  - WebView host (flutter_inappwebview)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ JS bridge
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  TOKLYTICS-LIVEIQ (existing web app)                        │
│  - Detects "in BEA app" via UA string                       │
│  - Hides web-only chrome (browser back, footer)             │
│  - Calls bridge for native features (push opt-in, biometric)│
│  - Routes user by their profile region (no app-side switch) │
└─────────────────────────────────────────────────────────────┘
```

LiveIQ stays the source of truth. The Flutter shell adds native capabilities and store distribution. Total native code stays under ~2000 LOC since multi-portal complexity is gone.

---

## 4. Module breakdown

### 4.1 Flutter shell (this new repo)

Built from `full_web_converter_To_flutter_App` as starting point. Likely customizations:

- Single target URL (Toklytics-LiveIQ production / staging)
- BEA brand splash + theme
- Replace generic WebView with `flutter_inappwebview` for the JS bridge
- Add `firebase_messaging` for push (FCM works on both platforms)
- Add `local_auth` for biometrics
- Add `app_links` for deep linking

### 4.2 Toklytics-LiveIQ additions

LiveIQ needs a small "mobile mode" addition:

- Detect UA: `BEA-Mobile/1.0`
- Apply `.in-app` CSS class to hide elements that don't make sense in-app (browser back button, footer with marketing links)
- Expose JS calls that the bridge intercepts: `bea.registerPush()`, `bea.requestBiometric()`, `bea.openExternal(url)`

Coordinate with whoever owns the LiveIQ repo so this lands ~1 sprint before the mobile MVP needs it.

### 4.3 Push notification backend

Cloudflare Worker or Supabase Edge Function that:

- Receives event triggers (payout posted, LIVE schedule change, training video ready)
- Looks up creator's FCM tokens (stored on portal sign-in)
- Sends push via FCM HTTP v1 API

Server-side, not in this repo's scope — but the Flutter side registers tokens and the portals provide the trigger events.

---

## 5. Distribution

### iOS
- Apple Developer Program membership ($99/year per org)
- App Store Connect listing
- Privacy nutrition labels (must declare every data type the wrapped web app collects)
- Sign-in with Apple required if any other social login is offered
- Age rating: likely 17+ given creator/streaming domain — confirm
- App Tracking Transparency prompt if any analytics SDK tracks across apps

### Android
- Google Play Developer account ($25 one-time)
- Play Console listing
- Data Safety form (similar to Apple's privacy labels)
- Target API level kept current (Play enforces a rolling minimum)

### Compliance gotchas to verify before submission
- **Apple §4.7 "minimum functionality"**: Pure web wrappers can be rejected. Solution: native push, biometric, deep links, and offline screen are enough native features to clear this.
- **Google "spam" policy**: Same concern. Same solution.
- **Both stores**: TikTok-adjacent apps face extra scrutiny. Be very clear in the listing this is a *creator portal* for an agency, not a TikTok client.
- **GDPR + UK GDPR**: Privacy policy URL must be in store listing. Already required by §portal-security-audit-spec.
- **Push notification permissions**: iOS 13+ requires explicit opt-in. Android 13+ requires runtime permission.

---

## 6. Phased rollout

### Phase 0 — Spike (3 days)

Goal: Prove `full_web_converter_To_flutter_App` can wrap Toklytics-LiveIQ with a WebView and load it on an iOS Simulator + Android Emulator.

- Clone fork
- Configure with the LiveIQ staging URL
- Brand splash, smoke test
- Verify session cookies persist across app launches
- Test the trickiest UX paths: CSV upload, screenshot upload, live coaching feed (websocket / SSE)

**Deliverable:** A `.apk` + `.app` on dev machines, demoed.

**Decision gate:** Is the WebView UX acceptable? Specifically: scrolling, keyboard handling, file pickers, camera access for screenshot uploads, realtime coaching feed stability inside a WebView.

---

### Phase 1 — MVP (2-3 weeks)

- [ ] BEA brand theming
- [ ] Native auth shell with biometric lock
- [ ] FCM push notifications (registration + receive)
- [ ] Deep linking (`https://m.bea.com/...` → app)
- [ ] Offline screen
- [ ] CI: build pipeline for both platforms (Codemagic, Bitrise, or GitHub Actions)

Faster than v0.1's estimate because the multi-portal selector / region routing complexity is gone.

**Deliverable:** TestFlight + Play Internal Testing builds installable by the BEA team.

---

### Phase 2 — Store submission (2-4 weeks elapsed, mostly waiting on reviews)

- [ ] Privacy policy + DPA finalized
- [ ] App Store + Play Store listings drafted (copy, screenshots, video preview)
- [ ] Privacy labels / Data Safety form completed
- [ ] Submit to App Store + Play Store
- [ ] Handle review feedback (expect 1-2 rounds)

**Deliverable:** Apps published.

---

### Phase 3 — Post-launch

- Auto-update mechanism (CodePush or similar, optional)
- Analytics (privacy-respecting — Plausible/PostHog, not GA)
- Crash reporting (Sentry)
- A/B test push notification copy/timing

---

## 7. Tech stack decisions

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Flutter | Single codebase, your fork is already Flutter-based |
| WebView | `flutter_inappwebview` | Most capable bridge; better than the official one |
| Push | Firebase Cloud Messaging | Works on both platforms, free at this scale |
| Auth shell | `local_auth` (biometrics) + `flutter_secure_storage` | Keychain / Keystore backed |
| Deep links | `app_links` | Universal Links + App Links |
| State | Riverpod or Bloc | Either fine; pick one team preference |
| CI | GitHub Actions + Codemagic for iOS signing | Free tier handles low volume |
| Distribution | TestFlight + Play Internal Testing for staging | Standard |

---

## 8. Cross-cutting dependency: `toklytics-liveiq-security-audit-spec.md`

**A mobile wrapper inherits every web vulnerability.** If the audit finds Critical or High issues, the mobile launch slips with the web launch. Plan the security audit and the mobile wrapper as parallel workstreams gated by the same go-live decision.

Specifically, mobile adds these *new* security considerations on top of the audit:

- [ ] WebView doesn't expose JS bridge methods that grant capabilities the website itself doesn't have (review `bea.*` bridge surface)
- [ ] Certificate pinning for LiveIQ API calls (prevent MITM on hostile WiFi)
- [ ] Jailbreak / root detection (optional — low value vs effort for v1)
- [ ] Deep link handlers validate the URL before navigation (prevent UXSS via crafted deep links)
- [ ] App Transport Security configured (no `NSAllowsArbitraryLoads`)
- [ ] Android `usesCleartextTraffic: false`

Add these to the audit's Phase 3 checklist before mobile launch.

---

## 9. Risks & open questions

| Risk | Mitigation |
|---|---|
| Store rejection for "minimum functionality" | Phase 1 adds enough native features (push, biometric, deep links, offline) to clear this. Document the native-only features in the store listing copy. |
| WebView UX feels janky | Phase 0 spike answers this before further investment. |
| Maintenance burden of one more repo | Single binary, web portals carry the UI updates — Flutter shell rarely changes after v1. |
| TikTok-adjacent rejection risk | Lead with "creator agency portal" framing in the listing, avoid the word "TikTok" in the app name and primary description. |
| Apple/Google policy changes | Acceptable risk; affects everyone equally. |

**Open questions:**

1. ~~One single app with region picker, or three branded apps?~~ **Resolved by scope correction** — one app wrapping LiveIQ, region routing inside the web app.
2. Native deep links require domain ownership of `m.bea.com` (or similar). Is that domain available / planned?
3. Push notification opt-in flow: on first launch (early, low conversion) or after first meaningful action (later, higher conversion)?
4. Is the agency comfortable with the 17+ rating likely required, or do we need to scrub anything that pushes the rating up?
5. Are creators expected to install this themselves, or will the agency push it via onboarding?
6. Does Toklytics-LiveIQ's realtime coaching feed work reliably inside a WebView? (Answered during Phase 0 spike.)

---

## 10. Concrete next steps

1. Phase 0 spike — 3 days to validate WebView UX works for the actual LiveIQ screens (especially CSV/screenshot upload + the realtime coaching feed, which are the riskiest).
2. Decision gate after spike — go/no-go before committing to Phase 1.
3. If go: create `liveiq-mobile` repo, scaffold per §3, set up TestFlight + Play Internal Testing.
4. Coordinate with `toklytics-liveiq-security-audit-spec.md` work so mobile launch isn't blocked at the end by surprises from the audit.
