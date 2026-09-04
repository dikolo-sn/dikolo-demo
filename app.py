print("DIKOLO V1.2 FORCE REBUILD")
from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta

app = FastAPI()

# ===== CONFIG SECURITE =====
DATE_EXPIRATION = datetime(2026, 10, 3)   # 30 jours de test
USER = "admin"
PASS = "1234"

CSS = """<style>
body{font-family:Arial;margin:0;background:#f0f8ff}
header{background:linear-gradient(135deg, #00BFFF 0%, #0099CC 100%);color:white;padding:15px 30px;box-shadow:0 4px 10px rgba(0,191,255,0.3)}
header h2{margin:0 0 10px 0;font-size:22px}
.nav-links{display:flex;gap:10px;flex-wrap:wrap}
.nav-links a{color:white;text-decoration:none;padding:8px 12px;border-radius:8px;font-weight:500;transition:0.3s;font-size:14px}
.nav-links a:hover{background:rgba(255,255,255,0.2)}
.login-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:10px;box-shadow:0 0 10px #ccc}
input,button{width:100%;padding:10px;margin:5px 0;border-radius:5px;border:1px solid #ddd}
button{background:#00BFFF;color:white;border:none;cursor:pointer;font-weight:600}
.welcome-box{background:linear-gradient(135deg, #00BFFF 0%, #0099CC 100%);color:white;padding:40px;border-radius:15px;text-align:center;margin:30px;box-shadow:0 4px 15px rgba(0,191,255,0.2)}
.welcome-box h1{color:white;font-size:32px;margin:0}
.content-box{background:white;padding:30px;margin:30px;border-radius:15px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
@media(max-width: 768px){.nav-links{flex-direction: column;}.login-box{width:90%}}
</style>"""

def build_menu(active):
    modules = [
        ("Accueil","/dashboard"), 
        ("Caisse","/caisse"), 
        ("Etat Caisse","/etat_caisse"),
        ("Facturation","/facturation"), 
        ("Commandes/BLs","/commandes"), 
        ("Produits","/produits"),
        ("Vente","/vente"), 
        ("Historique","/historique"), 
        ("Alertes","/alertes"),
        ("Statistiques","/stats"), 
        ("Inventaire","/inventaire"), 
        ("Exportations","/export"),
        ("Utilisateurs","/users")
    ]
    
    links = ""
    for nom, url in modules:
        if f"/{active}" == url:
            links += f"<a href='{url}' style='background:rgba(255,255,255,0.3)'>{nom}</a>"
        else:
            links += f"<a href='{url}'>{nom}</a>"
    
    return f"""
    <header>
        <h2>DiKoLo (Digante-Koungheul-Lour)</h2>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
            <nav class='nav-links'>{links}</nav>
            <a href='/logout' style='background:#ff4444;padding:8px 15px;border-radius:5px;color:white;text-decoration:none;font-weight:600'>Déconnexion</a>
        </div>
    </header>
    """

# ===== MIDDLEWARE EXPIRATION =====
@app.middleware("http")
async def check_license(request: Request, call_next):
    if datetime.now() > DATE_EXPIRATION:
        return HTMLResponse("<h1 style='text-align:center;margin-top:100px'>Version d'essai expirée</h1>")
    return await call_next(request)

# ===== ROUTES LOGIN =====
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(f"{CSS}<div class='login-box'><h1>DiKoLo Login</h1><form method='post'><input name='username' placeholder='Username' required><input name='password' type='password' placeholder='Password' required><button type='submit'>Se connecter</button></form></div>")

@app.post("/login")
async def do_login(username: str = Form(...), password: str = Form(...)):
    if username == USER and password == PASS:
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie("user", "admin")
        return response
    return RedirectResponse(url="/login", status_code=302)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user")
    return response

# ===== FONCTION PAGE CONSTRUCTION =====
def page_construction(titre, user):
    menu = build_menu(titre.lower())
    return HTMLResponse(f"""{CSS}{menu}
    <div class="content-box">
        <h1>{titre}</h1>
        <p>Module en cours de développement</p>
    </div>
    """)

# ===== ROUTES APP =====
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(user: str = Cookie(None)):
    if user != "admin": 
        return RedirectResponse(url="/login")
    menu = build_menu("dashboard")
    return HTMLResponse(f"""{CSS}{menu}
    <div class="welcome-box">
        <h1>Bienvenue admin</h1>
        <p>Version securisee + Mobile OK</p>
    </div>
    """)

# TOUTES LES AUTRES ROUTES
@app.get("/produits", response_class=HTMLResponse)
async def produits(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Produits", user)

@app.get("/caisse", response_class=HTMLResponse)
async def caisse(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Caisse", user)

@app.get("/etat_caisse", response_class=HTMLResponse)
async def etat_caisse(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Etat Caisse", user)

@app.get("/facturation", response_class=HTMLResponse)
async def facturation(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Facturation", user)

@app.get("/commandes", response_class=HTMLResponse)
async def commandes(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Commandes/BLs", user)

@app.get("/vente", response_class=HTMLResponse)
async def vente(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Vente", user)

@app.get("/historique", response_class=HTMLResponse)
async def historique(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Historique", user)

@app.get("/alertes", response_class=HTMLResponse)
async def alertes(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Alertes", user)

@app.get("/stats", response_class=HTMLResponse)
async def stats(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Statistiques", user)

@app.get("/inventaire", response_class=HTMLResponse)
async def inventaire(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Inventaire", user)

@app.get("/export", response_class=HTMLResponse)
async def export(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Exportations", user)

@app.get("/users", response_class=HTMLResponse)
async def users(user: str = Cookie(None)):
    if user != "admin": return RedirectResponse(url="/login")
    return page_construction("Utilisateurs", user)

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")
