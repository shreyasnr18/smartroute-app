# SmartRoute — Multi-Agent Traffic Routing & Entertainment Auto-Routing Demo (Bengaluru Pilot)

## 1. Project Overview
SmartRoute is a free, lightweight, dependency-light multi-agent web application designed to solve both urban commuting and entertainment discovery. Traditional navigation apps simultaneously route thousands of commuters along the exact same "optimal" path, instantly turning corridors into severe gridlocks. SmartRoute proves how an **8-Agent Pipeline** coupled with real-time shared state (`SQLite`) actively balances traffic load, while providing an integrated **Show Discovery & Booking Sub-Pipeline** that finds movies/events by budget and automatically routes commuters to the venue!

---

## 2. The 8-Agent Architecture & Data Flow

```
+-----------------------------------------------------------------------------------+
|               ENTERTAINMENT & BOOKING SUB-PIPELINE (Agents 6, 7, 8)               |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  Agent 6: Show-Discovery Agent                                                    |
|  - Scans data/shows.json (mock BookMyShow dataset) by budget, tickets & screen    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  Agent 7: Venue Cost & Proximity Agent                                            |
|  - Calculates spatial distance (km) & commute duration from commuter's origin     |
|  - Computes total cost: ticket cost + 10% BMS fee + hourly parking breakdown      |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  Agent 8: Booking Confirmation Agent                                              |
|  - Simulates ticket checkout (decrements tickets_available in data/shows.json)    |
|  - Generates verifiable receipt ID & real outbound BookMyShow search URL          |
|  - Automatically triggers Agents 1-5 Traffic Pipeline pointing directly to venue! |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        COMMUTER ROUTE REQUEST (Hebbal -> Venue / KR Puram)        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
       +---------------------------------+---------------------------------+
       | (Parallel Execution)                                              |
       v                                                                   v
+---------------------------------------+   +---------------------------------------+
|  Agent 1: Event-Density Agent         |   |  Agent 2: Traffic & Incident Agent    |
|  - Checks mock events dataset         |   |  - Checks Google Maps / routes.json   |
|  - Calculates crowd size & risk score |   |  - Cross-references incidents.json    |
+---------------------------------------+   +---------------------------------------+
       |                                                                   |
       +---------------------------------+---------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  Agent 3: Evaluator Agent                                                         |
|  - Combines Event + Traffic + Incident heuristics into normalized penalty scores  |
|  - Ranks candidate corridors from best to worst & generates human explanation      |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  Agent 4: Router Agent                                                            |
|  - Consults Agent 5 before finalizing route assignment                            |
|  - Formats turn-by-turn guidance, ETA, distance, and diversion transparency       |
+-----------------------------------------------------------------------------------+
                                         ^
                                         | (Consults & Updates Real-Time State)
                                         v
+-----------------------------------------------------------------------------------+
|  Agent 5: Load-Balancing / Diversion Agent (Key Differentiator)                   |
|  - Checks SQLite (route_load table) against CAPACITY_THRESHOLD                    |
|  - If optimal corridor < threshold: Allows assignment (`diverted = false`)        |
|  - If optimal corridor >= threshold: Diverts to next candidate (`diverted = true`)|
+-----------------------------------------------------------------------------------+
```

