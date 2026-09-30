import io
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import qrcode

from app.orchestrator import orchestrator
from app.database import get_debug_state, reset_db, sync_parking_spot
from app.config import load_config, save_config
from app.agents.compliance_agent import agent_zero

app = FastAPI(
    title="SmartRoute — Multi-Agent Traffic Routing Demo (Bengaluru pilot)",
    description="5-agent pipeline demo that routes commuters while preventing corridor saturation via real-time load balancing and dynamic diversion."
)

STATIC_DIR = Path(__file__).parent.parent / "static"

class RouteRequest(BaseModel):
    origin: str = "Hebbal"
    destination: str = "KR Puram via Tin Factory"

class SimulateRushRequest(BaseModel):
    origin: str = "Hebbal"
    destination: str = "KR Puram via Tin Factory"
    count: int = 15

class ConfigUpdateRequest(BaseModel):
    CAPACITY_THRESHOLD: Optional[int] = None
    USE_MOCK_TRAFFIC: Optional[bool] = None
    USE_MOCK_LLM: Optional[bool] = None

class ShowSearchRequest(BaseModel):
    show_name: str = ""
    city: str = "Bengaluru"
    budget_per_ticket: float = 10000.0
    ticket_count: int = 1
    screen_types: Optional[list] = None
    location_pref: str = ""
    origin: str = "Hebbal"

class MockPaymentCallbackRequest(BaseModel):
    show_id: str = ""
    ticket_count: int = 1
    origin: str = "Hebbal"
    venue_name: str = ""
    lat: float = 0.0
    lng: float = 0.0
    total_cost: float = 0.0

class ParkingSearchRequest(BaseModel):
    vehicle_query: str = "maruti_swift"
    origin: str = "Hebbal"
    area_query: str = ""

class DeleteDataRequest(BaseModel):
    user_id: str
    confirmation_phrase: str = "DELETE MY DATA"

class AddEventRequest(BaseModel):
    event_id: str
    venue: str
    event_name: str
    start_time: str = "Today 6:00 PM"
    expected_crowd_size: int = 500
    risk_score: int = 35
    affected_corridors: list = ["route_orr_tinfactory"]
    admin_token: str = "secret_admin_token"

class AddShowRequest(BaseModel):
    show_id: str
    show_name: str
    type: str = "Movie"
    venue_name: str
    address: str
    city: str = "Bengaluru"
    price_per_ticket: float = 350.0
    tickets_available: int = 100
    screen_type: str = "PVR / INOX"
    lat: float = 13.0110
    lng: float = 77.5548
    admin_token: str = "secret_admin_token"

class CheckoutSessionRequest(BaseModel):
    show_id: str
    ticket_count: int = 1
    total_cost: float = 350.0
    origin: str = "Hebbal"
    gateway: str = "razorpay"

class WebhookVerificationRequest(BaseModel):
    show_id: str
    ticket_count: int = 1
    origin: str = "Hebbal"
    venue_name: str = ""
    lat: float = 0.0
    lng: float = 0.0
    total_cost: float = 0.0
    payment_id: str
    signature: str = "verified_webhook"

class ReportParkingRequest(BaseModel):
    location_id: str
    address: str
    lat: float
    lng: float
    gap_length_m: float
    curb_side: str = "Curb Bay"
    notes: str = "Crowdsourced On-Device Report"

@app.post("/api/route")
async def request_route(req: RouteRequest):
    result = await orchestrator.route_commuter(req.origin, req.destination)
    return result

@app.get("/api/debug/route-load")
@app.get("/debug/route-load")
async def debug_route_load():
    """
    Returns current load counts per route corridor vs CAPACITY_THRESHOLD and recent assignment logs.
    Essential for proving the diversion concept to non-technical audiences during demos.
    """
    return get_debug_state()

@app.post("/api/debug/reset")
async def reset_route_loads():
    """Resets all SQLite route load counters and assignment logs to 0."""
    return reset_db()

@app.post("/api/simulate-rush")
async def simulate_rush(req: SimulateRushRequest):
    """
    Runs `count` sequential commuter requests through the 5-agent pipeline to instantly
    demonstrate route 1 filling up to CAPACITY_THRESHOLD and subsequent commuters being diverted.
    """
    results = []
    for i in range(1, req.count + 1):
        # We append commuter id just for logging/tracking clarity if needed, or keep identical origin->dest
        res = await orchestrator.route_commuter(req.origin, req.destination)
        results.append({
            "commuter_index": i,
            "assigned_route": res["assigned_route"]["name"],
            "diverted": res["diversion_info"]["diverted"],
            "status_badge": res["diversion_info"]["status_badge"],
            "current_load": res["diversion_info"]["assigned_route_load"]
        })
    
    return {
        "status": "success",
        "total_simulated": req.count,
        "summary": f"Simulated {req.count} sequential commuters along {req.origin} -> {req.destination}.",
        "commuters": results,
        "final_debug_state": get_debug_state()
    }

