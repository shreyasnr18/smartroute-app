import requests
from typing import Dict, Any, List
from app.config import use_mock_llm, load_config

class EvaluatorAgent:
    """
    Agent 3: Evaluator Agent
    Combines outputs of Agent 1 (Events) and Agent 2 (Traffic/Incidents).
    Scores each candidate route deterministically using weighted heuristics.
    Generates a concise one-line explanation per route (using Gemini Flash if enabled or deterministic template).
    """
    def __init__(self):
        pass

    async def run(self, event_output: Dict[str, Any], traffic_output: Dict[str, Any]) -> Dict[str, Any]:
        cfg = load_config()
        is_mock_llm = use_mock_llm()
        gemini_key = cfg.get("GEMINI_API_KEY", "").strip()

        routes = traffic_output.get("routes", [])
        event_corridor_risks = event_output.get("affected_corridors_risk", {})

        scored_routes = []
        for route in routes:
            r_id = route["route_id"]
            adjusted_eta = route.get("adjusted_eta_minutes", route.get("base_eta_minutes", 40))
            extra_delay = traffic_output.get("congestion_per_route", {}).get(r_id, {}).get("extra_delay", 0)
            
            # 1. Congestion penalty (0-100+)
            congestion_penalty = min(adjusted_eta * 1.5, 100.0)
            
            # 2. Event risk penalty (0-100)
            event_risk = event_corridor_risks.get(r_id, 0)
            
            # 3. Incident severity/delay penalty (0-100)
            incident_penalty = min(extra_delay * 4.0, 100.0)

            # Weighted Heuristic Formula (Lower score = Better / Faster / Safer route)
            total_score = round((congestion_penalty * 0.5) + (event_risk * 0.3) + (incident_penalty * 0.2), 1)

            # Generate short explanation
            explanation = self._generate_reason(
                route["name"], adjusted_eta, extra_delay, event_risk, total_score, is_mock_llm, gemini_key
            )

            scored_routes.append({
                "route_id": r_id,
                "name": route["name"],
                "corridor": route.get("corridor", ""),
                "distance_km": route.get("distance_km", 0),
                "adjusted_eta_minutes": adjusted_eta,
                "score": total_score,
                "breakdown": {
                    "congestion_penalty": round(congestion_penalty, 1),
                    "event_risk": round(event_risk, 1),
                    "incident_penalty": round(incident_penalty, 1)
                },
                "reason": explanation,
                "steps": route.get("steps", [])
            })

        # Rank routes: lowest penalty score first
        scored_routes.sort(key=lambda x: x["score"])

        top_route = scored_routes[0]["name"] if scored_routes else "None"
        llm_mode = "Gemini Flash API" if (not is_mock_llm and gemini_key) else "Deterministic Rule-Based Heuristics"
        agent_log = (
            f"Scored {len(scored_routes)} candidate routes using {llm_mode}. "
            f"Top Ranked Optimal Route: '{top_route}' (Score: {scored_routes[0]['score'] if scored_routes else 'N/A'}, "
            f"ETA: {scored_routes[0]['adjusted_eta_minutes'] if scored_routes else 'N/A'} min)."
        )

        return {
            "agent_name": "Evaluator Agent (Agent 3)",
            "llm_mode": llm_mode,
            "ranked_routes": scored_routes,
            "agent_log": agent_log
        }

    def _generate_reason(
        self, route_name: str, eta: int, delay: int, event_risk: int, score: float, is_mock_llm: bool, gemini_key: str
    ) -> str:
        # If Gemini Flash key is provided and not in mock mode, attempt minimal one-line LLM summary
        if not is_mock_llm and gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                prompt = (
                    f"Write exactly ONE short, crisp, human-readable sentence explaining why route '{route_name}' "
                    f"has an ETA of {eta} mins (delay +{delay}m, event risk {event_risk}/100, score {score}). "
                    f"Be direct and mention the main trade-off in under 15 words."
                )
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = requests.post(url, json=payload, timeout=4)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text:
                        return text
            except Exception:
                pass # Fallback to deterministic string

        # Deterministic Rule-Based Reason
        parts = []
        if delay == 0 and event_risk < 30:
            return f"Optimal balance of travel time ({eta} mins) with free-flowing traffic and no event congestion."
        if delay > 0:
            parts.append(f"adds +{delay}m roadwork/traffic delay")
        if event_risk >= 50:
            parts.append(f"faces high event crowd risk ({event_risk}/100)")
        elif event_risk >= 30:
            parts.append(f"moderate event proximity ({event_risk}/100)")
        
        reason_str = "; ".join(parts) if parts else f"steady traffic conditions across corridor"
        return f"Estimated {eta} mins — {reason_str} (Score: {score})."