### Agent Responsibilities:
1. **Event-Density Agent (Agent 1):** Scans the `data/events.json` feed for large crowd bottlenecks, concerts, or tech park surges across candidate corridors.
2. **Traffic & Incident Agent (Agent 2):** Retrieves route geometries via Google Maps Directions API (or `data/routes.json` fallback) and overlays live traffic alerts (`data/incidents.json`).
3. **Evaluator Agent (Agent 3):** Deterministically scores candidate routes (`congestion_penalty * 0.5 + event_risk * 0.3 + incident_penalty * 0.2`) and generates human-readable explanations.
4. **Router Agent (Agent 4):** Acts as the final commuter-facing coordinator, passing Evaluator choices to the Load Balancer and formatting turn-by-turn steps.
5. **Load-Balancing / Diversion Agent (Agent 5):** Maintains shared `(route_id, time_bucket)` assignment counters in SQLite (`smartroute.db`), enforcing `CAPACITY_THRESHOLD` to prevent gridlock.
6. **Show-Discovery Agent (Agent 6):** Filters candidate entertainment events from `data/shows.json` based on commuter budget, city, screen type (PVR, INOX, IMAX), and location preference.
7. **Venue Cost & Proximity Agent (Agent 7):** Enriches candidate shows with spatial distance (`haversine * 1.35x` urban road multiplier) from commuter origin, estimated commute time, and financial breakdown (`ticket cost + 10% BMS fee + parking fee/hr`).
8. **Booking Confirmation Agent (Agent 8):** Orchestrates simulated payment callbacks (`POST /api/mock-payment-callback`), decrements available ticket stock, generates receipt IDs (`BMS-MOCK-XXXXX`), provides real BookMyShow search links, and automatically hands off the venue destination to the 5-Agent routing engine.
9. **Vehicle-Profile Agent (Agent 9):** Resolves vehicle dimensions (`length_m`, `width_m`, make, model, type) from `data/vehicles.json` based on vehicle dropdown selection or license plate OCR string (standing in for Vahan/Surepass APIs).
10. **Space-Assessment Agent (Agent 10):** Reads offline precomputed curb parking gaps (`data/parking_gaps.json`) generated by the standalone YOLOv8n detector (`scripts/offline_yolo_gap_detector.py`).
11. **Fit-Matching Agent (Agent 11):** Evaluates physical compatibility between car dimensions (+0.3m safety buffer) and monitored curb gaps (`Fits`, `Marginal`, `Too Tight`), ranks spots by commute duration/distance from origin (`haversine * 1.35x`), and hands off the spot coordinates to Agents 1-5 for immediate guidance!

---

## 3. Folder & File Structure

```
smartroute-demo/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application, API routes, show search, parking search & callback endpoints
│   ├── config.py             # Configuration loader (`config.json` + environment variables)
│   ├── database.py           # SQLite connection, schema initialization, load counter queries
│   ├── places.py             # Bengaluru places coordinate resolver & autocomplete suggestions
│   ├── orchestrator.py       # Async pipeline orchestrating all 11 Agents cleanly
│   └── agents/
│       ├── __init__.py
│       ├── event_agent.py          # Agent 1: Event-Density analysis
│       ├── traffic_agent.py        # Agent 2: Traffic and Incident overlay
│       ├── evaluator_agent.py      # Agent 3: Route scoring and ranking
│       ├── router_agent.py         # Agent 4: Commuter navigation formatter
│       ├── load_balancer_agent.py  # Agent 5: Real-time capacity monitoring and diversion
│       ├── show_agent.py           # Agent 6: Show & ticket discovery filter
│       ├── venue_cost_agent.py     # Agent 7: Venue proximity, duration & financial cost breakdown
│       ├── booking_agent.py        # Agent 8: Mock checkout, stock decrement & auto-routing handoff
│       ├── vehicle_profile_agent.py# Agent 9: Vehicle dimensions and plate lookup
│       ├── space_assessment_agent.py# Agent 10: Precomputed curb gap reader
│       └── fit_matching_agent.py   # Agent 11: Dimension vs gap compatibility & ranking
├── data/
│   ├── events.json           # Editable mock dataset of Bengaluru crowd events
│   ├── incidents.json        # Editable mock dataset of roadwork and traffic incidents
│   ├── routes.json           # Editable mock candidate routes from Hebbal to KR Puram
│   ├── shows.json            # Editable mock BookMyShow dataset (14 Bengaluru venues/shows)
│   ├── vehicles.json         # Editable mock vehicle dictionary (Maruti Swift, Tata Nexon, Creta, etc.)
│   └── parking_gaps.json     # Precomputed curb parking gaps across Bengaluru corridors
├── scripts/
│   └── offline_yolo_gap_detector.py # One-time offline YOLOv8n script that detects curb vehicle gaps
├── static/                   # Mobile-first frontend web app (~375px responsive)
│   ├── index.html            # UI with Mode Tabs (Route, Shows, Parking), Tables, Modals & Live Map
│   ├── style.css             # Functional CSS styled with clear badges and modal cards
│   └── script.js             # Vanilla JS handling auto-routing, checkouts, and live logs
├── config.json               # Central configuration file for thresholds and API keys
├── requirements.txt          # Python project dependencies (`fastapi`, `uvicorn`, `requests`, `qrcode`)
├── run.py                    # One-command server start script (`python run.py`)
├── test_diversion.py         # Automated verification script asserting threshold diversion
├── test_show_pipeline.py     # Automated verification script asserting Agents 6, 7, 8 & auto-routing
├── test_spot_match_pipeline.py # Automated verification script asserting Agents 9, 10, 11 & spot fit
└── README.md                 # Mandatory project documentation
```

---

## 4. Swappable Mock vs. Real Components

