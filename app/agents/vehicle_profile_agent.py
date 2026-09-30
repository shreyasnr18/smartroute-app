import json
import os
from typing import Dict, Any, List, Optional
from app.agents.compliance_agent import agent_zero

class VehicleProfileAgent:
    """
    Agent 9: Vehicle-Profile Agent
    Resolves car dimensions (`length_m`, `width_m`) using our high-speed local vehicle dictionary (`data/vehicles.json`).
    Enforces Agent 0 compliance advisory: production Parivahan/VAHAN registration queries require paid B2B KYC
    API partners (Surepass/Attestr) and must never be scraped or faked.
    """
    def __init__(self, data_path: str = "data/vehicles.json"):
        self.data_path = data_path
        self._vehicles = []
        self._load_vehicles()

    def _load_vehicles(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self._vehicles = json.load(f)
            except Exception as e:
                print(f"[VehicleProfileAgent] Error loading {self.data_path}: {e}")
                self._vehicles = self._fallback_vehicles()
        else:
            self._vehicles = self._fallback_vehicles()

    def _fallback_vehicles(self) -> List[Dict[str, Any]]:
        return [
            {"vehicle_id": "maruti_swift", "make": "Maruti Suzuki", "model": "Swift", "length_m": 3.86, "width_m": 1.74, "type": "Hatchback", "sample_plates": ["KA 04 EQ 1234", "SWIFT"]},
            {"vehicle_id": "tata_nexon", "make": "Tata Motors", "model": "Nexon", "length_m": 3.99, "width_m": 1.80, "type": "Compact SUV", "sample_plates": ["KA 51 NX 7788", "NEXON"]},
            {"vehicle_id": "hyundai_creta", "make": "Hyundai", "model": "Creta", "length_m": 4.33, "width_m": 1.79, "type": "Mid-size SUV", "sample_plates": ["KA 05 CR 5566", "CRETA"]},
            {"vehicle_id": "toyota_innova", "make": "Toyota", "model": "Innova Crysta", "length_m": 4.74, "width_m": 1.85, "type": "MPV", "sample_plates": ["KA 03 IN 9000", "INNOVA"]}
        ]

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        return self._vehicles

    async def run(self, vehicle_query: str = "maruti_swift") -> Dict[str, Any]:
        if not vehicle_query or not vehicle_query.strip():
            vehicle_query = "maruti_swift"

        clean_q = vehicle_query.strip().lower()

        # Consult Agent 0 on VAHAN lookup rules
        vahan_rules = agent_zero.check_vahan_lookup_rules(vehicle_query)

        for v in self._vehicles:
            if v.get("vehicle_id", "").lower() == clean_q:
                return self._format_output(v, matched_by="Exact Vehicle ID", compliance_advisory=vahan_rules["compliance_advisory"])

        for v in self._vehicles:
            plates = [p.lower().replace(" ", "") for p in v.get("sample_plates", [])]
            clean_plate_q = clean_q.replace(" ", "")
            if clean_plate_q in plates:
                return self._format_output(v, matched_by=f"License Plate / Keyword '{vehicle_query}'", compliance_advisory=vahan_rules["compliance_advisory"])

        for v in self._vehicles:
            if clean_q in v.get("model", "").lower() or clean_q in v.get("make", "").lower() or clean_q in f"{v.get('make')} {v.get('model')}".lower():
                return self._format_output(v, matched_by=f"Model Name '{vehicle_query}'", compliance_advisory=vahan_rules["compliance_advisory"])

        default_v = self._vehicles[0] if self._vehicles else self._fallback_vehicles()[0]
        return self._format_output(default_v, matched_by="Default Fallback (Maruti Swift)", compliance_advisory=vahan_rules["compliance_advisory"])

    def _format_output(self, v: Dict[str, Any], matched_by: str, compliance_advisory: str) -> Dict[str, Any]:
        return {
            "agent_name": "Vehicle-Profile Agent (Agent 9)",
            "status": "success",
            "lookup_source": "Local Vehicle Dictionary (`data/vehicles.json`)",
            "matched_by": matched_by,
            "compliance_advisory": compliance_advisory,
            "vehicle": {
                "vehicle_id": v.get("vehicle_id", "maruti_swift"),
                "make": v.get("make", "Maruti Suzuki"),
                "model": v.get("model", "Swift"),
                "length_m": float(v.get("length_m", 3.86)),
                "width_m": float(v.get("width_m", 1.74)),
                "type": v.get("type", "Hatchback"),
                "display_name": f"{v.get('make')} {v.get('model')} ({v.get('length_m')}m x {v.get('width_m')}m)"
            }
        }
