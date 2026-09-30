import asyncio
import time
from typing import Dict, Any, List, Optional
from app.agents.event_agent import EventDensityAgent
from app.agents.traffic_agent import TrafficIncidentAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.router_agent import RouterAgent
from app.agents.show_agent import ShowDiscoveryAgent
from app.agents.venue_cost_agent import VenueCostAgent
from app.agents.booking_agent import BookingConfirmationAgent
from app.agents.vehicle_profile_agent import VehicleProfileAgent
from app.agents.space_assessment_agent import SpaceAssessmentAgent
from app.agents.fit_matching_agent import FitMatchingAgent

class SmartRouteOrchestrator:
    """
    Orchestrates the 5-Agent pipeline cleanly using async Python:
    Step 1: Run Agent 1 (Event-Density) & Agent 2 (Traffic/Incidents) in parallel.
    Step 2: Feed both outputs into Agent 3 (Evaluator) for candidate scoring.
    Step 3: Feed Agent 3 output into Agent 4 (Router), which consults Agent 5 (Load-Balancing).
    Returns complete execution trace and UI-ready navigation result.
    
    Also orchestrates the 3-Agent Entertainment & Booking Sub-pipeline (Agents 6, 7, 8):
    Agent 6 (Show Discovery) -> Agent 7 (Venue Cost & Proximity) -> Agent 8 (Booking & Auto-Route handoff).
    """
    def __init__(self):
        self.event_agent = EventDensityAgent()
        self.traffic_agent = TrafficIncidentAgent()
        self.evaluator_agent = EvaluatorAgent()
        self.router_agent = RouterAgent()
        self.show_agent = ShowDiscoveryAgent()
        self.venue_cost_agent = VenueCostAgent()
        self.booking_agent = BookingConfirmationAgent()
        self.vehicle_agent = VehicleProfileAgent()
        self.space_agent = SpaceAssessmentAgent()
        self.fit_agent = FitMatchingAgent()

    async def route_commuter(self, origin: str = "Hebbal", destination: str = "KR Puram via Tin Factory") -> Dict[str, Any]:
        start_time = time.time()

        # Step 1: Run Agent 1 and Agent 2 concurrently
        event_task = asyncio.create_task(self.event_agent.run(destination))
        traffic_task = asyncio.create_task(self.traffic_agent.run(origin, destination))
        
        event_output, traffic_output = await asyncio.gather(event_task, traffic_task)

        # Step 2: Run Agent 3 (Evaluator Agent)
        evaluator_output = await self.evaluator_agent.run(event_output, traffic_output)

        # Step 3: Run Agent 4 (Router Agent), which internally consults Agent 5 (Load-Balancing Agent)
        router_output = await self.router_agent.run(origin, destination, evaluator_output)

        elapsed_ms = round((time.time() - start_time) * 1000.0, 1)

        # Build clean trace response
        pipeline_trace = [
            {
                "step": 1,
                "agent": "Agent 1: Event-Density Agent",
                "status": "Success (Parallel)",
                "summary": event_output.get("agent_log", ""),
                "data": {
                    "event_found": event_output.get("event_found"),
                    "location": event_output.get("location"),
                    "risk_score": event_output.get("risk_score")
                }
            },
            {
                "step": 1,
                "agent": "Agent 2: Traffic & Incident Agent",
                "status": "Success (Parallel)",
                "summary": traffic_output.get("agent_log", ""),
                "data": {
                    "source_mode": traffic_output.get("source_mode"),
                    "routes_checked": len(traffic_output.get("routes", [])),
                    "incidents_matched": len(traffic_output.get("incidents", []))
                }
            },
            {
                "step": 2,
                "agent": "Agent 3: Evaluator Agent",
                "status": "Success (Sequential)",
                "summary": evaluator_output.get("agent_log", ""),
                "data": {
                    "top_route_name": evaluator_output.get("ranked_routes", [{}])[0].get("name", "N/A"),
                    "top_score": evaluator_output.get("ranked_routes", [{}])[0].get("score", "N/A")
                }
            },
            {
                "step": 3,
                "agent": "Agent 5: Load-Balancing / Diversion Agent",
                "status": "Success (Consulted by Router)",
                "summary": router_output.get("load_balancer_output", {}).get("agent_log", ""),
                "data": {
                    "diverted": router_output.get("diversion_info", {}).get("diverted"),
                    "optimal_route_load_before": router_output.get("diversion_info", {}).get("optimal_route_load_before"),
                    "new_load": router_output.get("diversion_info", {}).get("assigned_route_load"),
                    "capacity_threshold": router_output.get("diversion_info", {}).get("capacity_threshold")
                }
            },
            {
                "step": 4,
                "agent": "Agent 4: Router Agent",
                "status": "Success (Final Output)",
                "summary": router_output.get("agent_log", ""),
                "data": {
                    "assigned_route_name": router_output.get("assigned_route", {}).get("name"),
                    "eta": router_output.get("assigned_route", {}).get("eta_minutes"),
                    "distance_km": router_output.get("assigned_route", {}).get("distance_km")
                }
            }
        ]

        return {
            "status": "success",
            "pipeline_time_ms": elapsed_ms,
            "origin": origin,
            "destination": destination,
            "assigned_route": router_output.get("assigned_route"),
            "diversion_info": router_output.get("diversion_info"),
            "pipeline_trace": pipeline_trace,
            "raw_ranked_routes": evaluator_output.get("ranked_routes", []),
            "incidents_on_route": [
                inc for inc in traffic_output.get("incidents", [])
                if router_output.get("assigned_route", {}).get("route_id") in inc.get("affected_corridors", [])
            ]
        }

    async def search_shows(
        self,
        show_name: str = "",
        city: str = "Bengaluru",
        budget_per_ticket: float = 10000.0,
        ticket_count: int = 1,
        screen_types: list = None,
        location_pref: str = "",
        origin: str = "Hebbal"
    ) -> Dict[str, Any]:
        start_time = time.time()
        # Step 1: Run Agent 6 (Show-Discovery Agent)
        show_output = await self.show_agent.run(
            show_name=show_name,
            city=city,
            budget_per_ticket=budget_per_ticket,
            ticket_count=ticket_count,
            screen_types=screen_types,
            location_pref=location_pref
        )
        candidates = show_output.get("candidate_shows", [])

        # Step 2: Run Agent 7 (Venue Proximity & Cost Agent)
        cost_output = await self.venue_cost_agent.run(
            candidate_shows=candidates,
            origin=origin,
            ticket_count=ticket_count
        )

        elapsed_ms = round((time.time() - start_time) * 1000.0, 1)

        return {
            "status": "success",
            "pipeline_time_ms": elapsed_ms,
            "origin": origin,
            "shows": cost_output.get("enriched_shows", []),
            "show_agent_log": show_output.get("agent_log", ""),
            "venue_cost_log": cost_output.get("agent_log", "")
        }

    async def confirm_booking_and_route(
        self,
        show_id: str,
        ticket_count: int,
        origin: str,
        venue_name: str = "",
        lat: float = 0.0,
        lng: float = 0.0,
        total_cost: float = 0.0
    ) -> Dict[str, Any]:
        # Step 1: Run Agent 8 (Booking Confirmation Agent)
        booking_output = await self.booking_agent.run(
            show_id=show_id,
            ticket_count=ticket_count,
            origin=origin,
            venue_name=venue_name,
            lat=lat,
            lng=lng,
            total_cost=total_cost
        )

        # Step 2: Automatically trigger existing 5-Agent SmartRoute pipeline pointing to the venue
        target_destination = booking_output.get("venue_name") or booking_output.get("venue_address") or "Orion Mall, Yeshwantpur"
        route_output = await self.route_commuter(origin=origin, destination=target_destination)

        return {
            "status": "success",
            "booking_confirmation": booking_output,
            "route_result": route_output
        }

    def get_vehicles_list(self) -> List[Dict[str, Any]]:
        return self.vehicle_agent.get_all_vehicles()

    async def search_parking_spots(
        self,
        vehicle_query: str = "maruti_swift",
        origin: str = "Hebbal",
        area_query: str = ""
    ) -> Dict[str, Any]:
        start_time = time.time()

        # Step 1: Run Agent 9 (Vehicle-Profile Agent)
        vehicle_output = await self.vehicle_agent.run(vehicle_query)
        vehicle_profile = vehicle_output.get("vehicle", {})

        # Step 2: Run Agent 10 (Space-Assessment Agent)
        space_output = await self.space_agent.run(area_query)
        gaps_list = space_output.get("spots", [])

        # Step 3: Run Agent 11 (Fit-Matching Agent)
        fit_output = await self.fit_agent.run(vehicle_profile, gaps_list, origin=origin)

        elapsed_ms = round((time.time() - start_time) * 1000.0, 1)

        return {
            "status": "success",
            "pipeline_time_ms": elapsed_ms,
            "vehicle_profile": vehicle_output,
            "space_assessment": space_output,
            "fit_matching": fit_output
        }

# Global orchestrator instance
orchestrator = SmartRouteOrchestrator()
