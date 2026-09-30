import json
import os
import re
from typing import Dict, Any, List
from app.agents.compliance_agent import agent_zero

class ShowDiscoveryAgent:
    """
    Agent 6: Show-Discovery Agent
    Queries our owned Admin Inventory Subsystem (`data/shows.json` / self-listed theatre stock) based on commuter preferences.
    Strictly adheres to Agent 0 Compliance Guardrail prohibiting automated scraping of BookMyShow or restricted portals.
    """
    def __init__(self, data_path: str = "data/shows.json"):
        self.data_path = data_path
        self._shows = []
        self._load_shows()

    def _load_shows(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self._shows = json.load(f)
            except Exception as e:
                print(f"[ShowDiscoveryAgent] Error loading {self.data_path}: {e}")
                self._shows = []
        else:
            print(f"[ShowDiscoveryAgent] Warning: File not found at {self.data_path}")

    async def run(
        self,
        show_name: str = "",
        city: str = "Bengaluru",
        budget_per_ticket: float = 10000.0,
        ticket_count: int = 1,
        screen_types: List[str] = None,
        location_pref: str = ""
    ) -> Dict[str, Any]:
        # Consult Agent 0 Compliance check on data origin
        guard = agent_zero.check_http_request("https://local-admin-subsystem/shows", agent_name="Agent 6 (Show Discovery)", purpose="Self-listed inventory query")
        
        # Always reload dataset dynamically so admin self-listings (`POST /api/shows/add`) are instantly reflected
        self._load_shows()

        if screen_types is None:
            screen_types = ["Any"]
        
        query = (show_name or "").strip().lower()
        city_query = (city or "Bengaluru").strip().lower()
        loc_pref = (location_pref or "").strip().lower()
        loc_keywords = [k.strip() for k in re.split(r'[/,;]', loc_pref) if k.strip()]

        candidates = []
        for show in self._shows:
            if city_query and city_query not in show.get("city", "").lower():
                continue

            available = show.get("tickets_available", 0)
            if available < ticket_count:
                continue

            price = show.get("price_per_ticket", 0)
            if price > budget_per_ticket:
                continue

            if query and query != "all" and query != "any":
                s_name = show.get("show_name", "").lower()
                s_type = show.get("type", "").lower()
                if query not in s_name and query not in s_type:
                    continue

            if screen_types and "Any" not in screen_types and "any" not in [st.lower() for st in screen_types]:
                s_screen = show.get("screen_type", "").upper()
                allowed_upper = [st.upper() for st in screen_types]
                v_name = show.get("venue_name", "").upper()
                if not any(token in s_screen or token in v_name for token in allowed_upper):
                    continue

            if loc_keywords:
                v_text = f"{show.get('venue_name', '')} {show.get('address', '')}".lower()
                if not any(kw in v_text for kw in loc_keywords):
                    continue

            candidates.append(show)

        agent_log = (
            f"Filtered {len(self._shows)} self-listed admin shows (`data/shows.json`). Found {len(candidates)} candidates matching "
            f"query='{show_name or 'All'}', budget<=₹{budget_per_ticket}/tkt, count={ticket_count}, "
            f"screens={screen_types}, location_pref='{location_pref or 'All Bengaluru'}'. "
            f"100% Owned Inventory (Zero BookMyShow Scraping)."
        )

        return {
            "agent_name": "Show-Discovery Agent (Agent 6)",
            "source_mode": "Admin Inventory Subsystem (Zero Scraping)",
            "candidate_shows": candidates,
            "filter_summary": {
                "show_name": show_name,
                "city": city,
                "budget_per_ticket": budget_per_ticket,
                "ticket_count": ticket_count,
                "screen_types": screen_types,
                "location_pref": location_pref,
                "total_matches": len(candidates)
            },
            "agent_log": agent_log
        }
