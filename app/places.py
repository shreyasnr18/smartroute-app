from typing import List, Dict, Any

BENGALURU_PLACES: List[Dict[str, Any]] = [
    {"name": "Hebbal", "locality": "North Bengaluru", "lat": 13.0358, "lng": 77.5970, "corridors": ["route_orr_tinfactory", "route_hennur_kalyannagar", "route_thanisandra_bypass"]},
    {"name": "KR Puram via Tin Factory", "locality": "East Bengaluru Junction", "lat": 13.0012, "lng": 77.6970, "corridors": ["route_orr_tinfactory", "route_hennur_kalyannagar", "route_thanisandra_bypass"]},
    {"name": "KR Puram Railway Station", "locality": "East Bengaluru", "lat": 13.0035, "lng": 77.6744, "corridors": ["route_orr_tinfactory"]},
    {"name": "Tin Factory Junction", "locality": "Outer Ring Road East", "lat": 12.9941, "lng": 77.6662, "corridors": ["route_orr_tinfactory"]},
    {"name": "Manyata Tech Park", "locality": "Hebbal ORR", "lat": 13.0487, "lng": 77.6200, "corridors": ["route_orr_tinfactory", "route_thanisandra_bypass"]},
    {"name": "Hennur Main Road", "locality": "North-East Bengaluru", "lat": 13.0285, "lng": 77.6398, "corridors": ["route_hennur_kalyannagar"]},
    {"name": "Kalyan Nagar", "locality": "HRBR Layout / Outer Ring Road", "lat": 13.0180, "lng": 77.6432, "corridors": ["route_hennur_kalyannagar"]},
    {"name": "Ramamurthy Nagar", "locality": "East Bengaluru", "lat": 13.0163, "lng": 77.6781, "corridors": ["route_hennur_kalyannagar", "route_orr_tinfactory"]},
    {"name": "Thanisandra Main Road", "locality": "North Bengaluru", "lat": 13.0560, "lng": 77.6330, "corridors": ["route_thanisandra_bypass"]},
    {"name": "Bhartiya City", "locality": "Thanisandra", "lat": 13.0850, "lng": 77.6360, "corridors": ["route_thanisandra_bypass"]},
    {"name": "Old Madras Road Bypass", "locality": "East Peripheral Corridor", "lat": 13.0080, "lng": 77.6850, "corridors": ["route_thanisandra_bypass"]},
    {"name": "Indiranagar 100 Feet Road", "locality": "Central-East Bengaluru", "lat": 12.9784, "lng": 77.6408, "corridors": ["route_orr_tinfactory"]},
    {"name": "Koramangala 80 Feet Road", "locality": "South-East Bengaluru", "lat": 12.9352, "lng": 77.6245, "corridors": ["route_orr_tinfactory"]},
    {"name": "Whitefield ITPL", "locality": "East Bengaluru IT Corridor", "lat": 12.9860, "lng": 77.7373, "corridors": ["route_orr_tinfactory", "route_thanisandra_bypass"]},
    {"name": "Marathahalli Bridge", "locality": "Outer Ring Road East", "lat": 12.9569, "lng": 77.7011, "corridors": ["route_orr_tinfactory"]},
    {"name": "Bellandur Junction", "locality": "Outer Ring Road South-East", "lat": 12.9260, "lng": 77.6762, "corridors": ["route_orr_tinfactory"]},
    {"name": "Kadubeesanahalli / Cessna Business Park", "locality": "Outer Ring Road", "lat": 12.9360, "lng": 77.6910, "corridors": ["route_orr_tinfactory"]},
    {"name": "Sarjapur Road / Wipro Signal", "locality": "South-East Bengaluru", "lat": 12.9166, "lng": 77.6790, "corridors": ["route_orr_tinfactory"]},
    {"name": "Electronic City Phase 1", "locality": "South Bengaluru Tech Hub", "lat": 12.8452, "lng": 77.6602, "corridors": ["route_orr_tinfactory"]},
    {"name": "Silk Board Junction", "locality": "South ORR Intersection", "lat": 12.9177, "lng": 77.6238, "corridors": ["route_orr_tinfactory"]},
    {"name": "Madiwala", "locality": "South Bengaluru", "lat": 12.9226, "lng": 77.6174, "corridors": ["route_orr_tinfactory"]},
    {"name": "Jayanagar 4th Block", "locality": "South Bengaluru", "lat": 12.9250, "lng": 77.5838, "corridors": ["route_orr_tinfactory"]},
    {"name": "MG Road / Brigade Road", "locality": "Central Business District", "lat": 12.9756, "lng": 77.6067, "corridors": ["route_orr_tinfactory", "route_hennur_kalyannagar"]},
    {"name": "Domlur Flyover / EGL Tech Park", "locality": "Central-East Bengaluru", "lat": 12.9609, "lng": 77.6387, "corridors": ["route_orr_tinfactory"]},
    {"name": "Bagmane Tech Park", "locality": "CV Raman Nagar", "lat": 12.9818, "lng": 77.6644, "corridors": ["route_orr_tinfactory", "route_hennur_kalyannagar"]},
    {"name": "Kempegowda International Airport (BLR)", "locality": "Devanahalli / Bellary Road", "lat": 13.1986, "lng": 77.7066, "corridors": ["route_thanisandra_bypass", "route_hennur_kalyannagar"]},
    {"name": "Yelahanka New Town", "locality": "North Bengaluru", "lat": 13.1007, "lng": 77.5963, "corridors": ["route_thanisandra_bypass"]},
    {"name": "Yeshwanthpur Junction", "locality": "North-West Bengaluru", "lat": 13.0238, "lng": 77.5530, "corridors": ["route_orr_tinfactory"]},
    {"name": "Malleshwaram 18th Cross", "locality": "North-West Bengaluru", "lat": 13.0076, "lng": 77.5684, "corridors": ["route_orr_tinfactory"]},
    {"name": "Rajajinagar 1st Block", "locality": "West Bengaluru", "lat": 12.9982, "lng": 77.5530, "corridors": ["route_orr_tinfactory"]},
    {"name": "Peenya Industrial Area", "locality": "North-West Bengaluru", "lat": 13.0330, "lng": 77.5190, "corridors": ["route_orr_tinfactory"]},
    {"name": "Banashankari 2nd Stage", "locality": "South-West Bengaluru", "lat": 12.9255, "lng": 77.5667, "corridors": ["route_orr_tinfactory"]},
    {"name": "Basavanagudi / Vidyarthi Bhavan", "locality": "South Bengaluru", "lat": 12.9421, "lng": 77.5756, "corridors": ["route_orr_tinfactory"]},
    {"name": "BTM Layout 2nd Stage", "locality": "South Bengaluru", "lat": 12.9166, "lng": 77.6101, "corridors": ["route_orr_tinfactory"]},
    {"name": "Hoodi Junction", "locality": "ITPL Main Road", "lat": 12.9916, "lng": 77.7162, "corridors": ["route_orr_tinfactory", "route_thanisandra_bypass"]}
]