To ensure the demo runs out-of-the-box for **free** with zero API keys or external dependencies, all external data sources are structured behind clean interfaces with swappable mock datasets:

| Component | Current Demo Source (Mocked) | How to Swap for Production / Live API |
| :--- | :--- | :--- |
| **Google Maps Traffic & Routes** | `data/routes.json` (3 candidate corridors between Hebbal and KR Puram) | Set `"USE_MOCK_TRAFFIC": false` and add your Google Maps Directions API key to `"GOOGLE_MAPS_API_KEY"` in `config.json`. |
| **Gemini Flash LLM Reasoning** | Deterministic heuristic templates (`app/agents/evaluator_agent.py`) | Set `"USE_MOCK_LLM": false` and add your free-tier Gemini API key (`gemini-1.5-flash`) to `"GEMINI_API_KEY"` in `config.json`. |
| **Local Events Feed** | `data/events.json` (mock IPL match, tech summits, flea markets) | Swap `_load_events()` in `app/agents/event_agent.py` to call live Eventbrite, BookMyShow (via authorized API), or Allevents endpoints. |
| **Traffic Incidents Feed** | `data/incidents.json` (mock waterlogging, BWSSB roadwork) | Swap `_load_json()` in `app/agents/traffic_agent.py` with a live RSS feed or GDELT/NewsAPI query. |
| **BookMyShow Shows & Venues Feed** | `data/shows.json` (mock movies/events across 14 Bengaluru venues) | Swap `self._load_shows()` in `app/agents/show_agent.py` to connect to authorized BookMyShow partner APIs or PostgreSQL database. |
| **Vehicle Registration / Dimensions API** | `data/vehicles.json` (mock Indian vehicle profiles) | Swap `lookup_vehicle` in `app/agents/vehicle_profile_agent.py` to call Surepass, Attestr, or HyperVerge Vahan OCR APIs. |
| **Real-Time Dashcam / Edge Curb Video Feed** | `data/parking_gaps.json` (precomputed offline using `scripts/offline_yolo_gap_detector.py`) | Connect live RTSP curb cameras or municipal dashcams to continuously run `scripts/offline_yolo_gap_detector.py` and upsert to the exact same JSON/SQLite schema! |

---

## 5. Step-by-Step Setup & Local Execution

### Prerequisites
- **Python 3.10+** installed on your system (`python --version`).

### Installation
1. Clone or navigate to the project directory:
   ```bash
   cd smartroute-demo
   ```
