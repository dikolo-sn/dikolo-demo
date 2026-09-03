import threading
import time
import uvicorn
import webview
from run import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == '__main__':
    # 1. Lance FastAPI
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)

    # 2. Lance la fenêtre SANS BARRE
    webview.create_window(
        'DiKoLo', 
        'http://127.0.0.1:8000',
        frameless=True,    # <-- enlève - ⬜ X
        resizable=False,   # <-- bloque redimensionnement
        width=1200,
        height=800
    )
    webview.start()