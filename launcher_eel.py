import threading
import time
import sys
from cefpython3 import cefpython as cef
import uvicorn
import run # ton fichier de 2800 lignes

def start_server():
    uvicorn.run(run.app, host="127.0.0.1", port=8001, log_level="error")

def main():
    # 1. Lance FastAPI en arrière plan
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    time.sleep(2)

    # 2. Lance Chrome embarqué sans barre d'adresse
    sys.excepthook = cef.ExceptHook
    cef.Initialize()
    cef.CreateBrowserSync(url="http://127.0.0.1:8001/login", window_title="DiKoLo")
    cef.MessageLoop()
    cef.Shutdown()

if __name__ == '__main__':
    main()