@app.post("/api/shows/search")
async def search_shows_endpoint(req: ShowSearchRequest):
    """
    Runs Agent 6 (Show-Discovery) & Agent 7 (Venue Proximity & Cost) to find,
    filter, and enrich candidate shows around Bengaluru based on commuter budget & preferences.
    """
    return await orchestrator.search_shows(
        show_name=req.show_name,
        city=req.city,
        budget_per_ticket=req.budget_per_ticket,
        ticket_count=req.ticket_count,
        screen_types=req.screen_types,
        location_pref=req.location_pref,
        origin=req.origin
    )

@app.post("/api/mock-payment-callback")
async def mock_payment_callback(req: MockPaymentCallbackRequest):
    """
    Simulates a payment gateway callback confirmation (Agent 8).
    Processes ticket booking and immediately hands off to the existing 5-Agent
    SmartRoute routing pipeline (`route_commuter`), returning the live navigation result pointing to the venue.
    """
    return await orchestrator.confirm_booking_and_route(
        show_id=req.show_id,
        ticket_count=req.ticket_count,
        origin=req.origin,
        venue_name=req.venue_name,
        lat=req.lat,
        lng=req.lng,
        total_cost=req.total_cost
    )

@app.get("/api/vehicles")
async def get_vehicles_endpoint():
    """Returns list of mock vehicle profiles (Agent 9) for dropdown selection."""
    return {"status": "success", "vehicles": orchestrator.get_vehicles_list()}

@app.post("/api/parking-search")
async def search_parking_endpoint(req: ParkingSearchRequest):
    """
    Runs Agent 9 (Vehicle-Profile), Agent 10 (Space-Assessment offline feed), and
    Agent 11 (Fit-Matching) to identify curb parking gaps that physically fit the vehicle.
    """
    return await orchestrator.search_parking_spots(
        vehicle_query=req.vehicle_query,
        origin=req.origin,
        area_query=req.area_query
    )

@app.get("/api/compliance/policy")
async def get_compliance_policy():
    """Returns Agent 0 formal privacy and data minimization policies under DPDP Act / GDPR."""
    return {
        "status": "success",
        "agent_name": "Compliance & Guardrail Agent (Agent 0)",
        "privacy_policy": agent_zero.get_privacy_policy(),
        "data_minimization_policy": agent_zero.get_data_minimization_policy()
    }

@app.post("/api/compliance/delete-my-data")
async def delete_my_data_endpoint(req: DeleteDataRequest):
    """Allows commuters to instantly exercise right to erasure under DPDP Act."""
    return agent_zero.handle_user_data_deletion(req.user_id, req.confirmation_phrase)

