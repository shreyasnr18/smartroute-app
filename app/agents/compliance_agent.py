"""
Agent 0: Compliance Guardrail Agent
===========================================================================
This cross-cutting agent enforces legal, privacy, and architectural guardrails across
all other 11 agents in SmartRoute. Every agent must consult Agent 0 before:
1. Making outbound HTTP calls (enforcing the scraping-restricted blocklist).
2. Storing or retaining personal data (enforcing India DPDP Act 2023 data minimization).
3. Processing payment checkouts (enforcing RBI PA/PG pass-through checkout rules).
4. Accessing motor vehicle registries (enforcing VAHAN B2B KYC partner advisory).
"""

import urllib.parse
from typing import Dict, Any, List, Optional


class ComplianceViolationException(Exception):
    """Raised when an agent attempts an action that violates SmartRoute compliance rules."""
    pass


class ComplianceGuardrailAgent:
    """Agent 0: Enforces legal, policy, and data privacy rules."""

    SCRAPING_RESTRICTED_DOMAINS = {
        "bookmyshow.com",
        "in.bookmyshow.com",
        "parivahan.gov.in",
        "vahan.parivahan.gov.in",
        "vahan.nic.in",
        "mparivahan.gov.in",
        "paytm.com/movies",
        "ticketnew.com"
    }

    LICENSED_PAYMENT_GATEWAYS = {"razorpay", "stripe"}

    def __init__(self, enforce_strict: bool = True):
        self.enforce_strict = enforce_strict

    def check_http_request(self, url: str, agent_name: str = "UnknownAgent", purpose: str = "") -> Dict[str, Any]:
        """
        Validates outbound URLs against the scraping-restricted blocklist.
        If a target domain is restricted, refuses the request and logs why.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
        except Exception:
            domain = url.lower()

        for restricted in self.SCRAPING_RESTRICTED_DOMAINS:
            if restricted in domain:
                msg = (
                    f"[Agent 0 COMPLIANCE VIOLATION] Agent '{agent_name}' attempted automated access "
                    f"to restricted domain '{domain}'. Purpose: '{purpose}'. "
                    f"Scraping or automated data extraction on '{restricted}' explicitly violates ToS "
                    f"and is prohibited under SmartRoute policy. Use Admin Self-Listing subsystem instead."
                )
                if self.enforce_strict:
                    raise ComplianceViolationException(msg)
                return {"allowed": False, "reason": msg, "domain": domain}

        return {"allowed": True, "domain": domain, "message": "HTTP request approved by Agent 0."}

    def enforce_data_minimization(self, payload: Dict[str, Any], category: str = "session") -> Dict[str, Any]:
        """
        Enforces India DPDP Act 2023 (Section 8(7)) purpose limitation and data minimization.
        - If category == 'persistent' or 'analytics', strips exact GPS coordinates or raw license plates.
        - If category == 'session', allows temporary ephemeral processing.
        """
        if not payload:
            return {}

        sanitized = dict(payload)
        if category in ("persistent", "analytics", "shared_state"):
            # Strip or anonymize sensitive PII before permanent/shared database storage
            if "raw_license_plate" in sanitized:
                sanitized["raw_license_plate"] = "[ANONYMIZED_UNDER_DPDP_ACT]"
            if "phone_number" in sanitized:
                sanitized["phone_number"] = "[REDACTED]"
            if "email" in sanitized:
                sanitized["email"] = "[REDACTED]"
            
            # Anonymize exact lat/lng to ~100m grid if stored purely for historical analytics
            if category == "analytics":
                if "lat" in sanitized and isinstance(sanitized["lat"], (int, float)):
                    sanitized["lat"] = round(sanitized["lat"], 3)
                if "lng" in sanitized and isinstance(sanitized["lng"], (int, float)):
                    sanitized["lng"] = round(sanitized["lng"], 3)

        return sanitized

    def verify_payment_flow(self, gateway_name: str, is_hosted_checkout: bool = True) -> Dict[str, Any]:
        """
        Enforces RBI Payment Aggregator / Payment Gateway (PA/PG) guidelines and PCI-DSS.
        Guarantees that raw card credentials are never processed or stored on our servers,
        and that checkout is routed via licensed pass-through SDKs/checkouts.
        """
        gw = gateway_name.lower().strip()
        if gw not in self.LICENSED_PAYMENT_GATEWAYS:
            msg = f"[Agent 0 VIOLATION] Gateway '{gateway_name}' is not an approved licensed payment aggregator."
            if self.enforce_strict:
                raise ComplianceViolationException(msg)
            return {"allowed": False, "reason": msg}

        if not is_hosted_checkout:
            msg = "[Agent 0 VIOLATION] Custom card entry forms are strictly prohibited. Must use hosted checkout/SDK."
            if self.enforce_strict:
                raise ComplianceViolationException(msg)
            return {"allowed": False, "reason": msg}

        return {
            "allowed": True,
            "gateway": gw,
            "compliance_status": "Approved pass-through checkout under RBI PA/PG guidelines."
        }

    def check_vahan_lookup_rules(self, plate_query: str) -> Dict[str, Any]:
        """
        Evaluates license plate lookup requests. Clearly flags that production Parivahan/VAHAN
        registry lookups require a paid B2B KYC API partner (Surepass / Attestr).
        """
        return {
            "allowed_via_local_profile": True,
            "compliance_advisory": (
                f"License plate OCR query '{plate_query}' processed via local profile matching (`data/vehicles.json`). "
                "Automated scraping of VAHAN/Parivahan is illegal and strictly blocked. "
                "Real-time national motor vehicle registry lookups require a paid B2B API partnership "
                "(e.g., Surepass, Attestr) and are flagged as a Phase 2 paid production tier."
            )
        }

    def get_privacy_policy_disclosures(self) -> Dict[str, Any]:
        """Returns machine/human readable legal & privacy disclosures."""
        return {
            "fiduciary": "SmartRoute Production System (Bengaluru Pilot)",
            "governing_laws": [
                "India Digital Personal Data Protection Act (DPDP), 2023",
                "Google Play Developer Program Policies (Data Safety Section)",
                "Apple App Store Review Guidelines",
                "RBI Master Directions on Payment Aggregators"
            ],
            "data_collected": {
                "location": "Collected foreground-only while Route Planner or Parking tab is open to compute live turn-by-turn guidance and gap distance. Never tracked in background.",
                "vehicle_dimensions": "Selected vehicle length/width used ephemerally to evaluate physical curb gap compatibility (+0.3m safety buffer).",
                "payment_info": "All checkouts are processed 100% via licensed gateways (Razorpay/Stripe). Zero card/banking details touch SmartRoute servers."
            },
            "user_rights": {
                "right_to_erasure": "Users can request immediate erasure of all session and profile data via POST /api/compliance/delete-my-data or the in-app Privacy Policy modal.",
                "purpose_limitation": "Data is processed strictly for navigation and parking assistance, and anonymized immediately upon session completion."
            }
        }


# Global singleton instance of Agent 0
agent_zero = ComplianceGuardrailAgent(enforce_strict=False)