2. Install minimal Python dependencies (`requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```

### Running the App locally
1. Start the single-stack backend server:
   ```bash
   python run.py
   ```
2. Open your web browser or phone to:
   ```
   http://localhost:8000
   ```
   *(The Express/FastAPI server mounts and serves `static/index.html` directly at `/`)*.

---

## 6. Configuration Management (`CAPACITY_THRESHOLD`)

All runtime settings live in **`config.json`** at the project root:
```json
{
  "CAPACITY_THRESHOLD": 10,
  "TIME_BUCKET_MINUTES": 15,
  "USE_MOCK_TRAFFIC": true,
  "USE_MOCK_LLM": true,
  "GOOGLE_MAPS_API_KEY": "",
  "GEMINI_API_KEY": "",
  "DB_PATH": "smartroute.db",
  "HOST": "0.0.0.0",
  "PORT": 8000
}
```

- **`CAPACITY_THRESHOLD`:** The exact number of concurrent commuters allowed on a single route corridor within a `TIME_BUCKET_MINUTES` window before **Agent 5 (Load-Balancing Agent)** diverts subsequent commuters.
- **How to Change:** Edit `config.json` directly, set environment variables (`CAPACITY_THRESHOLD=5 python run.py`), or update dynamically via `POST /api/config`.

---

## 7. How to Test the Diversion Logic Locally

There are three easy ways to verify the load-balancing and diversion concept:

### Method 1: The UI "Simulate Rush" Button (Best for Demos)
1. Open `http://localhost:8000` in your browser.
2. Click the **`Simulate Rush (Test Diversion)`** button.
3. The app instantly sends 15 sequential commuter requests through the 5-Agent pipeline and renders a comparative table:
   - Commuters **#1 to #10** are assigned the top optimal route (`Via Hennur Main Road & Kalyan Nagar / Ramamurthy Nagar`) with status badge `[Optimal Route Assigned]`.
   - Commuter **#11 to #15** are automatically intercepted by Agent 5 (`LoadBalancingAgent`) when Route 1 hits `10/10` and diverted to `Via Thanisandra & Old Madras Road Peripheral Bypass` with badge `[Diverted (High Capacity on Primary Route)]`.
4. Inspect the **Live Corridor Load Debug Dashboard** right on the page to see `[SATURATED -> DIVERTING]` counters in real time.

### Method 2: Automated Command-Line Verification Script
Run the automated test script while the server is running (or offline):
```bash
python test_diversion.py
```
This script asserts exact threshold enforcement and prints an ASCII summary table.

### Method 3: Direct API Inspection (`/debug/route-load`)
Inspect real-time SQLite counters anytime via curl or browser:
```bash
curl http://localhost:8000/debug/route-load
```
To reset all counters back to `0/10` during a pitch:
```bash
curl -X POST http://localhost:8000/api/debug/reset
```

### Method 4: Automated Show Discovery & Auto-Routing Pipeline Verification (`test_show_pipeline.py`)
To test Agents 6, 7, and 8 along with the automatic transition into the 5-Agent SmartRoute navigation pipeline directly from the command line:
```bash
python test_show_pipeline.py
```
This script runs a complete simulated ticket booking workflow (`Kalki 2898 AD` at `PVR Orion Mall`), decrements available ticket stock, checks distance from `Hebbal`, outputs the `BMS-MOCK-XXXX` receipt ID, and verifies that the destination coordinates are cleanly routed via Agents 1-5 in `< 50 ms`.

### Method 5: Automated Spot-Match (Dimension-Aware Parking Finder) Verification (`test_spot_match_pipeline.py`)
To verify Agents 9, 10, and 11 along with the physical dimension checking against precomputed YOLOv8n curb gaps:
```bash
python test_spot_match_pipeline.py
```
This script tests vehicle lookups (`Maruti Swift` vs `Toyota Innova Crysta`), verifies safety buffer calculation (`+0.3m`), asserts classification (`Fits`, `Marginal`, `Too Tight`), and verifies distance/duration calculation from origin.

---

## 8. Mobile Testing & QR Code Generation

### Built-in Dynamic QR Code Generator
SmartRoute ships with an automatic QR code generator endpoint:
- **`GET /qrcode`**: Returns a high-contrast PNG QR code embedding the application's base URL.
- When demoing on a desktop browser, scroll down to the **Mobile Access QR Code** section on `http://localhost:8000` and scan it directly with your iPhone or Android camera to test the ~375px responsive mobile layout instantly.

### Deployment Instructions (Free Hosting Tiers)
Because SmartRoute packages both API endpoints and static HTML/CSS/JS inside a single lightweight Uvicorn instance (`app/main.py`), deploying to free platforms takes minutes:

- **Render / Railway / Fly.io (Backend + Frontend in One):**
  1. Push this repository to GitHub.
  2. Create a new Web Service on [Render](https://render.com) or [Railway](https://railway.app).
  3. Set Build Command: `pip install -r requirements.txt`
  4. Set Start Command: `python run.py`
  5. Visit the generated `.onrender.com` or `.railway.app` URL on your phone or scan its `/qrcode`!

---

## 9. Known Limitations & Production Roadmap

### Known Limitations (Demo Build)
1. **SQLite Concurrency & In-Memory Locks:** The demo uses a local `sqlite3` file (`smartroute.db`) suitable for single-node pilots and live pitch demonstrations. Under massive distributed traffic (10,000+ req/sec across multi-region instances), SQLite file locking would become a bottleneck.
2. **Static Corridor Definitions:** The demo evaluates 3 pre-defined candidate corridors between Hebbal and KR Puram rather than dynamically slicing arbitrary road graphs across all of Karnataka.
3. **Discrete Time Buckets:** Capacity is tracked per fixed `TIME_BUCKET_MINUTES` block (default 15 mins). A commuter departing at minute `14:59` shares a bucket separately from one at `15:01`.

### Production Roadmap
1. **Distributed State (`Redis / PostgreSQL`):** Replace `app/database.py` with Redis atomic counters (`INCR`) and sliding-window rate limiters to scale across clustered Kubernetes pods.
2. **Live Telemetry & IoT Integration:** Connect Agent 1 & Agent 2 directly to Bengaluru Traffic Police (BTP) ASTrA cameras, BMTC bus GPS feeds, and live Google Maps Directions Matrix API streams.
3. **Reinforcement Learning Diversion:** Upgrade Agent 5 from a static `CAPACITY_THRESHOLD` heuristic to a dynamic multi-agent reinforcement learning (MARL) model that adjusts capacity limits continuously based on rain, signal cycle timing, and real-time corridor outflow velocity.
