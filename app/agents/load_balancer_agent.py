from typing import Dict, Any, List
from app.database import get_route_load, increment_route_load, log_assignment, get_current_time_bucket, get_debug_state
from app.config import get_capacity_threshold

class LoadBalancingAgent:
    """
    Agent 5: Load-Balancing / Diversion Agent (Key Differentiator)
    Maintains real-time shared counters per (route_id, time_bucket) in Firebase Firestore + SQLite fallback.
    Monitors capacity thresholds and diverts commuters from saturated optimal routes to next best alternatives
    to prevent herding and gridlock.
    """
    def __init__(self):
        pass

    async def evaluate_and_assign(self, origin: str, destination: str, ranked_routes: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not ranked_routes:
            return {
                "agent_name": "Load-Balancing / Diversion Agent (Agent 5)",
                "error": "No ranked routes available to assign."
            }

        capacity = get_capacity_threshold()
        time_bucket = get_current_time_bucket()

        optimal_route = ranked_routes[0]
        optimal_id = optimal_route["route_id"]
        optimal_load = get_route_load(optimal_id, time_bucket)

        chosen_route = None
        diverted = False
        diversion_reason = ""

        if optimal_load < capacity:
            chosen_route = optimal_route
            diverted = False
            diversion_reason = (
                f"Assigned primary optimal route ({optimal_load}/{capacity} concurrent commuters "
                f"in current window '{time_bucket}' via real-time shared state). No diversion required."
            )
        else:
            diverted = True
            for candidate in ranked_routes[1:]:
                cand_id = candidate["route_id"]
                cand_load = get_route_load(cand_id, time_bucket)
                if cand_load < capacity:
                    chosen_route = candidate
                    diversion_reason = (
                        f"DIVERSION ACTIVE: Primary optimal route ('{optimal_route['name']}') reached threshold limit "
                        f"({optimal_load}/{capacity} commuters in Firestore/SQLite shared state). Diverted to next best candidate ('{candidate['name']}') "
                        f"with current load {cand_load}/{capacity} to prevent corridor herding."
                    )
                    break
            
            if not chosen_route:
                least_loaded = min(ranked_routes, key=lambda r: get_route_load(r["route_id"], time_bucket))
                cand_load = get_route_load(least_loaded["route_id"], time_bucket)
                chosen_route = least_loaded
                diversion_reason = (
                    f"ALL CORRIDORS SATURATED: Primary route ('{optimal_route['name']}') at {optimal_load}/{capacity}. "
                    f"Assigned least loaded candidate ('{least_loaded['name']}') with {cand_load}/{capacity} commuters."
                )

        chosen_id = chosen_route["route_id"]
        new_load = increment_route_load(chosen_id, time_bucket)

        log_assignment(origin, destination, chosen_route["name"], diverted, diversion_reason)

        agent_log = (
            f"Evaluated capacity in shared real-time state for time bucket '{time_bucket}' (Threshold: {capacity}). "
            f"Optimal Route '{optimal_route['name']}' had load {optimal_load}/{capacity}. "
            f"{'-> DIVERTED commuter to ' + chosen_route['name'] if diverted else '-> ALLOWED optimal assignment'}. "
            f"New load for '{chosen_route['name']}': {new_load}/{capacity}."
        )

        return {
            "agent_name": "Load-Balancing / Diversion Agent (Agent 5)",
            "time_bucket": time_bucket,
            "capacity_threshold": capacity,
            "optimal_route_id": optimal_id,
            "optimal_route_load_before": optimal_load,
            "chosen_route": chosen_route,
            "chosen_route_id": chosen_id,
            "chosen_route_new_load": new_load,
            "diverted": diverted,
            "diversion_reason": diversion_reason,
            "agent_log": agent_log
        }

    def get_status(self) -> Dict[str, Any]:
        return get_debug_state()
