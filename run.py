from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI()

@app.get("/")
def home():
    return HTMLResponse("<h1>DIKOLO MARCHE !!!</h1>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("run:app", host="0.0.0.0", port=port)