@app.post("/api/events/add")
async def add_admin_event(req: AddEventRequest):
    """Admin Event Subsystem: allows businesses/venues to self-list events with zero scraping."""
    guard = agent_zero.check_admin_listing("events", req.admin_token)
    if not guard.get("allowed"):
        raise HTTPException(status_code=403, detail=guard.get("reason"))
    
    events_path = Path(__file__).parent.parent / "data" / "events.json"
    import json
    events = []
    if events_path.exists():
        try:
            with open(events_path, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception:
            events = []
    
    new_event = {
        "event_id": req.event_id,
        "venue": req.venue,
        "event_name": req.event_name,
        "start_time": req.start_time,
        "expected_crowd_size": req.expected_crowd_size,
        "risk_score": req.risk_score,
        "affected_corridors": req.affected_corridors
    }
    events.append(new_event)
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    
    return {"status": "success", "message": f"Event '{req.event_name}' listed successfully.", "total_events": len(events)}

@app.post("/api/shows/add")
async def add_admin_show(req: AddShowRequest):
    """Admin Inventory Subsystem: allows theatres to self-list stock with zero scraping."""
    guard = agent_zero.check_admin_listing("shows", req.admin_token)
    if not guard.get("allowed"):
        raise HTTPException(status_code=403, detail=guard.get("reason"))
    
    shows_path = Path(__file__).parent.parent / "data" / "shows.json"
    import json
    shows = []
    if shows_path.exists():
        try:
            with open(shows_path, "r", encoding="utf-8") as f:
                shows = json.load(f)
        except Exception:
            shows = []
    
    new_show = {
        "show_id": req.show_id,
        "show_name": req.show_name,
        "type": req.type,
        "venue_name": req.venue_name,
        "address": req.address,
        "city": req.city,
        "price_per_ticket": req.price_per_ticket,
        "tickets_available": req.tickets_available,
        "screen_type": req.screen_type,
        "lat": req.lat,
        "lng": req.lng
    }
    shows.append(new_show)
    with open(shows_path, "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2)
    
    return {"status": "success", "message": f"Show '{req.show_name}' listed successfully.", "total_shows": len(shows)}

@app.post("/api/checkout/create-session")
async def create_checkout_session_endpoint(req: CheckoutSessionRequest):
    """Creates a licensed Razorpay/Stripe pass-through checkout session handshake."""
    return orchestrator.booking_agent.create_checkout_session(
        show_id=req.show_id,
        ticket_count=req.ticket_count,
        total_cost=req.total_cost,
        origin=req.origin,
        gateway=req.gateway
    )

@app.post("/api/checkout/webhook")
async def checkout_webhook_endpoint(req: WebhookVerificationRequest):
    """Processes verified payment handshake and hands off venue coordinates to 5-Agent routing pipeline."""
    return await orchestrator.booking_agent.run(
        show_id=req.show_id,
        ticket_count=req.ticket_count,
        origin=req.origin,
        venue_name=req.venue_name,
        lat=req.lat,
        lng=req.lng,
        total_cost=req.total_cost,
        payment_id=req.payment_id,
        signature=req.signature
    )

@app.post("/api/parking/report")
async def report_parking_spot_endpoint(req: ReportParkingRequest):
    """Crowdsources an on-device curb parking report and syncs to Firestore real-time shared state."""
    sync_parking_spot(
        spot_id=req.location_id,
        address=req.address,
        lat=req.lat,
        lng=req.lng,
        gap_length_m=req.gap_length_m,
        curb_side=req.curb_side,
        notes=req.notes
    )
    return {"status": "success", "message": f"Spot at '{req.address}' synced to Firestore shared state with 15m expiry."}

@app.get("/api/config")
async def get_configuration():
    cfg = load_config()
    # Mask API keys in public GET response
    return {
        "CAPACITY_THRESHOLD": int(cfg.get("CAPACITY_THRESHOLD", 10)),
        "TIME_BUCKET_MINUTES": int(cfg.get("TIME_BUCKET_MINUTES", 15)),
        "USE_MOCK_TRAFFIC": bool(cfg.get("USE_MOCK_TRAFFIC", True)),
        "USE_MOCK_LLM": bool(cfg.get("USE_MOCK_LLM", True)),
        "HAS_GOOGLE_MAPS_KEY": bool(cfg.get("GOOGLE_MAPS_API_KEY", "").strip()),
        "HAS_GEMINI_KEY": bool(cfg.get("GEMINI_API_KEY", "").strip())
    }

@app.post("/api/config")
async def update_configuration(req: ConfigUpdateRequest):
    update_data = {}
    if req.CAPACITY_THRESHOLD is not None:
        update_data["CAPACITY_THRESHOLD"] = req.CAPACITY_THRESHOLD
    if req.USE_MOCK_TRAFFIC is not None:
        update_data["USE_MOCK_TRAFFIC"] = req.USE_MOCK_TRAFFIC
    if req.USE_MOCK_LLM is not None:
        update_data["USE_MOCK_LLM"] = req.USE_MOCK_LLM
    
    if update_data:
        save_config(update_data)
    return {"status": "success", "updated": update_data, "current_config": await get_configuration()}

import socket
from app.places import suggest_bengaluru_places, get_place_details

def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

@app.get("/api/places/suggest")
async def suggest_places(q: str = ""):
    """Returns matching Bengaluru places and junctions for autocomplete suggestions."""
    suggestions = suggest_bengaluru_places(q)
    return {"suggestions": suggestions}

@app.get("/qrcode")
async def generate_qr_code(request: Request, url: Optional[str] = None):
    """
    Generates and streams a PNG QR code pointing to the app's LAN URL (or custom url parameter)
    so commuters can instantly scan with their mobile cameras and open the app over Wi-Fi.
    """
    if not url:
        host = request.headers.get("host", "127.0.0.1:8000")
        port = host.split(":")[-1] if ":" in host else "8000"
        # If accessed via localhost/127.0.0.1/0.0.0.0, replace with LAN IP for phone scanners
        if any(host.startswith(prefix) for prefix in ("localhost", "127.0.0.1", "0.0.0.0")):
            lan_ip = get_local_ip()
            url = f"http://{lan_ip}:{port}/"
        else:
            scheme = request.headers.get("x-forwarded-proto", "http")
            url = f"{scheme}://{host}/"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# Mount static files (HTML/CSS/JS frontend) at the root path
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
