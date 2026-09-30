import asyncio
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from app.orchestrator import orchestrator

async def test_show_and_routing_pipeline():
    print("=" * 75)
    print("  Testing Show Discovery -> Proximity & Cost -> Booking -> Auto-Routing")
    print("=" * 75)

    # 1. Test Agent 6 & Agent 7 via search_shows
    print("\n[Step 1] Running Agent 6 (ShowDiscovery) & Agent 7 (VenueCost)...")
    search_res = await orchestrator.search_shows(
        show_name="Sikandar",
        city="Bengaluru",
        budget_per_ticket=600.0,
        ticket_count=3,
        screen_types=["Any"],
        location_pref="Malleshwaram/Yeshwantpur",
        origin="Hebbal"
    )

    assert search_res["status"] == "success", "search_shows failed status"
    shows = search_res["shows"]
    print(f"  [OK] Found {len(shows)} candidate shows matching criteria.")
    for s in shows[:3]:
        print(f"      -> {s['selection_summary']}")
        assert s["ticket_count"] == 3
        assert s["total_cost"] > 0
        assert s["distance_km"] > 0

    if not shows:
        print("  [ERROR] No shows returned from search.")
        sys.exit(1)

    top_show = shows[0]
    print(f"\n[Step 2] Selecting top show: '{top_show['show_name']}' at '{top_show['mall_theatre']}'")

    # 2. Test Agent 8 & Auto-Routing Handoff via confirm_booking_and_route
    print("\n[Step 3] Firing mock payment callback (Agent 8) and testing Auto-Routing handoff...")
    callback_res = await orchestrator.confirm_booking_and_route(
        show_id=top_show["show_id"],
        ticket_count=3,
        origin="Hebbal",
        venue_name=top_show["mall_theatre"],
        lat=top_show["lat"],
        lng=top_show["lng"],
        total_cost=top_show["total_cost"]
    )

    assert callback_res["status"] == "success", "confirm_booking_and_route failed status"
    receipt = callback_res["booking_confirmation"]["receipt_id"]
    print(f"  [OK] Booking confirmed! Receipt ID: {receipt}")
    print(f"  [OK] Outbound BookMyShow link generated: {callback_res['booking_confirmation']['bookmyshow_outbound_url']}")

    route_res = callback_res["route_result"]
    assert route_res["status"] == "success", "Route pipeline handoff failed"
    assigned_route = route_res["assigned_route"]
    print(f"  [OK] Auto-Routing 5-Agent pipeline completed in {route_res['pipeline_time_ms']} ms!")
    print(f"      -> Assigned Route: {assigned_route['name']} (ETA: {assigned_route['eta_minutes']} mins, Dist: {assigned_route['distance_km']} km)")
    print(f"      -> Corridor Status: {route_res['diversion_info']['status_badge']}")
    print(f"      -> Evaluator Reason: {assigned_route['reason']}")

    print("\n" + "=" * 75)
    print("  [OK] SUCCESS: Complete 8-Agent Show -> Booking -> Auto-Routing Pipeline Verified!")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(test_show_and_routing_pipeline())
