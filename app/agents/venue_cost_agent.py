import math
from typing import Dict, Any, List
from app.agents.traffic_agent import TrafficIncidentAgent
from app.places import get_place_details

class VenueCostAgent:
    """
    Agent 7: Venue Cost & Proximity Agent
    Enriches candidate shows with spatial distance from commuter origin, estimated commute duration,
    and total financial breakdown (ticket cost x count + BMS convenience fee + hourly parking estimate).
    """
    def __init__(self):
        self.traffic_agent = TrafficIncidentAgent()

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    async def run(
        self,
        candidate_shows: List[Dict[str, Any]],
        origin: str = "Hebbal",
        ticket_count: int = 1
    ) -> Dict[str, Any]:
        origin_details = get_place_details(origin or "Hebbal")
        origin_coords = (origin_details["lat"], origin_details["lng"]) if origin_details else (13.0358, 77.5970)
        
        enriched_shows = []
        for idx, show in enumerate(candidate_shows, start=1):
            v_lat = show.get("lat", 13.0110)
            v_lng = show.get("lng", 77.5548)
            
            # Compute distance and duration using urban corridor multipliers
            if origin_coords:
                straight_dist = self._haversine_distance(origin_coords[0], origin_coords[1], v_lat, v_lng)
                # Urban road distance is ~1.35x straight line in Bengaluru
                distance_km = max(round(straight_dist * 1.35, 1), 2.5)
            else:
                distance_km = 12.5

            # Estimate travel duration based on average Bengaluru corridor speed (~18-22 km/h during evening rush)
            duration_minutes = max(int(round(distance_km * 2.4 + 5)), 15)

            # Financial calculations
            price_per_ticket = float(show.get("price_per_ticket", 300))
            tickets_cost = round(price_per_ticket * ticket_count, 2)
            # BookMyShow convenience fee estimate (10% mock constant)
            bms_fee = round(tickets_cost * 0.10, 2)
            total_cost = round(tickets_cost + bms_fee, 2)
            parking_fee = float(show.get("parking_fee_per_hour", 40))

            # Extract location (locality) vs mall/theatre name cleanly
            venue_full = show.get("venue_name", "Unknown Venue")
            address_full = show.get("address", "")
            # If venue_name has comma e.g. "PVR Orion Mall, Dr Rajkumar Road, Malleshwaram West"
            parts = [p.strip() for p in venue_full.split(",")]
            mall_theatre = parts[0] if parts else venue_full
            location_str = parts[-1] if len(parts) > 1 else (show.get("city", "Bengaluru"))
            if "Yeshwantpur" in address_full:
                location_str = "Yeshwantpur"
            elif "Malleshwaram" in address_full or "Malleshwaram" in venue_full:
                location_str = "Malleshwaram"
            elif "Rajajinagar" in address_full:
                location_str = "Rajajinagar"
            elif "Koramangala" in address_full:
                location_str = "Koramangala"
            elif "Whitefield" in address_full:
                location_str = "Whitefield"
            elif "Yelahanka" in address_full:
                location_str = "Yelahanka"
            elif "Richmond" in address_full or "Ulsoor" in address_full:
                location_str = "Central Bengaluru"

            enriched_show = {
                "s_no": idx,
                "show_id": show.get("show_id", f"bms_{idx}"),
                "show_name": show.get("show_name", ""),
                "type": show.get("type", "movie"),
                "location": location_str,
                "mall_theatre": mall_theatre,
                "venue_name_full": venue_full,
                "address": address_full,
                "lat": v_lat,
                "lng": v_lng,
                "screen_type": show.get("screen_type", "Other"),
                "distance_km": distance_km,
                "duration_minutes": duration_minutes,
                "tickets_available": show.get("tickets_available", 0),
                "price_per_ticket": price_per_ticket,
                "ticket_count": ticket_count,
                "tickets_cost": tickets_cost,
                "bms_fee_estimate": bms_fee,
                "total_cost": total_cost,
                "parking_fee_per_hour": parking_fee,
                # Format selection summary string required by user:
                # e.g. "2. Soap Factory, Yeshwantpur — Orion Mall — 20 km — 48 mins — 5 tickets available — ₹300 x 5 + BookMyShow fee — Parking ₹50/hr — Total: ₹XXXX"
                "selection_summary": (
                    f"{idx}. {location_str} — {mall_theatre} — {distance_km} km — {duration_minutes} mins — "
                    f"{show.get('tickets_available', 0)} tickets available — ₹{int(price_per_ticket)} x {ticket_count} + BookMyShow fee — "
                    f"Parking ₹{int(parking_fee)}/hr — Total: ₹{int(total_cost)}"
                )
            }
            enriched_shows.append(enriched_show)

        # Sort by total cost ascending (or balanced distance/cost)
        enriched_shows.sort(key=lambda x: (x["total_cost"], x["distance_km"]))
        # Re-index s_no after sort
        for i, item in enumerate(enriched_shows, start=1):
            item["s_no"] = i
            item["selection_summary"] = (
                f"{i}. {item['location']} — {item['mall_theatre']} — {item['distance_km']} km — {item['duration_minutes']} mins — "
                f"{item['tickets_available']} tickets available — ₹{int(item['price_per_ticket'])} x {item['ticket_count']} + BookMyShow fee — "
                f"Parking ₹{int(item['parking_fee_per_hour'])}/hr — Total: ₹{int(item['total_cost'])}"
            )

        agent_log = (
            f"Calculated proximity and costs for {len(enriched_shows)} venues from origin '{origin}'. "
            f"Top Ranked Option: '{enriched_shows[0]['mall_theatre'] if enriched_shows else 'None'}' "
            f"({enriched_shows[0]['distance_km'] if enriched_shows else 0} km, Total: ₹{enriched_shows[0]['total_cost'] if enriched_shows else 0})."
        )

        return {
            "agent_name": "Venue Proximity & Cost Agent (Agent 7)",
            "enriched_shows": enriched_shows,
            "origin_used": origin,
            "ticket_count_used": ticket_count,
            "agent_log": agent_log
        }
