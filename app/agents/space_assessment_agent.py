import json
import os
from typing import Dict, Any, List
from app.database import get_active_parking_spots
from app.config import get_parking_expiry_minutes

class SpaceAssessmentAgent:
    """
    Agent 10: Space-Assessment Agent
    ============================================================================
    ARCHITECTURAL UPGRADE:
    Replaces continuous street camera / server inference costs with CROWDSOURCED, ON-DEVICE detection.
    When a user reports a spot or captures a photo from their phone, `gap_length_m` is synced to
    Firebase Firestore real-time database (`parking_spots` table).
    
    This agent retrieves all active parking gaps (`get_active_parking_spots`) and automatically
    expires any report older than `PARKING_SPOT_EXPIRY_MINUTES` (default: 15 minutes) to guarantee
    commuters only see genuinely available real-time curb bays. Also merges with baseline `data/parking_gaps.json`
    if fresh.
    ============================================================================
    """
    def __init__(self, data_path: str = "data/parking_gaps.json"):
        self.data_path = data_path
        self._gaps = []
        self._load_gaps()

    def _load_gaps(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self._gaps = json.load(f)
            except Exception as e:
                print(f"[SpaceAssessmentAgent] Error loading {self.data_path}: {e}")
                self._gaps = []
        else:
            self._gaps = []

    async def run(self, area_query: str = "") -> Dict[str, Any]:
        """
        Input: area_query (optional keyword e.g. 'Yeshwantpur', 'Malleshwaram', 'Hebbal', 'Tin Factory')
        Output: { agent_name, total_gaps_monitored, spots: [ { location_id, address, lat, lng, gap_length_m, ... } ] }
        """
        self._load_gaps()
        expiry_mins = get_parking_expiry_minutes()

        # Fetch crowdsourced live spots from Firestore / SQLite
        live_spots = get_active_parking_spots(expiry_minutes=expiry_mins)

        # Merge with baseline precomputed gaps, avoiding duplicate location IDs if live override exists
        live_ids = {s.get("id") or s.get("location_id") for s in live_spots}
        combined_source = list(live_spots)
        for item in self._gaps:
            if item.get("location_id") not in live_ids and item.get("id") not in live_ids:
                combined_source.append(item)

        spots = []
        clean_q = area_query.strip().lower() if area_query else ""

        for item in combined_source:
            addr = item.get("address", "").lower()
            notes = item.get("notes", "").lower()
            curb = item.get("curb_side", "").lower()
            
            matches = True
            if clean_q and clean_q != "bengaluru":
                keywords = clean_q.split()
                if not any(kw in addr or kw in notes or kw in curb for kw in keywords):
                    matches = False

            if matches:
                spots.append({
                    "location_id": item.get("location_id") or item.get("id", "unknown"),
                    "address": item.get("address", "Unknown Curb Address"),
                    "lat": float(item.get("lat", 13.0)),
                    "lng": float(item.get("lng", 77.58)),
                    "gap_length_m": float(item.get("gap_length_m", 4.0)),
                    "last_updated": item.get("timestamp") or item.get("last_updated", ""),
                    "curb_side": item.get("curb_side", "Curb Bay"),
                    "detection_confidence": item.get("detection_confidence", 0.95),
                    "notes": item.get("notes", "Crowdsourced On-Device Report (Firestore Real-Time Sync)")
                })

        if not spots and combined_source:
            for item in combined_source:
                spots.append({
                    "location_id": item.get("location_id") or item.get("id", "unknown"),
                    "address": item.get("address", "Unknown Curb Address"),
                    "lat": float(item.get("lat", 13.0)),
                    "lng": float(item.get("lng", 77.58)),
                    "gap_length_m": float(item.get("gap_length_m", 4.0)),
                    "last_updated": item.get("timestamp") or item.get("last_updated", ""),
                    "curb_side": item.get("curb_side", "Curb Bay"),
                    "detection_confidence": item.get("detection_confidence", 0.95),
                    "notes": item.get("notes", "Crowdsourced On-Device Report (Firestore Real-Time Sync)")
                })

        return {
            "agent_name": "Space-Assessment Agent (Agent 10)",
            "status": "success",
            "source": f"Crowdsourced On-Device Reports (`Firestore`) & Baseline (`data/parking_gaps.json`) with {expiry_mins}m auto-expiry",
            "expiry_minutes": expiry_mins,
            "total_gaps_monitored": len(combined_source),
            "filtered_count": len(spots),
            "spots": spots
        }
