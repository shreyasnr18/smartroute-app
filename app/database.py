import sqlite3
import datetime
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.config import load_config, get_time_bucket_minutes, get_parking_expiry_minutes

DB_FILE = Path(__file__).parent.parent / "smartroute.db"

# Global Firestore reference
_firestore_db = None
_firestore_initialized = False

def init_firestore() -> Optional[Any]:
    """Initializes Firebase Firestore if credentials or project ID are configured."""
    global _firestore_db, _firestore_initialized
    if _firestore_initialized:
        return _firestore_db

    _firestore_initialized = True
    cfg = load_config()
    cred_path = cfg.get("FIREBASE_CREDENTIALS_PATH", "").strip()
    project_id = cfg.get("FIREBASE_PROJECT_ID", "").strip()

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            _firestore_db = firestore.client()
            print(f"[Database] Connected to live Firebase Firestore using {cred_path}")
        elif project_id and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            if not firebase_admin._apps:
                firebase_admin.initialize_app(options={"projectId": project_id})
            _firestore_db = firestore.client()
            print(f"[Database] Connected to live Firebase Firestore project '{project_id}'")
        else:
            print("[Database] Running on local thread-safe SQLite fallback (Firebase credentials not supplied or offline).")
            _firestore_db = None
    except Exception as e:
        print(f"[Database] Firestore initialization fallback: {e}. Using local SQLite.")
        _firestore_db = None

    return _firestore_db

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_load (
            route_id TEXT,
            time_bucket TEXT,
            user_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (route_id, time_bucket)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origin TEXT,
            destination TEXT,
            assigned_route TEXT,
            diverted BOOLEAN,
            reason TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_spots (
            id TEXT PRIMARY KEY,
            location_id TEXT,
            address TEXT,
            lat REAL,
            lng REAL,
            gap_length_m REAL,
            curb_side TEXT,
            timestamp TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    init_firestore()

def get_current_time_bucket() -> str:
    """Returns the current time bucket string (e.g., '2026-07-17 16:00') based on TIME_BUCKET_MINUTES."""
    now = datetime.datetime.now()
    bucket_mins = get_time_bucket_minutes()
    minute = (now.minute // bucket_mins) * bucket_mins
    bucket_time = now.replace(minute=minute, second=0, microsecond=0)
    return bucket_time.strftime("%Y-%m-%d %H:%M")

def get_route_load(route_id: str, time_bucket: str = None) -> int:
    if time_bucket is None:
        time_bucket = get_current_time_bucket()
    
    # Try Firestore real-time shared state
    db = init_firestore()
    if db:
        try:
            doc_ref = db.collection("smartroute_route_loads").document(f"{route_id}_{time_bucket}")
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("user_count", 0)
            return 0
        except Exception:
            pass # Fallback to SQLite below if Firestore network fails

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_count FROM route_load WHERE route_id = ? AND time_bucket = ?",
        (route_id, time_bucket)
    )
    row = cursor.fetchone()
    conn.close()
    return row["user_count"] if row else 0

def increment_route_load(route_id: str, time_bucket: str = None) -> int:
    if time_bucket is None:
        time_bucket = get_current_time_bucket()
    
    # Try Firestore real-time shared state
    db = init_firestore()
    if db:
        try:
            from firebase_admin import firestore
            doc_ref = db.collection("smartroute_route_loads").document(f"{route_id}_{time_bucket}")
            @firestore.transactional
            def update_in_transaction(transaction, ref):
                snapshot = ref.get(transaction=transaction)
                if snapshot.exists:
                    new_count = snapshot.to_dict().get("user_count", 0) + 1
                    transaction.update(ref, {"user_count": new_count, "last_updated": datetime.datetime.now().isoformat()})
                    return new_count
                else:
                    transaction.set(ref, {"route_id": route_id, "time_bucket": time_bucket, "user_count": 1, "last_updated": datetime.datetime.now().isoformat()})
                    return 1
            transaction = db.transaction()
            new_count = update_in_transaction(transaction, doc_ref)
            # Also mirror locally for offline reliability
            _increment_sqlite(route_id, time_bucket)
            return new_count
        except Exception as e:
            pass # Fallback to SQLite below

    return _increment_sqlite(route_id, time_bucket)

def _increment_sqlite(route_id: str, time_bucket: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO route_load (route_id, time_bucket, user_count, last_updated)
        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(route_id, time_bucket)
        DO UPDATE SET user_count = user_count + 1, last_updated = CURRENT_TIMESTAMP
    """, (route_id, time_bucket))
    conn.commit()
    cursor.execute(
        "SELECT user_count FROM route_load WHERE route_id = ? AND time_bucket = ?",
        (route_id, time_bucket)
    )
    row = cursor.fetchone()
    conn.close()
    return row["user_count"] if row else 1

def log_assignment(origin: str, destination: str, assigned_route: str, diverted: bool, reason: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO route_logs (timestamp, origin, destination, assigned_route, diverted, reason)
        VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
    """, (origin, destination, assigned_route, 1 if diverted else 0, reason))
    conn.commit()
    conn.close()

def sync_parking_spot(spot_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stores or updates a crowdsourced curb parking spot report in Firestore & local SQLite.
    Guarantees auto-expiry calculation by stamping exact timestamp.
    """
    spot_id = spot_data.get("id") or f"spot_{uuid.uuid4().hex[:8]}"
    location_id = spot_data.get("location_id", "Bengaluru_Curb")
    address = spot_data.get("address", "Unknown Location")
    lat = float(spot_data.get("lat", 13.035))
    lng = float(spot_data.get("lng", 77.595))
    gap_length_m = float(spot_data.get("gap_length_m", 5.0))
    curb_side = spot_data.get("curb_side", "left")
    timestamp = spot_data.get("timestamp") or datetime.datetime.now().isoformat()

    record = {
        "id": spot_id,
        "location_id": location_id,
        "address": address,
        "lat": lat,
        "lng": lng,
        "gap_length_m": gap_length_m,
        "curb_side": curb_side,
        "timestamp": timestamp
    }

    # Try Firestore sync
    db = init_firestore()
    if db:
        try:
            db.collection("parking_spots").document(spot_id).set(record)
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parking_spots (id, location_id, address, lat, lng, gap_length_m, curb_side, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            gap_length_m = excluded.gap_length_m,
            timestamp = excluded.timestamp
    """, (spot_id, location_id, address, lat, lng, gap_length_m, curb_side, timestamp))
    conn.commit()
    conn.close()
    return record

def get_active_parking_spots(expiry_minutes: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns all crowdsourced parking spots whose timestamp is newer than `expiry_minutes`.
    Dynamic auto-expiry ensures old/stale spots are filtered out automatically.
    """
    if expiry_minutes is None:
        expiry_minutes = get_parking_expiry_minutes()
    
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=expiry_minutes)
    
    # Try Firestore first
    db = init_firestore()
    if db:
        try:
            docs = db.collection("parking_spots").get()
            active = []
            for d in docs:
                data = d.to_dict()
                ts_str = data.get("timestamp", "")
                try:
                    # Parse timestamp ISO or float
                    if isinstance(ts_str, (int, float)):
                        ts = datetime.datetime.fromtimestamp(ts_str)
                    else:
                        ts = datetime.datetime.fromisoformat(ts_str.replace("Z", ""))
                    if ts >= cutoff:
                        active.append(data)
                except Exception:
                    active.append(data) # Include if format unrecognized
            if active:
                return active
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_spots")
    rows = cursor.fetchall()
    conn.close()

    active_local = []
    for row in rows:
        data = dict(row)
        ts_str = data.get("timestamp", "")
        try:
            if isinstance(ts_str, (int, float)):
                ts = datetime.datetime.fromtimestamp(ts_str)
            else:
                ts = datetime.datetime.fromisoformat(str(ts_str).replace("Z", ""))
            if ts >= cutoff:
                active_local.append(data)
        except Exception:
            active_local.append(data)
    return active_local

def get_all_route_loads(time_bucket: str = None) -> Dict[str, int]:
    if time_bucket is None:
        time_bucket = get_current_time_bucket()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT route_id, user_count FROM route_load WHERE time_bucket = ?", (time_bucket,))
    rows = cursor.fetchall()
    conn.close()
    return {row["route_id"]: row["user_count"] for row in rows}

def get_debug_state() -> Dict[str, Any]:
    bucket = get_current_time_bucket()
    loads = get_all_route_loads(bucket)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM route_logs ORDER BY id DESC LIMIT 20")
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    from app.config import get_capacity_threshold
    capacity = get_capacity_threshold()
    spots = get_active_parking_spots()
    
    return {
        "time_bucket": bucket,
        "capacity_threshold": capacity,
        "loads": loads,
        "active_parking_spots": spots,
        "recent_assignments": logs
    }

def reset_db() -> Dict[str, str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM route_load")
    cursor.execute("DELETE FROM route_logs")
    cursor.execute("DELETE FROM parking_spots")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "All route loads, assignment logs, and parking spots have been reset to 0."}

# Initialize DB on import if needed
init_db()
