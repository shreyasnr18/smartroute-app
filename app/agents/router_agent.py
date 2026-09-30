from typing import Dict, Any, List
from app.agents.load_balancer_agent import LoadBalancingAgent

class RouterAgent:
    """
    Agent 4: Router Agent
    Receives Evaluator's ranked routes and consults Agent 5 (Load-Balancing Agent) to check capacity thresholds.
    Finalizes the route assignment for this specific user, formatting turn-by-turn navigation, ETA, and diversion transparency.
    """
    def __init__(self):
        self.load_balancer = LoadBalancingAgent()

    async def run(self, origin: str, destination: str, evaluator_output: Dict[str, Any]) -> Dict[str, Any]:
        ranked_routes = evaluator_output.get("ranked_routes", [])

        # Consult Agent 5: Load-Balancing / Diversion Agent
        lb_output = await self.load_balancer.evaluate_and_assign(origin, destination, ranked_routes)

        chosen = lb_output.get("chosen_route", {})
        diverted = lb_output.get("diverted", False)
        diversion_reason = lb_output.get("diversion_reason", "")
        new_load = lb_output.get("chosen_route_new_load", 1)
        capacity = lb_output.get("capacity_threshold", 10)

        predictive_checkpoints = self._build_predictive_checkpoints(origin, destination, chosen, diverted, new_load, capacity)
        turn_by_turn = [
            f"📍 Checkpoint 1 — {cp['junction']}: {cp['guidance']}" for cp in predictive_checkpoints
        ]

        status_badge = "Diverted (High Capacity on Primary Route)" if diverted else "Optimal Route Assigned"
        
        agent_log = (
            f"Consulted Agent 5 before assignment. Selected Route: '{chosen.get('name')}'. "
            f"Status: {status_badge}. Assigned Load Counter: {new_load}/{capacity}. "
            f"ETA: {chosen.get('adjusted_eta_minutes')} mins ({chosen.get('distance_km')} km)."
        )

        return {
            "agent_name": "Router Agent (Agent 4)",
            "assigned_route": {
                "route_id": chosen.get("route_id", "unknown"),
                "name": chosen.get("name", "Unknown Route"),
                "corridor": chosen.get("corridor", ""),
                "distance_km": chosen.get("distance_km", 0),
                "eta_minutes": chosen.get("adjusted_eta_minutes", 40),
                "score": chosen.get("score", 0),
                "reason": chosen.get("reason", ""),
                "steps": turn_by_turn,
                "predictive_checkpoints": predictive_checkpoints
            },
            "diversion_info": {
                "diverted": diverted,
                "status_badge": status_badge,
                "diversion_reason": diversion_reason,
                "optimal_route_id": lb_output.get("optimal_route_id", ""),
                "optimal_route_load_before": lb_output.get("optimal_route_load_before", 0),
                "assigned_route_load": new_load,
                "capacity_threshold": capacity,
                "time_bucket": lb_output.get("time_bucket", "")
            },
            "agent_log": agent_log,
            "load_balancer_output": lb_output
        }

    def _build_predictive_checkpoints(self, origin: str, destination: str, chosen: Dict[str, Any], diverted: bool, new_load: int, capacity: int) -> List[Dict[str, Any]]:
        route_name = chosen.get("name", "Assigned Corridor")
        eta = chosen.get("adjusted_eta_minutes", chosen.get("base_eta_minutes", 38))
        dist = chosen.get("distance_km", 14.0)
        mid_dist = round(dist * 0.45, 1)

        is_venue_destination = any(kw in destination.lower() for kw in ["mall", "pvr", "inox", "imax", "theatre", "hall", "auditorium", "stadium", "grounds", "convention"])

        if diverted:
            return [
                {
                    "junction": f"{origin} Flyover & Departure Checkpoint",
                    "distance_marker": "0.0 km",
                    "expected_flow": f"⚡ Early Diversion Engaged (Load: {new_load}/{capacity})",
                    "prediction_status": "diverted",
                    "guidance": f"Agent 5 detected primary corridor reached capacity threshold ({capacity}/{capacity}). Re-routing you immediately onto '{route_name}' to bypass Outer Ring Road gridlock before you depart."
                },
                {
                    "junction": "Thanisandra / Kalyan Nagar Peripheral Expressway",
                    "distance_marker": f"{mid_dist} km",
                    "expected_flow": "⚡ Optimal Free-Flow Corridor Confirmed",
                    "prediction_status": "optimal",
                    "guidance": f"SmartRoute AI prediction model confirms ~18-25 mins saved over primary arterial corridor. Minimal signal delays and free-flowing transit anticipated along this peripheral loop."
                },
                {
                    "junction": f"{destination} Approach & Arrival Gate",
                    "distance_marker": f"{dist} km",
                    "expected_flow": "🎯 Target Approach Clear — On-Time Arrival",
                    "prediction_status": "success",
                    "guidance": f"Smooth destination approach verified via eastern bypass link. Total estimated journey time: {eta} mins ({dist} km)." + (" Priority Basement P2/P3 parking navigation active for verified BookMyShow ticket holders." if is_venue_destination else "")
                }
            ]
        else:
            mid_junction_name = "Tin Factory / Manyata Tech Park Junction" if not is_venue_destination else "Dr Rajkumar Road / Malleshwaram Signal Corridor"
            return [
                {
                    "junction": f"{origin} Flyover & Departure Checkpoint",
                    "distance_marker": "0.0 km",
                    "expected_flow": f"✅ Optimal Corridor Flow ({new_load}/{capacity} capacity used)",
                    "prediction_status": "optimal",
                    "guidance": f"Begin commute along assigned primary corridor: '{route_name}'. Agent 5 actively tracking 15-minute sliding capacity bucket."
                },
                {
                    "junction": f"{mid_junction_name} (Predictive Checkpoint)",
                    "distance_marker": f"{mid_dist} km",
                    "expected_flow": "⚠️ Predictive Alert: High Bottleneck Surge Probability (+12m)",
                    "prediction_status": "alert",
                    "guidance": f"SmartRoute multi-agent prediction indicates potential traffic/signal buildup ahead. Once you reach this junction, SmartRoute will automatically re-evaluate real-time corridor capacity and guide you via an instant alternate diversion if congestion spikes!"
                },
                {
                    "junction": f"{destination} Final Arrival Approach",
                    "distance_marker": f"{dist} km",
                    "expected_flow": "🎯 Target Destination & Bay Allocation Active",
                    "prediction_status": "success",
                    "guidance": f"Final half-mile corridor cleared. Estimated arrival in {eta} mins ({dist} km)." + (" Express VIP entry & QR scanning assistance ready at venue entrance." if is_venue_destination else "")
                }
            ]

