import math
from typing import Dict, Any, List
from app.places import get_place_details

# Safety buffer tolerance config value (default +0.3m combined front/back)
SAFETY_BUFFER_M = 0.3

class FitMatchingAgent:
    """
    Agent 11: Fit-Matching Agent
    ============================================================================
    ARCHITECTURAL NOTE:
    Evaluates physical compatibility between the commuter's vehicle dimensions
    (from Agent 9) and open curb parking gap lengths (from Agent 10).

    Adds a configurable safety buffer (`SAFETY_BUFFER_M = 0.3m` combined front/back)
    to vehicle length before comparing against open gap length:
      - "Fits"      if gap_length_m >= (vehicle_length + buffer)
      - "Marginal"  if gap_length_m >= vehicle_length AND < (vehicle_length + buffer)
      - "Too Tight" if gap_length_m < vehicle_length

    Also computes spatial distance and driving duration from user's origin to
    each candidate parking curb spot, reusing the existing Google Maps / urban
    corridor calculation from Agent 2 & Agent 7 (`get_place_details`).
    ============================================================================
    """
    def __init__(self, safety_buffer_m: float = SAFETY_BUFFER_M):
        self.safety_buffer_m = safety_buffer_m

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    async def run(
        self,
        vehicle_profile: Dict[str, Any],
        gaps_list: List[Dict[str, Any]],
        origin: str = "Hebbal"
    ) -> Dict[str, Any]:
        origin_details = get_place_details(origin or "Hebbal")
        origin_coords = (origin_details["lat"], origin_details["lng"]) if origin_details else (13.0358, 77.5970)

        vehicle_length = float(vehicle_profile.get("length_m", 3.86))
        vehicle_width = float(vehicle_profile.get("width_m", 1.74))
        vehicle_name = f"{vehicle_profile.get('make', '')} {vehicle_profile.get('model', '')}".strip() or "Vehicle"
        required_length = round(vehicle_length + self.safety_buffer_m, 2)

        matched_spots = []
        for idx, spot in enumerate(gaps_list, start=1):
            s_lat = float(spot.get("lat", 13.0180))
            s_lng = float(spot.get("lng", 77.5550))
            gap_len = float(spot.get("gap_length_m", 4.5))

            # Compute spatial distance and commute duration from origin
            straight_dist = self._haversine_distance(origin_coords[0], origin_coords[1], s_lat, s_lng)
            # Urban road distance multiplier (~1.35x)
            distance_km = max(round(straight_dist * 1.35, 1), 0.8)
            duration_minutes = max(int(round(distance_km * 2.4 + 3)), 3)

            # Classify physical fit
            if gap_len >= required_length:
                fit_status = "Fits"
            elif gap_len >= vehicle_length:
                fit_status = "Marginal"
            else:
                fit_status = "Too Tight"

            # Confirmation string format requested by user:
            # e.g. "Spot near Soap Factory, Yeshwantpur — 1.2 km — 5 mins — Gap: 5.4m — Fits your Maruti Swift (4.9m + 0.3m buffer)."
            confirm_summary = (
                f"Spot near {spot.get('address', 'Unknown Location')} — {distance_km} km — {duration_minutes} mins — "
                f"Gap: {gap_len}m — {fit_status} your {vehicle_name} ({vehicle_length}m + {self.safety_buffer_m}m buffer)."
            )

            matched_spots.append({
                "s_no": idx,
                "location_id": spot.get("location_id", f"spot_{idx}"),
                "address": spot.get("address", "Unknown Location"),
                "lat": s_lat,
                "lng": s_lng,
                "distance_km": distance_km,
                "duration_minutes": duration_minutes,
                "gap_length_m": gap_len,
                "fit_status": fit_status,
                "curb_side": spot.get("curb_side", "Service Curb"),
                "confirmation_summary": confirm_summary,
                "notes": spot.get("notes", "")
            })

        # Rank candidate spots: Fits first, then Marginal, then Too Tight; sorted by distance ascending within groups
        status_priority = {"Fits": 1, "Marginal": 2, "Too Tight": 3}
        matched_spots.sort(key=lambda x: (status_priority.get(x["fit_status"], 4), x["distance_km"]))

        # Re-index s_no after sorting
        for i, item in enumerate(matched_spots, start=1):
            item["s_no"] = i

        fits_count = sum(1 for s in matched_spots if s["fit_status"] == "Fits")
        marginal_count = sum(1 for s in matched_spots if s["fit_status"] == "Marginal")
        tight_count = sum(1 for s in matched_spots if s["fit_status"] == "Too Tight")

        agent_log = (
            f"Evaluated {len(matched_spots)} curb parking gaps against {vehicle_name} ({vehicle_length}m + {self.safety_buffer_m}m buffer = {required_length}m req). "
            f"Result: {fits_count} Fits, {marginal_count} Marginal, {tight_count} Too Tight. "
            f"Top Spot: '{matched_spots[0]['address'] if matched_spots else 'None'}' ({matched_spots[0]['distance_km'] if matched_spots else 0} km)."
        )

        return {
            "agent_name": "Fit-Matching Agent (Agent 11)",
            "status": "success",
            "vehicle_evaluated": vehicle_profile,
            "safety_buffer_m": self.safety_buffer_m,
            "required_length_m": required_length,
            "origin_used": origin,
            "summary_counts": {
                "fits": fits_count,
                "marginal": marginal_count,
                "too_tight": tight_count,
                "total": len(matched_spots)
            },
            "ranked_spots": matched_spots,
            "agent_log": agent_log
        }
