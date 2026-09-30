# SmartRoute — Production Deployment Guide & Store Submission Architecture (DEPLOYMENT.md)

This document provides exact step-by-step instructions for deploying the SmartRoute single-stack backend (`FastAPI` + `Uvicorn`), real-time database (`Firebase Firestore`), and cross-platform mobile app (`Flutter` Android APK & iOS build + Progressive Web App).

---

## 1. App Store Submission Fees & Cost Architecture

To transition from a zero-cost local development pilot to formal public app store distribution, note the unavoidable official store account fees:

| Distribution Channel | Store / Platform Fee | Mandatory Requirements & Notes | Zero-Cost Alternative for Initial Pilot |
| :--- | :--- | :--- | :--- |
| **Google Play Store (Android APK)** | **$25 (One-time fee)** | Requires Google Play Developer Account setup, Data Safety Section completion (`COMPLIANCE.md`), and 20-tester closed track verification (if personal developer account). | **Direct APK Sideloading:** Share the compiled release `app-release.apk` directly via email, GitHub Releases, or corporate portal. |
| **Apple App Store (iOS App)** | **$99 / year** | Requires annual Apple Developer Program enrollment, App Store Connect provisioning profiles, and strict privacy purpose string disclosures (`Info.plist`). | **Progressive Web App (PWA):** Users visit `https://your-smartroute.onrender.com` in Safari and select `"Add to Home Screen"`. Runs full screen like a native app with zero store fees! |

---

## 2. Cloud Backend Hosting (Free Tiers: Render / Railway / Fly.io)

SmartRoute bundles both real-time API endpoints and responsive frontend assets into a single lightweight Uvicorn server (`app/main.py`), making deployment trivial:

### Option A: Render.com Web Service (Recommended Free Tier)
1. Push this repository to your GitHub account.
2. Create a new **Web Service** on [Render Dashboard](https://dashboard.render.com).
3. Select your GitHub repo (`smartroute-demo`).
4. Configure Build & Start settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run.py`
5. Add Environment Variables under **Environment**:
   - `CAPACITY_THRESHOLD=10`
   - `FIREBASE_PROJECT_ID=your-firebase-project-id`
   - `GOOGLE_MAPS_API_KEY=AIzaSy...` *(Optional: activates live traffic polylines; falls back gracefully if blank)*
   - `RAZORPAY_KEY_ID=rzp_test_...`
   - `RAZORPAY_KEY_SECRET=your_test_secret`
6. Click **Create Web Service**. Your live HTTPS backend is up at `https://your-app.onrender.com` within 2 minutes!

---

## 3. Real-Time Database Setup (Firebase Firestore)

To ensure **Agent 5 (Load-Balancing Agent)** and **Agent 10 (Space-Assessment Agent)** operate across thousands of concurrent mobile/web users globally:

1. Go to [Firebase Console](https://console.firebase.google.com/) and click **Add Project**.
2. Name your project (e.g. `smartroute-demo-live`) and select **Build -> Firestore Database -> Create Database**.
3. Choose **Start in Production Mode** and select your closest region (`asia-south1` for Bengaluru/India).
4. Go to **Project Settings -> Service Accounts -> Generate New Private Key**.
5. Save the JSON file as `serviceAccountKey.json` on your secure production server (or paste its JSON contents into environment variable `FIREBASE_CREDENTIALS_PATH`).
6. **Graceful Fallback Notice:** If `FIREBASE_CREDENTIALS_PATH` is not configured, `app/database.py` automatically falls back to local thread-safe `sqlite3` while displaying a compliance log advisory (`Running on local SQLite fallback`).

---

## 4. Building the Cross-Platform Mobile Application (Flutter APK & iOS)

### Prerequisites
- Install **Flutter SDK** (`flutter --version` >= 3.19+).
- Install **Android Studio** (for Android command-line tools & NDK).

### Building the Android Production APK (`$0 Cost`)
1. Navigate into the Flutter app directory:
   ```bash
   cd flutter_app
   ```
2. Get packages and verify configuration:
   ```bash
   flutter pub get
   ```
3. Build the optimized release APK:
   ```bash
   flutter build apk --release
   ```
4. Your production-ready, lean Android APK is generated at:
   `flutter_app/build/app/outputs/flutter-apk/app-release.apk`
   *(Minimum Android API Level: `21` / Android 5.0 Lollipop — covering >99% of Android devices globally while meeting Google Play `targetSdkVersion: 34` requirements).*

### Building the iOS App / PWA
- For native iOS (`$99/yr Apple Developer Account` required):
  ```bash
  flutter build ios --release
  ```
- For **Progressive Web App (PWA)** (`$0 Cost`):
  The static web root (`static/index.html`) is pre-configured with a responsive viewport and mobile web app tags, enabling instant iPhone home screen installation via Safari with zero store review delays.
