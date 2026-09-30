# SmartRoute — Legal, Compliance, and Privacy Guardrail Architecture (COMPLIANCE.md)

This document establishes the binding legal, privacy, and architectural guardrails enforced by **Agent 0 (`ComplianceGuardrailAgent`)** across the entire SmartRoute production application, backend pipeline, and cross-platform mobile clients (Android APK + iOS).

Every agent, subsystem, and external integration in SmartRoute MUST strictly adhere to these policies. No workaround or scraping of restricted third-party domains is permitted under any circumstance.

---

## 1. Google Maps Platform Terms of Service (ToS)

### Usage & Free Tier Limits
- **Monthly Credit:** Google Maps Platform provides a **$200 monthly free tier credit** (~40,000 Directions or Distance Matrix API calls).
- **Graceful Degradation:** To prevent unexpected billing overruns or app crashes if quota (`OVER_QUERY_LIMIT`) is exceeded or if an API key is unconfigured, **Agent 2 (`TrafficAndIncidentAgent`)** automatically falls back to cached corridor geometries while setting `is_live: false` and displaying a visible warning badge to the user (`⚠️ Live Google Maps data temporarily unavailable (`{reason}`). Using cached corridor geometry.`).

### Caching & Storage Restrictions
- **Prohibited Caching:** Pre-fetching, bulk downloading, indexing, or permanently storing Google Maps Content (such as turn-by-turn steps, polylines, or business details) outside of the service is **strictly prohibited**.
- **Permitted Caching:** Only specific "Google ID" values (such as `place_id` or `pano_ID`) may be cached. Temporary performance caching (e.g. up to 30 days for Address Validation or specific grounded outputs) is permitted only where explicitly authorized in API documentation. SmartRoute treats all live polylines and directions as **ephemeral session data** that is never stored in persistent databases.

### Attribution Requirements
- **Mandatory Attribution:** Whenever map data or turn-by-turn guidance is displayed outside of an interactive Google Map widget, the UI must prominently display required attribution notices (`Powered by Google` / `Map data: Google`).
- **Unmodified Display:** Attribution logos, copyright notices, and trademark text must never be hidden, obscured, or modified.

---

## 2. Google Play Developer Program Policies (Android APK)

### Data Safety Section Declaration
- SmartRoute must accurately disclose all collected data in the Google Play Data Safety Section before app store submission:
  - **Location Data:** Declared as collected exclusively for **App Functionality** (route calculation and curb parking gap identification). Declared as **Not Shared with Third Parties** for tracking/advertising, and **Encrypted in Transit (HTTPS/TLS 1.3)**.
  - **Data Deletion:** Must declare and provide a working, accessible in-app and web mechanism for users to request complete data deletion (`POST /api/compliance/delete-my-data`).

### Permissions & Background Location Rules
- **Foreground-Only Principle:** SmartRoute operates on **minimal location tracking**. Location access (`ACCESS_FINE_LOCATION` / `ACCESS_COARSE_LOCATION`) is requested only when the user explicitly opens the Route Planner or SpotMatch Parking tab.
- **No Covert Background Tracking:** The application does **not** request or use `ACCESS_BACKGROUND_LOCATION`. When the app is backgrounded or closed, location tracking ceases instantly. This satisfies Play Store data minimization rules and prevents rejection during store review.

---

## 3. Apple App Store Review Guidelines (iOS App)

