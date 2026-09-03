import threading
import time
import sys
import os
import uvicorn
from cefpython3 import cefpython as cef
from run import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def main():
    # 1. Lance FastAPI
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)

    # 2. Lance la fenêtre sans boutons
    sys.excepthook = cef.ExceptHook
    cef.Initialize()
    cef.CreateBrowserSync(
        url="http://127.0.0.1:8000",
        window_title="DiKoLo", 
        window_size=(1200, 800),
        frameless=True,
        resizable=False
    )
    cef.MessageLoop()
    cef.Shutdown()

if __name__ == '__main__':
    main()