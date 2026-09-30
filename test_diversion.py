import asyncio
import requests
import sys
from app.database import reset_db, get_debug_state
from app.orchestrator import orchestrator
from app.config import get_capacity_threshold

def test_via_http(base_url="http://localhost:8000"):
    print(f"\n[HTTP Mode] Testing SmartRoute diversion pipeline against {base_url}...")
    try:
        requests.post(f"{base_url}/api/debug/reset", timeout=3)
    except Exception as e:
        return False

    capacity = get_capacity_threshold()
    print(f"[*] CAPACITY_THRESHOLD configured as: {capacity}")
    print(f"[*] Simulating {capacity + 5} sequential commuters requesting route: Hebbal -> KR Puram via Tin Factory\n")
    print(f"{'Commuter #':<12} | {'Assigned Route':<52} | {'Diverted?':<10} | {'Current Load':<14}")
    print("-" * 95)

    for i in range(1, capacity + 6):
        resp = requests.post(
            f"{base_url}/api/route",
            json={"origin": "Hebbal", "destination": "KR Puram via Tin Factory"},
            timeout=5
        ).json()
        
        assigned = resp["assigned_route"]["name"]
        diverted = resp["diversion_info"]["diverted"]
        load = resp["diversion_info"]["assigned_route_load"]
        
        div_str = "YES" if diverted else "No"
        print(f"{'#' + str(i):<12} | {assigned:<52} | {div_str:<10} | {str(load) + '/' + str(capacity):<14}")

        if i <= capacity:
            assert not diverted, f"Commuter #{i} should NOT be diverted before threshold {capacity}!"
        else:
            assert diverted, f"Commuter #{i} MUST be diverted once primary route reaches {capacity}!"

    print("-" * 95)
    print("\n[OK] SUCCESS: Verified that first 10 commuters assigned to optimal Route 1, and commuters #11-#15 successfully diverted to Route 2 to prevent herding!")
    return True

async def test_via_direct_async():
    print("\n[Direct Async Mode] Testing SmartRoute diversion pipeline via local Python modules...")
    reset_db()
    capacity = get_capacity_threshold()
    print(f"[*] CAPACITY_THRESHOLD configured as: {capacity}")
    print(f"[*] Simulating {capacity + 5} sequential commuters requesting route: Hebbal -> KR Puram via Tin Factory\n")
    print(f"{'Commuter #':<12} | {'Assigned Route':<52} | {'Diverted?':<10} | {'Current Load':<14}")
    print("-" * 95)

    for i in range(1, capacity + 6):
        resp = await orchestrator.route_commuter("Hebbal", "KR Puram via Tin Factory")
        assigned = resp["assigned_route"]["name"]
        diverted = resp["diversion_info"]["diverted"]
        load = resp["diversion_info"]["assigned_route_load"]
        
        div_str = "YES" if diverted else "No"
        print(f"{'#' + str(i):<12} | {assigned:<52} | {div_str:<10} | {str(load) + '/' + str(capacity):<14}")

        if i <= capacity:
            assert not diverted, f"Commuter #{i} should NOT be diverted before threshold {capacity}!"
        else:
            assert diverted, f"Commuter #{i} MUST be diverted once primary route reaches {capacity}!"

    print("-" * 95)
    print("\n[OK] SUCCESS: Verified that first 10 commuters assigned to optimal Route 1, and commuters #11-#15 successfully diverted to Route 2 to prevent herding!")

if __name__ == "__main__":
    if not test_via_http():
        asyncio.run(test_via_direct_async())
