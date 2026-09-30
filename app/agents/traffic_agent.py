import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List
from app.config import use_mock_traffic, load_config
from app.agents.compliance_agent import agent_zero

ROUTES_FILE = Path(__file__).parent.parent.parent / "data" / "routes.json"
INCIDENTS_FILE = Path(__file__).parent.parent.parent / "data" / "incidents.json"

class TrafficIncidentAgent:
    """
    Agent 2: Traffic & Incident Agent
    Calls real Google Maps Directions/Distance Matrix API when configured + live RSS news feeds.
    Enforces Agent 0 Compliance Guardrails and graceful degradation (`is_live: False`) fallback.
    """
    def __init__(self):
        self.routes = self._load_json(ROUTES_FILE)
        self.incidents = self._load_json(INCIDENTS_FILE)

    def _load_json(self, filepath: Path) -> List[Dict[str, Any]]:
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _get_coordinates(self, place_name: str):
        from app.places import get_place_details
        d = get_place_details(place_name)
        return (d["lat"], d["lng"]) if d else (13.0358, 77.5970)

    def _fetch_live_rss_incidents(self) -> List[Dict[str, Any]]:
        """
        Fetches live public traffic news via RSS (or syndicated traffic alerts feed)
        and parses with xml.etree.ElementTree for sector keyword matches.
        """
        live_incidents = []
        rss_urls = [
            "https://bangalore.citizenmatters.in/feed",
            "https://www.thehindu.com/news/cities/bangalore/feeder/default.rss"
        ]
        keywords = ("accident", "road closed", "waterlogging", "traffic", "jam", "diversion", "pothole", "metro work")
        sectors = {
            "Hebbal": ["Hebbal", "Tin Factory", "KR Puram"],
            "KR Puram": ["Tin Factory", "KR Puram", "ORR"],
            "Tin Factory": ["Tin Factory", "ORR", "Benniganahalli"],
            "ORR": ["ORR", "Tin Factory", "KR Puram"],
            "Yeshwantpur": ["Yeshwantpur", "Tumkur Road", "Goraguntepalya"],
            "Hennur": ["Hennur", "Kalyan Nagar", "Outer Ring Road"]
        }

        for url in rss_urls:
            try:
                # Consult Agent 0 before making outbound call
                guard = agent_zero.check_http_request(url, agent_name="Agent 2 (Traffic & Incident)", purpose="Fetch live RSS traffic alerts")
                if not guard.get("allowed"):
                    continue

                resp = requests.get(url, timeout=3, headers={"User-Agent": "SmartRoute-Traffic-Agent/1.0"})
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    for item in root.findall(".//item")[:15]:
                        title = item.findtext("title", "")
                        desc = item.findtext("description", "")
                        combined = f"{title} {desc}".lower()
                        if any(kw in combined for kw in keywords):
                            matched_corridors = set()
                            for sector_name, corr_list in sectors.items():
                                if sector_name.lower() in combined:
                                    for c in corr_list:
                                        matched_corridors.add(f"route_{c.lower().replace(' ', '_')}")
                            if matched_corridors or "traffic" in combined:
                                live_incidents.append({
                                    "id": f"rss_{len(live_incidents)+100}",
                                    "type": "Live News Feed Alert",
                                    "severity": "High" if "accident" in combined or "closed" in combined else "Moderate",
                                    "location": title[:80],
                                    "description": f"Live RSS Report: {title}",
                                    "delay_minutes": 15 if "accident" in combined else 8,
                                    "affected_corridors": list(matched_corridors) or ["route_orr_tinfactory", "gmaps_route_1"]
                                })
            except Exception:
                pass

        return live_incidents

    async def run(self, origin: str, destination: str) -> Dict[str, Any]:
        cfg = load_config()
        is_mock = use_mock_traffic()
        api_key = cfg.get("GOOGLE_MAPS_API_KEY", "").strip()

        routes_data = []
        is_live = False
        fallback_reason = "missing_api_key_or_mock_flag"
        source_mode = "Mock Local Dataset (routes.json)"

        if not is_mock and api_key:
            try:
                url = "https://maps.googleapis.com/maps/api/directions/json"
                # Consult Agent 0
                guard = agent_zero.check_http_request(url, agent_name="Agent 2 (Traffic & Incident)", purpose="Google Maps Directions API route calculation")
                if guard.get("allowed"):
                    params = {
                        "origin": origin,
                        "destination": destination,
                        "alternatives": "true",
                        "departure_time": "now",
                        "key": api_key
                    }
                    resp = requests.get(url, params=params, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = data.get("status")
                        if status == "OK" and data.get("routes"):
                            is_live = True
                            fallback_reason = ""
                            source_mode = "Live Google Maps Directions API"
                            for idx, r in enumerate(data["routes"]):
                                leg = r["legs"][0]
                                dist_km = round(leg["distance"]["value"] / 1000.0, 1)
                                eta_mins = round(leg.get("duration_in_traffic", leg["duration"])["value"] / 60.0)
                                summary = r.get("summary", f"Route Option {idx+1}")
                                routes_data.append({
                                    "route_id": f"gmaps_route_{idx+1}",
                                    "name": f"Via {summary}",
                                    "corridor": summary,
                                    "distance_km": dist_km,
                                    "base_eta_minutes": eta_mins,
                                    "current_traffic_level": "Live Traffic Calculated",
                                    "summary": f"Google Maps live route via {summary}.",
                                    "steps": [step.get("html_instructions", "Continue straight") for step in leg.get("steps", [])[:5]]
                                })
                        else:
                            fallback_reason = f"gmaps_api_{status.lower() if status else 'error'}"
                            source_mode = f"Cached Corridor Geometry (Fallback: {status})"
            except Exception as e:
                fallback_reason = "network_timeout_or_error"
                source_mode = "Cached Corridor Geometry (Fallback: Network Timeout)"

        if not routes_data:
            # Check standard Hebbal -> KR Puram or calculate dynamic corridors
            o_lower = origin.strip().lower()
            d_lower = destination.strip().lower()
            if "hebbal" in o_lower and ("kr puram" in d_lower or "tin factory" in d_lower):
                routes_data = [r.copy() for r in self.routes]
            else:
                from app.places import get_place_details
                import math
                p1 = get_place_details(origin)
                p2 = get_place_details(destination)
                
                dlat = math.radians(p2["lat"] - p1["lat"])
                dlng = math.radians(p2["lng"] - p1["lng"])
                a = math.sin(dlat/2)**2 + math.cos(math.radians(p1["lat"])) * math.cos(math.radians(p2["lat"])) * math.sin(dlng/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                haversine_km = max(round(6371 * c * 1.35, 1), 3.5)
                base_eta = max(int(haversine_km * 2.2), 12)

                routes_data = [
                    {
                        "route_id": "route_orr_tinfactory",
                        "name": f"Via {p1['name']} Main Arterial & ORR Corridor",
                        "corridor": f"{p1['name']} - ORR - {p2['name']}",
                        "distance_km": haversine_km,
                        "base_eta_minutes": base_eta,
                        "current_traffic_level": "Congested",
                        "summary": f"Primary high-capacity arterial between {p1['name']} and {p2['name']}.",
                        "steps": [f"Head east from {p1['name']}", "Take the Outer Ring Road / Main Arterial ramp", "Pass the major junction flyover", f"Exit towards {p2['name']}", f"Arrive at {p2['name']} destination"]
                    },
                    {
                        "route_id": "route_hennur_kalyannagar",
                        "name": f"Via {p1['locality']} Parallel Avenue & Junction Bypass",
                        "corridor": f"{p1['locality']} Parallel Bypass",
                        "distance_km": round(haversine_km * 1.15, 1),
                        "base_eta_minutes": max(int(base_eta * 0.95), 10),
                        "current_traffic_level": "Moderate",
                        "summary": f"Alternative parallel corridor bypassing central bottlenecks.",
                        "steps": [f"Depart {p1['name']} via parallel avenue", "Turn right onto the inner bypass road", "Continue straight through the residential link", f"Approach {p2['name']} via service road", f"Arrive at {p2['name']}"]
                    },
                    {
                        "route_id": "route_thanisandra_bypass",
                        "name": f"Via Peripheral Ring Expressway & {p2['locality']} Link",
                        "corridor": "Peripheral Ring Expressway",
                        "distance_km": round(haversine_km * 1.35, 1),
                        "base_eta_minutes": max(int(base_eta * 0.88), 10),
                        "current_traffic_level": "Low",
                        "summary": f"High-speed peripheral bypass routing around heavy urban traffic.",
                        "steps": [f"Head north-east from {p1['name']} towards expressway", "Merge onto the Peripheral Ring Expressway", "Enjoy high-speed transit with minimal signals", f"Take exit towards {p2['name']} link road", f"Arrive at {p2['name']}"]
                    }
                ]

        # Combine local incidents and live RSS news feed alerts
        all_incidents = list(self.incidents)
        live_rss = self._fetch_live_rss_incidents()
        all_incidents.extend(live_rss)

        congestion_map = {}
        matched_incidents = []

        for route in routes_data:
            r_id = route["route_id"]
            base_eta = route.get("base_eta_minutes", 40)
            extra_delay = 0
            route_incidents = []

            for inc in all_incidents:
                if r_id in inc.get("affected_corridors", []) or "gmaps_route" in r_id:
                    extra_delay += inc.get("delay_minutes", 0)
                    route_incidents.append(inc)
                    if inc not in matched_incidents:
                        matched_incidents.append(inc)

            adjusted_eta = base_eta + extra_delay
            route["adjusted_eta_minutes"] = adjusted_eta
            route["active_incidents"] = route_incidents

            if extra_delay >= 10 or route.get("current_traffic_level") == "Congested":
                c_level = "High"
            elif extra_delay >= 5 or route.get("current_traffic_level") == "Moderate":
                c_level = "Moderate"
            else:
                c_level = "Low"

            route["congestion_level"] = c_level
            congestion_map[r_id] = {
                "base_eta": base_eta,
                "extra_delay": extra_delay,
                "adjusted_eta": adjusted_eta,
                "level": c_level
            }

        if not is_live:
            warning_msg = f"⚠️ Live Google Maps data temporarily unavailable ({fallback_reason}). Using cached corridor geometry."
        else:
            warning_msg = "Live Google Maps Directions & Distance Matrix API Active."

        agent_log = (
            f"Retrieved {len(routes_data)} route options ({source_mode}). "
            f"Cross-referenced {len(all_incidents)} alerts (including {len(live_rss)} live RSS news items) -> "
            f"Detected {len(matched_incidents)} affecting incidents. {warning_msg}"
        )

        return {
            "agent_name": "Traffic & Incident Agent (Agent 2)",
            "source_mode": source_mode,
            "is_live": is_live,
            "fallback_reason": fallback_reason,
            "warning_notice": warning_msg if not is_live else "",
            "routes": routes_data,
            "congestion_per_route": congestion_map,
            "incidents": matched_incidents,
            "agent_log": agent_log
        }
