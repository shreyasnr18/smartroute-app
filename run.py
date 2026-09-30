import socket
import threading
import webbrowser
import uvicorn
from app.config import load_config

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def open_browser(port: int):
    url = f"http://127.0.0.1:{port}"
    print(f"\n[*] Opening default web browser to {url} ...")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    cfg = load_config()
    # Listen on 0.0.0.0 so both desktop browser (127.0.0.1) and mobile phones on Wi-Fi can connect simultaneously
    host = "0.0.0.0"
    port = int(cfg.get("PORT", 8000))

    if is_port_in_use(port):
        print(f"[!] Warning: Port {port} is currently in use.")
        for p in range(port + 1, port + 6):
            if not is_port_in_use(p):
                print(f"[*] Automatically switching to next available port: {p}")
                port = p
                break

    lan_ip = get_local_ip()

    print("=" * 75)
    print("  SmartRoute — Multi-Agent Traffic Routing Demo (Bengaluru pilot)")
    print(f"  [OK] Desktop Browser URL:   http://127.0.0.1:{port}  (or http://localhost:{port})")
    print(f"  [OK] Mobile Wi-Fi URL:      http://{lan_ip}:{port}   (Scan QR code on UI!)")
    print(f"  [OK] Debug Dashboard:       http://127.0.0.1:{port}/debug/route-load")
    print("=" * 75)

    # Schedule auto-opening the desktop browser 1.2 seconds after uvicorn starts
    threading.Timer(1.2, open_browser, args=[port]).start()

    uvicorn.run("app.main:app", host=host, port=port, reload=False)
