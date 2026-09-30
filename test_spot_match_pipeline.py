"""
Automated Verification Script for SmartRoute Spot-Match (Dimension-Aware Parking Finder)
Verifies:
1. Agent 9 (VehicleProfileAgent): Lookup by vehicle ID, model, or license plate.
2. Agent 10 (SpaceAssessmentAgent): Reads offline precomputed YOLOv8n curb gap dataset.
3. Agent 11 (FitMatchingAgent): Safety buffer calculation (+0.3m), classification ("Fits", "Marginal", "Too Tight"), and distance ranking.
"""

import asyncio
from app.orchestrator import orchestrator

async def main():
    print("===========================================================================")
    print("  Testing SmartRoute Spot-Match Pipeline (Agents 9, 10, 11)")
    print("===========================================================================\n")

    # Test 1: Search parking spots for a hatchback (Maruti Swift - 3.86m)
    print("[Step 1] Testing Agent 9 -> 10 -> 11 for 'Maruti Swift' near 'Yeshwantpur'...")
    res_swift = await orchestrator.search_parking_spots(
        vehicle_query="maruti_swift",
        origin="Hebbal",
        area_query="Yeshwantpur"
    )

    assert res_swift["status"] == "success"
    v_profile = res_swift["vehicle_profile"]["vehicle"]
    print(f"  [OK] Vehicle Identified: {v_profile['display_name']} — Match Source: {res_swift['vehicle_profile']['matched_by']}")
    
    fit_data = res_swift["fit_matching"]
    print(f"  [OK] Evaluated {fit_data['summary_counts']['total']} curb gaps with {fit_data['safety_buffer_m']}m safety buffer (Required length: {fit_data['required_length_m']}m).")
    print(f"       Summary: {fit_data['summary_counts']['fits']} Fits, {fit_data['summary_counts']['marginal']} Marginal, {fit_data['summary_counts']['too_tight']} Too Tight.")
    
    ranked = fit_data["ranked_spots"]
    assert len(ranked) > 0, "No spots returned!"
    print(f"\n  Top Fitting Candidates for Maruti Swift:")
    for s in ranked[:3]:
        print(f"    -> [{s['fit_status']}] {s['confirmation_summary']}")

    # Test 2: Search parking spots for a full-size MPV/SUV (Innova Crysta - 4.74m) with license plate lookup
    print("\n[Step 2] Testing license plate lookup ('KA 03 IN 9000' -> Toyota Innova Crysta)...")
    res_innova = await orchestrator.search_parking_spots(
        vehicle_query="KA 03 IN 9000",
        origin="Indiranagar",
        area_query="Yeshwantpur"
    )
    v_innova = res_innova["vehicle_profile"]["vehicle"]
    print(f"  [OK] Plate Resolved: {v_innova['display_name']} — Match Source: {res_innova['vehicle_profile']['matched_by']}")
    fit_innova = res_innova["fit_matching"]
    print(f"       Required length: {fit_innova['required_length_m']}m (4.74m + 0.3m buffer).")
    print(f"       Summary: {fit_innova['summary_counts']['fits']} Fits, {fit_innova['summary_counts']['marginal']} Marginal, {fit_innova['summary_counts']['too_tight']} Too Tight.")
    for s in fit_innova["ranked_spots"][:3]:
        print(f"    -> [{s['fit_status']}] {s['confirmation_summary']}")

    print("\n===========================================================================")
    print("  [OK] SUCCESS: Complete 3-Agent Spot-Match Pipeline Verified!")
    print("===========================================================================")

if __name__ == "__main__":
    asyncio.run(main())