### Data Collection Disclosure & Consent
- **Purpose Strings:** The iOS `Info.plist` (and Flutter wrapper configuration) must include clear, human-readable justification strings for `NSLocationWhenInUseUsageDescription` and `NSCameraUsageDescription`.
  - *Example:* `"SmartRoute needs your location while using the app to calculate live turn-by-turn traffic directions and measure distance to parking spots."*
- **No Mandatory Tracking:** Users must be able to use non-location-dependent features (such as searching movies by budget or browsing admin event listings) even if location permissions are denied (by entering manual origin text such as `Hebbal`).

---

## 4. India's Digital Personal Data Protection Act (DPDP), 2023

SmartRoute operates as a Data Fiduciary handling personal data of Data Principals within India and enforces the following statutory mandates:

### Section 8(7) — Storage & Purpose Limitation
- **Zero Persistent Retention by Default:** Personal identifiers—such as exact GPS origin/destination history, vehicle license plate numbers, and contact details—are collected solely for the immediate purpose of fulfilling the user's active session request.
- **Immediate Anonymization/Erasure:** Once the route calculation or parking gap match is completed, raw personal identifiers are discarded or anonymized. Shared route load counters in Firestore (`smartroute_route_loads`) store only aggregate, anonymous counts (`time_bucket: "2026-07-17T16:00", count: 8`). No individual user tracking or vehicle link is retained.

### Section 6 — Valid Consent & Notice
- **Clear Affirmative Action:** Consent must be free, specific, informed, unconditional, and unambiguous.
- **In-App Privacy Notice:** Prior to using location-aware or crowdsourced reporting features, users are presented with the accessible in-app **Privacy Policy & DPDP Disclosures Modal/Screen**, explaining exact data flows.

### User Rights — Access & Erasure
- **Right to Erasure:** Users can trigger `POST /api/compliance/delete-my-data` anytime via the app interface, immediately expunging any session data or opt-in profile records tied to their device token or session ID.

---

## 5. Reserve Bank of India (RBI) Payment Gateway Guidelines

### Pass-Through Architecture (Zero Direct PA/PG Licensing)
- **Prohibition of Custom Card Forms:** To ensure full compliance with RBI Master Directions on Payment Aggregators and Payment Gateways (PA/PG) and Payment Card Industry Data Security Standard (PCI-DSS), SmartRoute **never** collects, processes, or stores raw credit card numbers, CVVs, expiry dates, or bank credentials on its own servers.
- **Licensed Gateway Pass-Through:** All checkout transactions (`PART C`) strictly redirect to licensed payment aggregators (**Razorpay** or **Stripe India**) via their hosted checkout SDKs/sessions (`/api/checkout/create-session`).
- **Webhook Handshake:** Our backend receives verified cryptographic signatures (`POST /api/checkout/webhook`) confirming transaction status before decrements are applied to admin ticket inventory.

---

## 6. Scraping-Restricted Sites Blocklist (Zero Tolerance Policy)

### authoritative Prohibitions
- **BookMyShow & Commercial Ticketing Sites:** BookMyShow's Terms of Service explicitly prohibit automated scraping, crawling, or unauthorized data extraction. Any attempt to scrape BookMyShow introduces severe legal exposure, frequent technical breakage, and IP blacklisting.
- **Enforcement by Agent 0:** **Agent 0 (`ComplianceGuardrailAgent`)** maintains a strict `SCRAPING_RESTRICTED_DOMAINS` blocklist (`bookmyshow.com`, `in.bookmyshow.com`, `paytm.com/movies`, etc.). If any agent attempts an HTTP outbound request to these domains, `Agent 0` immediately raises a `ComplianceViolationException` and terminates the request.
- **Legal Alternative (Admin Inventory Subsystem):** Instead of scraping third-party platforms, SmartRoute implements its own **Admin Inventory Portal (`/api/shows/add`, `/api/events/add`)** where partner venues and business managers self-list genuine shows, prices, and ticket counts.

---

## 7. Motor Vehicle Registration Data Access (VAHAN / Parivahan)

### Statutory Rules & API Partnerships
- **Government VAHAN Database:** India's national vehicle registry (VAHAN/Parivahan) prohibits automated web scraping or captcha-bypassing to look up license plate details (`KA 04 EQ 1234`).
- **Licensed KYC API Partners:** Production access to real vehicle dimensions and registration details via license plates requires an authorized, paid B2B API partnership with licensed KYC/verification gateways (such as **Surepass**, **Attestr**, or **HyperVerge**).
- **Phase 1 Demo vs. Production Strategy:**
  - For zero-cost instant operation without incurring per-lookup B2B API fees, **Agent 9 (`VehicleProfileAgent`)** resolves car dimensions (`length_m`, `width_m`) using our high-speed local vehicle dictionary (`data/vehicles.json`) while supporting local keyword/model matching (`Creta`, `Innova`, `Swift`).
  - When a user enters a license plate string, `Agent 9` logs and returns a formal **Compliance Advisory Flag**:
    `"License plate OCR string '{plate}' processed via local profile matching. Real-time national registry (VAHAN) lookup requires a paid B2B API partnership (e.g. Surepass/Attestr) and is flagged as a Phase 2 paid production tier."`

---

## Summary Table: Compliance Guardrail Mapping

| Compliance Area | Policy / Legal Source | SmartRoute Enforcement Mechanism (Agent 0) |
| :--- | :--- | :--- |
| **Google Maps Caching & Quota** | Google Maps Platform ToS | Ephemeral memory-only polyline handling; automatic fallback to `data/routes.json` when `OVER_QUERY_LIMIT` is hit (`is_live: false`). |
| **Android Background Location** | Google Play Data Safety Policies | Foreground-only location requests (`ACCESS_FINE_LOCATION`); zero `ACCESS_BACKGROUND_LOCATION` tracking. |
| **Personal Data Storage** | India DPDP Act 2023 (Section 8(7)) | Data minimization (`enforce_data_minimization`); zero storage of GPS history; 1-click `POST /api/compliance/delete-my-data`. |
| **Payment Card Security** | RBI PA/PG Guidelines / PCI-DSS | Pass-through checkout (`verify_payment_flow`); 100% redirection to Razorpay/Stripe hosted checkouts (`create-session`). |
| **Ticketing Inventory** | BookMyShow ToS | Strict blocklist (`SCRAPING_RESTRICTED_DOMAINS`); zero scraping; 100% owned self-listed inventory via Admin Subsystem. |
| **Vehicle Plate Lookups** | Ministry of Road Transport (VAHAN) | Local dictionary matching (`data/vehicles.json`); clear compliance advisory flag prohibiting scraping of `parivahan.gov.in`. |
