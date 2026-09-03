import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import webbrowser
import threading

app = FastAPI()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")

def load_template(name):
    path = resource_path(f"templates/{name}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/")
def dashboard():
    return HTMLResponse(load_template("index.html"))

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8001")

if __name__ == "__main__":
    threading.Timer(1.25, open_browser).start()
    uvicorn.run("run:app", host="127.0.0.1", port=8001)  # <-- IMPORTANT: "run:app"