def suggest_bengaluru_places(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Returns matching Bengaluru places based on prefix or substring matching."""
    q = query.strip().lower()
    if not q:
        return BENGALURU_PLACES[:limit]

    # Prioritize exact prefix matches, then substring matches
    prefix_matches = []
    substr_matches = []

    for place in BENGALURU_PLACES:
        name_lower = place["name"].lower()
        locality_lower = place["locality"].lower()
        if name_lower.startswith(q):
            prefix_matches.append(place)
        elif q in name_lower or q in locality_lower:
            substr_matches.append(place)

    results = prefix_matches + substr_matches
    # Remove duplicates while preserving order
    seen = set()
    unique_results = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique_results.append(r)
            if len(unique_results) >= limit:
                break

    return unique_results

def get_place_details(place_name: str) -> Dict[str, Any]:
    """Find details by name, fallback to approximate match."""
    p_lower = place_name.strip().lower()
    for place in BENGALURU_PLACES:
        if place["name"].lower() == p_lower:
            return place
    for place in BENGALURU_PLACES:
        if p_lower in place["name"].lower():
            return place
    return {"name": place_name, "locality": "Bengaluru Urban", "lat": 12.9716, "lng": 77.5946, "corridors": ["route_orr_tinfactory", "route_hennur_kalyannagar", "route_thanisandra_bypass"]}
