import os, sys, json, csv, io, random, time, threading, webbrowser, subprocess
from datetime import datetime, date, timedelta
from collections import Counter
from collections import Counter

from fastapi import FastAPI, Form, UploadFile, File, Depends, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
import pandas as pd
import qrcode
import base64
from io import BytesIO  # <- IL MANQUAIT CELUI CI
import qrcode
import io
import base64
import json
import uuid, qrcode, base64, io
from datetime import datetime
from pydantic import BaseModel
import sqlite3

FICHIER_VENTES = "data/ventes.json"




app = FastAPI()

# 1. Créer la table au démarrage
def init_db():
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()

    # Table paiements si elle n'existe pas
    c.execute("""CREATE TABLE IF NOT EXISTS paiements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_heure TEXT,
        client TEXT,
        montant REAL,
        mode_paiement TEXT,
        detail TEXT,
        reference TEXT NOT NULL,
        statut TEXT
    )""")

    # Table ventes - LA NOUVELLE
    c.execute("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_heure TEXT,
        client TEXT,
        produits TEXT,
        total REAL,
        caissier TEXT,
        paiement TEXT,
        reference TEXT
    )""")

    conn.commit()
    conn.close()

init_db() # <--- AJOUTE CETTE LIGNE SOUS TES IMPORTS

def add_statut_to_ventes():
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE ventes ADD COLUMN statut TEXT DEFAULT 'validee'")
        conn.commit()
        print("✅ Colonne 'statut' ajoutée à ventes")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Colonne 'statut' existe déjà")
        else:
            print("❌ Erreur:", e)
    conn.close()

init_db()
add_statut_to_ventes() # <-- Ajoute cet appel

# 2. Le modèle pour recevoir ton JSON
class Paiement(BaseModel):
    mode_paiement: str
    montant: int
    reference: str
    statut: str

# 3. La route que ton JS appelle
@app.post("/api/paiements")
def enregistrer_paiement(p: Paiement):
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
    c.execute("INSERT INTO paiements (mode_paiement, montant, reference, statut) VALUES (?, ?, ?)",
              (p.mode_paiement, p.montant, p.reference, p.statut))
    conn.commit()
    conn.close()
    return {"status": "ok"}
def charger_json(fichier):
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def sauvegarder_json(fichier, data):
    os.makedirs(os.path.dirname(fichier), exist_ok=True)
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def sauvegarder_vente_paye(ref, mode):
    ventes = charger_json(FICHIER_VENTES)
    for v in ventes:
        if v.get("ref_temp") == ref: 
            v["statut"] = "payee"
            v["mode_paiement"] = mode
            v["date_paiement"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    sauvegarder_json(FICHIER_VENTES, ventes)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")
print("Dossier static:", resource_path("static"))
# TES CHEMINS
F_PRODUITS = resource_path("data/produits.json")
F_VENTES = resource_path("data/ventes.json")
F_PANIER = "panier.json"
# ... garde tous tes autres F_ ...

@app.get("/", response_class=HTMLResponse)
async def index():
    template_path = resource_path('templates/index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

CSS_GLOBAL = """<style>
body{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin:0; background:#ecf0f1}
.container{max-width:1200px; margin:auto; padding:20px}

.nav{
    background: #00BFFF;
    padding: 10px 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.nav-top{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.nav-links{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    align-items: center;
}
.nav a{
    color: white;
    background: transparent;
    text-decoration: none;
    padding: 7px 12px;
    font-weight: 600;
    font-size: 14px;
    border-radius: 5px;
    white-space: nowrap;
}
.nav a:hover{
    background: #1E90FF;
}
.nav a.active{
    background: #1E90FF;
}
.logo-text{
    color: white;
    font-size: 20px;
    font-weight: bold;
}
.logout-btn{
    background: #e74c3c !important;
    margin-left: auto;
}
.logout-btn:hover{
    background: #c0392b !important;
}
.welcome-box{
    background: linear-gradient(135deg, #00BFFF, #1E90FF);
    color: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 20px;
}
.stats-grid{display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-top: 20px}
.card{background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1)}
.card-header{background: #00BFFF; color: white; padding: 12px 15px; border-radius: 8px 8px 0 0; margin: -20px -20px 15px -20px; font-weight: bold}
.top10-table td{padding: 8px}
.badge-qte{background: #2c3e50; color: white; border-radius: 12px; padding: 2px 8px; font-size: 12px}
.badge-ca{color: #27ae60; font-weight: bold}
.filter-bar{display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 15px}
table{background:white; width:100%; border-collapse:collapse; margin-top:15px}
th{background:#2c3e50; color:white} td,th{padding:12px; border:1px solid #ddd; text-align:center}
input,select{padding:10px; width:100%; border:1px solid #ccc; border-radius:5px; box-sizing:border-box}
button, .btn{background:#3498db; color:white; padding:10px 18px; border:none; border-radius:6px; margin:4px; cursor:pointer}
.btn-danger{background:#e74c3c}
.btn-success{background:#27ae60}
</style>"""

#DATA_DIR = "data" 
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
#print("Dossier static:", os.path.join(BASE_DIR, "static"))

def load_data(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):  # si le fichier n'existe pas encore
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(filename, data):
    os.makedirs(DATA_DIR, exist_ok=True) # crée le dossier "data" si besoin
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
app = FastAPI()

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
print("Dossier static:", os.path.join(BASE_DIR, "static"))


F_PRODUITS = "produits.json"
F_VENTES = "ventes.json"
F_ACHATS = "achats.json"
F_USERS = "users.json"
F_ROLES = "roles.json"
F_IPM = "ipm.json"
F_PAIEMENT = "paiements.json"
F_RETOURS = "retours.json"
F_INVENTAIRE = "inventaire.json"
F_DEPENSES = "data/depenses.json"
F_BLS = 'bls.json'
F_LOTS = "lots.json"
F_RAYONS = "rayons.json"
F_ETAGERES = "etageres.json"

PERMISSIONS_LISTE = {
    "voir_dashboard": "Voir Dashboard", "voir_produits": "Gérer Produits", "voir_achat": "Gérer Achats BL",
    "voir_vente": "Faire Vente", "voir_historique": "Voir Historique", "voir_export": "Faire Exports",
    "voir_users": "Gérer Utilisateurs", "voir_caisse": "Accès Caisse", "gerer_ipm": "Gérer IPM/Paiement",
    "voir_alertes": "Voir Alertes", "voir_reception": "Faire Réception", "voir_inventaire": "Faire Inventaire", "voir_reception": "Faire Réception" # <-- AJOUTE ÇA
}
# 1. Crée le dossier data s'il n'existe pas
if not os.path.exists("data"):
    os.mkdir("data")

F_LOTS = "lots.json" # <-- ajoute ça ici

for f in [F_PRODUITS, F_VENTES, F_ACHATS, F_USERS, F_ROLES, F_IPM, F_PAIEMENT, F_RETOURS, F_INVENTAIRE, F_DEPENSES, F_LOTS]:
    if not os.path.exists(f):
        if f == F_USERS:
            with open(f, "w", encoding="utf-8") as file: 
                json.dump({"admin": {"username": "admin", "password": "1234", "role": "admin"}}, file)
        elif f == F_ROLES:
            with open(f, "w", encoding="utf-8") as file: 
                json.dump({"admin": list(PERMISSIONS_LISTE.keys()), "caissier": ["voir_dashboard", "voir_caisse", "voir_historique"], "commercial": ["voir_dashboard", "voir_produits", "voir_achat", "voir_vente", "voir_historique"]}, file)
        elif f == F_IPM:
            with open(f, "w", encoding="utf-8") as file: 
                json.dump([{"nom": "Client Anonyme", "taux": 0}, {"nom": "CNAM 80%", "taux": 80}], file)
        elif f == F_PAIEMENT:
            with open(f, "w", encoding="utf-8") as file: 
                json.dump([{"nom": "Cash"}, {"nom": "Orange Money"}, {"nom": "Wave"}], file)
        else: # <-- ICI IL N'Y A QU'UN SEUL with
            with open(f, "w", encoding="utf-8") as file: 
                json.dump([], file)
F_PRODUITS = "produits.json"

import json, os

F_PRODUITS = 'data/produits.json'
F_IPM = 'data/ipm.json'
F_PAIEMENT = 'data/paiement.json'

def lire(fichier):
    if not os.path.exists(fichier) or os.path.getsize(fichier) == 0:
        return []
    with open(fichier, "r", encoding="utf-8") as f:
        return json.load(f)
def sauver(fichier, data):
    os.makedirs(os.path.dirname(fichier), exist_ok=True)
    with open(fichier, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
def ecrire(fichier, data):
    if not isinstance(data, list): # on force que ce soit une liste
        data = []
    with open(fichier, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_current_user(access_token: str = Cookie(None)):
    if not access_token: return RedirectResponse(url="/login?msg=Veuillez vous connecter")
    users = lire(F_USERS); user = users.get(access_token)
    if not user: return RedirectResponse(url="/login?msg=Session invalide")

    return user
def user_a_permission(user, perm):
    if user["role"] == "admin": return True
    roles = lire(F_ROLES); role_perms = roles.get(user["role"], []); return perm in role_perms
def require_permission(perm):
    def checker(current_user: dict = Depends(get_current_user)):
        if isinstance(current_user, RedirectResponse): return current_user
        if not user_a_permission(current_user, perm): return HTMLResponse("<h1>Accès Refusé</h1><a href='/dashboard'>Retour</a>")
        return current_user
    return checker
def build_menu(current_user, active_page="dashboard"):
    menu = "<div class='nav'>"
    
    # LIGNE 1 : Logo + DiKoLo
    menu += "<div class='nav-top'>"
    menu += "<span class='logo-text'>DiKoLo (Digante-Koungheul-Lour)</span>"
    menu += "</div>"
    # LIGNE 2 : Tous les liens
    menu += "<div class='nav-links'>"
    menu += f"<a href='/dashboard' class='{'active' if active_page=='dashboard' else ''}'>Accueil</a>"
    menu += "<a href='/caisse'>Caisse</a>"
    menu += "<a href='/etatcaisse'>Etat Caisse</a>"
    menu += "<a href='/facturation'>Facturation</a>"
    menu += "<a href='/reception'>Commandes/Bls</a>"
    menu += "<a href='/produits'>Produits</a>"
    menu += "<a href='/vendre'>Vente</a>"
    menu += "<a href='/historique'>Historique</a>"
    menu += "<a href='/alertes'>Alertes</a>"
    menu += "<a href='/stats'>Statistiques</a>"
    menu += "<a href='/inventaire'>Inventaire</a>"
    menu += "<a href='/export'>Exportations</a>"
    menu += "<a href='/users'>Utilisateurs</a>"
    menu += "<a href='/logout' class='logout-btn'>Déconnexion</a>"
    menu += "</div>"
    
    menu += "</div>"
    return menu
CSS = """<style>body{font-family:'Segoe UI',Arial; margin:0; background:#ecf0f1}h1,h2{color:#2c3e50}a,button{background:#3498db; color:white; padding:10px 18px; text-decoration:none; border:none; border-radius:6px; display:inline-block; margin:4px; cursor:pointer; font-weight:bold}a.danger{background:#e74c3c} a.warning{background:#f39c12} a.success{background:#27ae60} a.info{background:#17a2b8}table{background:white; width:100%; border-collapse:collapse; margin-top:15px}th{background:#2c3e50; color:white} td,th{padding:12px; border:1px solid #ddd; text-align:center}input,select{padding:10px; width:100%; border:1px solid #ccc; border-radius:5px; box-sizing:border-box}.nav{background:#34495e; padding:10px}.nav a{background:#34495e; padding:8px 12px; font-size:14px}.card{background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); margin:10px}.login-box{background:white; padding:40px; border-radius:15px; width:350px; margin:80px auto; box-shadow:0 5px 20px rgba(0,0,0,0.2); text-align:center}.error{background:#e74c3c; color:white; padding:10px; border-radius:5px; margin-bottom:15px}.success{background:#27ae60; color:white; padding:10px; border-radius:5px; margin-bottom:15px}
.caisse-container{display:flex; height:calc(100vh - 60px)}.col-gauche{width:20%; padding:10px; overflow-y:auto}.col-droite{width:80%; padding:10px; background:#fff; border-left:2px solid #ddd; overflow-y:auto}.scan-bar{display:flex; gap:5px; margin-bottom:15px}.produit-grid{display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:10px}.produit-card{background:white; border:1px solid #ddd; padding:10px; border-radius:8px; cursor:pointer}.produit-card:hover{border-color:#3498db}.produit-card h4{margin:0; font-size:14px}.produit-card.prix{color:#e74c3c; font-weight:bold; font-size:18px}.produit-card.stock{color:#27ae60; font-size:12px}.commande-header{background:#2c3e50; color:white; padding:10px; text-align:center; font-weight:bold}.form-group{margin-bottom:10px}.form-group label{font-weight:bold; font-size:13px}.ipm-row{display:flex; gap:5px}.panier-table{font-size:12px}.panier-table th{background:#34495e; padding:5px}.total-box{background:#f39c12; color:white; padding:15px; text-align:center; font-size:24px; font-weight:bold; margin:10px 0}.mobile-box{border:2px solid #f39c12; padding:10px; margin:10px 0; border-radius:5px}.perm-grid{display:grid; grid-template-columns: 1fr 1fr; gap:10px}
.alert-box{padding:15px; margin:10px 0; border-radius:8px; border-left:5px solid}.alert-danger{background:#f8d7da; border-color:#e74c3c}.alert-warning{background:#fff3cd; border-color:#f39c12}
body{margin:0;font-family:Arial;background:#eef2f5}
.nav{
    background: #00BFFF;
    padding: 10px 20px;
}
.nav-top{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.nav-links{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    align-items: center;
}
.nav a{
    color: white;
    background: transparent;
    text-decoration: none;
    padding: 7px 12px;
    font-weight: 600;
    font-size: 14px;
    border-radius: 5px;
    white-space: nowrap;
}
.nav a:hover{
    background: #1E90FF;
}
.nav a.active{
    background: #1E90FF; /* pour Accueil actif */
}
.logo-text{
    color: white;
    font-size: 20px;
    font-weight: bold;
}
.logout-btn{
    background: #e74c3c !important;
}
.logout-btn:hover{
    background: #c0392b !important;
}
.welcome-box{
    background: linear-gradient(135deg, #00BFFF, #1E90FF);
    color: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 20px;
}
</style>
<script>
let panier = [];

function addProduit(index, nom, prix){
    let exist = panier.find(p=>p.nom==nom);
    if(exist){ exist.qte++; }
    else{ panier.push({nom:nom, prix:parseFloat(prix), qte:1}); }
    majCaisseEtMobile();
}

function majCaisseEtMobile(){
    if(typeof toggleMobile === 'function'){ toggleMobile(); } // sécurité au cas où
    afficherPanier();
}

function afficherPanier(){
    let tbody = document.getElementById('panier-body');
    tbody.innerHTML='';
    let total=0;

    panier.forEach((p, i)=>{
        let t = p.prix * p.qte;
        total += t;
        tbody.innerHTML += `<tr><td>${p.nom}</td><td><input type='number' value='${p.qte}' style='width:50px' onchange='changerQte(${i}, this.value); majCaisseEtMobile()'></td><td>${t.toFixed(0)} FCFA</td><td><button type="button" onclick='supprimerDuPanier(${i}); majCaisseEtMobile()'>X</button></td></tr>`
    });

    let remise = parseFloat(document.getElementById('remise').value) || 0;
    let ipm_select = document.getElementById('select_ipm').value.split('|');
    let taux = parseInt(ipm_select[1]) || 0;

    let total_apres_remise = total - remise;
    if(total_apres_remise < 0) total_apres_remise = 0;
    let part_ipm = total_apres_remise * taux / 100;
    let part_client = total_apres_remise - part_ipm;

    document.getElementById('total-general').innerText = total.toFixed(0) + ' FCFA';
    document.getElementById('total-client').innerText = part_client.toFixed(0) + ' FCFA';
    document.getElementById('total-ipm').innerText = part_ipm.toFixed(0) + ' FCFA';
    document.getElementById('panier-json').value = JSON.stringify(panier);

    calcMonnaie();
}

function changerQte(index, qte){
    panier[index].qte = parseInt(qte);
    if(panier[index].qte <= 0) panier.splice(index,1);
}

function supprimerDuPanier(index){
    panier.splice(index,1);
}

function calcMonnaie(){
    let a_payer = parseFloat(document.getElementById('total-client').innerText) || 0;
    let recu = parseFloat(document.getElementById('montant_recu').value) || 0;
    let monnaie = recu - a_payer;
    document.getElementById('monnaie').innerText = monnaie.toFixed(0);
    document.getElementById('monnaie-box').style.display = monnaie > 0? 'block' : 'none';
}
function togglePaiementMobile(){
    let mode = document.getElementById('mode_paiement').value;
    document.getElementById('mobile-box').style.display = mode.includes('Money') || mode.includes('Wave')? 'block' : 'none';
}
function ajouterIPM(){
    let nom = prompt("Nom du nouvel IPM:"); let taux = prompt("Taux %:");
    if(nom && taux){ fetch('/ajouter_ipm', {method:'POST', body:new URLSearchParams({nom:nom, taux:taux})}).then(()=>location.reload()); }
}
function ajouterPaiement(){
    let nom = prompt("Nom du nouveau mode de paiement:");
    if(nom){ fetch('/ajouter_paiement', {method:'POST', body:new URLSearchParams({nom:nom})}).then(()=>location.reload()); }

function majCaisseEtMobile(){
    toggleMobile(); // pour le responsive
    afficherPanier(); // pour les calculs
}
function toggleRoleInput(){var s=document.getElementById('role_select');var d=document.getElementById('new_role_div');d.style.display=s.value=='__new__'?'block':'none';}
</script>"""
@app.get("/")
async def home(): return RedirectResponse(url="/login", status_code=303)

@app.get("/login")
async def login_get(msg: str = ""):
    err = f"<div class='error'>{msg}</div>" if msg else ""
    return HTMLResponse(CSS + f"<div class='login-box'><h1>DiKoLo</h1><h3>Gestion + Caisse</h3>{err}<form method='post' action='/login'><input name='username' placeholder='Login' required><br><br><input name='password' type='password' placeholder='Mot de passe' required><br><br><button style='width:100%'>SE CONNECTER</button></form></div>")

@app.post("/login")
async def login_post(username: str = Form(...), password: str = Form(...)):
    users = lire(F_USERS); user = users.get(username)
    if not user or user["password"]!= password: return RedirectResponse(url="/login?msg=Identifiants incorrects", status_code=303)
    response = RedirectResponse(url="/dashboard", status_code=303); response.set_cookie(key="access_token", value=username); return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303); response.delete_cookie("access_token"); return response

@app.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse): return current_user
    produits = lire(F_PRODUITS)
    ventes = lire(F_VENTES)
    achats = lire(F_ACHATS)
    
    # VERSION SÉCURISÉE POUR NE PAS PLANTER
    ca_total = 0
    for v in ventes:
        if isinstance(v, dict): # <-- on vérifie que c'est bien un dict
            ca_total += int(v.get('total', v.get('montant', v.get('prix_total', 0))))
    
    alertes = len([p for p in produits if p.get('stock', 0) < 5])
    
    html = f"""{CSS_GLOBAL}<body>{build_menu(current_user, 'dashboard')}
    <div class='container'>
        <div class='welcome-box'>
            <h1>Bienvenue {current_user['username']}</h1>
            <p>Voici un résumé de votre activité DiKoLo aujourd'hui</p>
        </div>
        
        <h2>Accueil</h2>
        <div style="background:white; padding:20px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1)">
            <h3>Stats</h3>
            <p><b>Produits:</b> {len(produits)} | <b>Ventes:</b> {len(ventes)} | <b>Achats:</b> {len(achats)}</p>
            <p><b>CA Total:</b> {ca_total:.2f} FCFA</p>
            <a href='/alertes' style="background:#e74c3c; padding:10px 15px; border-radius:6px; color:white; text-decoration:none">
                Alertes: {alertes}
            </a>
        </div>
    </div></body>"""
    return HTMLResponse(html)
@app.get("/alertes")
async def page_alertes(current_user: dict = Depends(require_permission("voir_alertes"))):
    if isinstance(current_user, RedirectResponse): return current_user
    produits = lire(F_PRODUITS)
    stock_bas = ""; dlc_proche = ""; auj = date.today()
    for i,p in enumerate(produits):
        if p.get('stock',0) <= p.get('stock_min',5):
            stock_bas += f"<div class='alert-box alert-danger'><b>{p['nom']}</b> Stock: {p['stock']} - Seuil: {p.get('stock_min',5)} <a href='/produits/modifier/{i}'>Commander</a></div>"
        if p.get('dlc'):
            try:
                dlc_date = datetime.strptime(p['dlc'], '%Y-%m-%d').date()
                jours = (dlc_date - auj).days
                if jours <= 30:
                    dlc_proche += f"<div class='alert-box alert-warning'><b>{p['nom']}</b> Expire le: {p['dlc']} - Dans {jours} jours</div>"
            except: pass
    if stock_bas == "": stock_bas = "<div class='success'>Aucun stock bas</div>"
    if dlc_proche == "": dlc_proche = "<div class='success'>Aucune DLC proche</div>"
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Alertes</h1><h2>Stock Bas</h2>{stock_bas}<h2>DLC Proche - 30 jours</h2>{dlc_proche}</div></div>")

import html
from math import ceil

@app.get("/inventaire")
async def page_inventaire(request: Request, q: str = "", page: int = 1, current_user: dict = Depends(require_permission("voir_inventaire"))):
    if isinstance(current_user, RedirectResponse): return current_user
    
    produits = lire(F_PRODUITS)
    menu = build_menu(current_user, 'inventaire')
    
    # 1. RECHERCHE
    if q:
        q_lower = q.lower()
        produits_filtres = [p for p in produits if q_lower in p.get('nom','').lower() or q_lower in p.get('code_barre','').lower()]
    else:
        produits_filtres = produits

    # 2. PAGINATION PAR 10
    par_page = 10
    total = len(produits_filtres)
    pages = ceil(total / par_page) if total > 0 else 1
    page = max(1, min(page, pages))
    debut = (page - 1) * par_page
    produits_page = produits_filtres[debut:debut + par_page]
    
    # 3. LIGNES DU TABLEAU
    lignes = ""
    for p in produits_page:
        stock = p.get('stock',0)
        color = "red" if stock < 5 else "orange" if stock < 20 else "green"
        nom = html.escape(p.get('nom',''))
        code = html.escape(p.get('code_barre',''))
        lignes += f"<tr><td>{nom}</td><td>{code}</td><td style='color:{color}; font-weight:bold'>{stock}</td><td>{int(p.get('prix_achat',0))} FCFA</td><td>{int(p.get('prix_vente',0))} FCFA</td></tr>"
    
    if not lignes:
        lignes = "<tr><td colspan='5' style='text-align:center;padding:20px'>Aucun produit trouvé</td></tr>"

    # 4. BOUTONS PAGINATION
    boutons = ""
    if pages > 1:
        q_esc = html.escape(q)
        for i in range(1, pages + 1):
            style = "background:#2ecc71;color:white;border-color:#2ecc71" if i == page else ""
            boutons += f"<a href='/inventaire?q={q_esc}&page={i}' style='padding:8px 12px;margin:2px;border:1px solid #ccc;border-radius:4px;text-decoration:none;{style}'>{i}</a>"

    q_esc_input = html.escape(q)

    return HTMLResponse(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Inventaire</title>
    {CSS_GLOBAL}
    <style>
    body{{font-family:Arial; background:#f5f7fa; margin:0; padding:0}}
    .container{{padding:20px}}
    .card{{background:white; padding:20px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1)}}
    .card h1{{margin-top:0; color:#2c3e50}}
    .search-bar{{display:flex; gap:10px; margin-bottom:15px}}
    #searchInv{{flex:1; padding:12px; border:1px solid #ddd; border-radius:5px; font-size:14px}}
    table{{width:100%; border-collapse:collapse}}
    th{{background:#34495e; color:white; padding:12px; text-align:left}}
    td{{padding:10px; border-bottom:1px solid #eee}}
    tr:hover{{background:#f8f9fa}}
    .pagination{{display:flex;flex-wrap:wrap;gap:5px;justify-content:center;margin-top:15px}}
    .info{{text-align:center; color:#7f8c8d; margin:10px 0}}
    </style>
    </head><body>
    {menu}
    <div class='container'>
        <div class='card'>
            <h1>📦 Inventaire - {total} Produits</h1>
            <form method='get' action='/inventaire' class='search-bar'>
                <input id='searchInv' name='q' value='{q_esc_input}' placeholder='Recher par nom ou code barre...'>
                <button style='padding:12px 20px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer'>Recher</button>
            </form>
            
            <table id='tableInv'>
                <thead>
                    <tr><th>Produit</th><th>Code Barre</th><th>Stock</th><th>Prix Achat</th><th>Prix Vente</th></tr>
                </thead>
                <tbody>
                    {lignes}
                </tbody>
            </table>

            <div class='info'>Page {page} sur {pages} - Affichage {debut+1} à {min(debut+par_page, total)}</div>
            <div class='pagination'>{boutons}</div>
        </div>
    </div>
    </body></html>""" )
import sqlite3
import html
from math import ceil

@app.get("/historique")
async def page_historique(request: Request, q: str = "", page: int = 1, current_user: dict = Depends(require_permission("voir_historique"))):
    if isinstance(current_user, RedirectResponse): return current_user

    ventes = lire(F_VENTES) 

    # 1. TRI DU PLUS RECENT AU PLUS ANCIEN
    ventes = sorted(ventes, key=lambda x: x.get('date_heure', x.get('date', '0000')), reverse=True)

    # 2. RECHERCHE PAR CLIENT / PRODUIT / REF / CAISSIER
    if q:
        q_lower = q.lower()
        ventes = [v for v in ventes if 
            q_lower in v.get('client','').lower() or 
            q_lower in v.get('caissier','').lower() or 
            q_lower in str(v.get('reference', v.get('id',''))).lower() or
            any(q_lower in p.get('nom','').lower() for p in v.get('panier', []))
        ]

    # 3. PAGINATION 10 LIGNES
    par_page = 10
    total = len(ventes)
    pages = ceil(total / par_page) if total > 0 else 1
    page = max(1, min(page, pages))
    debut = (page - 1) * par_page
    ventes_page = ventes[debut:debut + par_page]

    ventes_html = ""
    for v in ventes_page:
        date_vente = v.get('date_heure', v.get('date', 'N/A'))[:19].replace('T', ' ')
        produits_list = ", ".join([f"{html.escape(p.get('nom',''))} x{p.get('qte',1)}" for p in v.get('panier', [])])
        vente_id = v.get('id', v.get('reference', ''))
        total_v = int(v.get('total',0))
        
        ventes_html += f"""<tr>
            <td>{date_vente}</td>
            <td>{html.escape(v.get('client','Client Anonyme'))}</td>
            <td>{produits_list}</td>
            <td>{total_v:,} FCFA</td>
            <td>{html.escape(v.get('caissier','N/A'))}</td>
            <td>{html.escape(v.get('paiement','Espèces'))}</td>
            <td>{vente_id}</td>
            <td>
                <button onclick="imprimerTicket('{vente_id}')" class="btn-ticket">📄 Imprimer</button>
                <button onclick="retourProduit('{vente_id}')" class="btn-retour">↩️ Retour</button>
            </td>
        </tr>"""
    
    if not ventes_html:
        ventes_html = "<tr><td colspan='8' style='text-align:center;padding:20px'>Aucune vente trouvée</td></tr>"

    # 4. BOUTONS PAGINATION
    boutons = ""
    if pages > 1:
        q_esc = html.escape(q)
        boutons += f"<a href='/historique?q={q_esc}&page=1'>&laquo;</a>" if page > 1 else ""
        for i in range(max(1, page-2), min(pages+1, page+3)):
            style = "background:#2c3e50;color:white;border-color:#2c3e50" if i == page else ""
            boutons += f"<a href='/historique?q={q_esc}&page={i}' style='{style}'>{i}</a>"
        boutons += f"<a href='/historique?q={q_esc}&page={pages}'>&raquo;</a>" if page < pages else ""

    q_esc_input = html.escape(q)

    html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Historique Ventes</title>{CSS_GLOBAL}
        <style>
        .container{{padding:20px}}
        .card{{background:white; padding:20px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1)}}
        .search-bar{{display:flex; gap:10px; margin-bottom:15px}}
        #searchHist{{flex:1; padding:12px; border:1px solid #ddd; border-radius:5px; font-size:14px}}
        table{{width:100%;border-collapse:collapse;margin-top:10px}}
        th{{background:#2c3e50;color:white;padding:12px;text-align:left}}
        td{{border:1px solid #ddd;padding:10px;text-align:left;font-size:14px}}
        tr:hover{{background:#f8f9fa}}
        .btn-ticket{{background:#27ae60;color:white;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;font-size:12px}}
        .btn-retour{{background:#e74c3c;color:white;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;font-size:12px;margin-left:5px}}
        .pagination{{display:flex;flex-wrap:wrap;gap:5px;justify-content:center;margin-top:15px}}
        .pagination a{{padding:8px 12px;margin:2px;border:1px solid #ccc;border-radius:4px;text-decoration:none;color:#2c3e50}}
        .pagination a:hover{{background:#eee}}
        .info{{text-align:center; color:#7f8c8d; margin:10px 0}}
        </style>
        <script>
        function imprimerTicket(venteId) {{ window.open("/ticket_caisse/" + venteId, "_blank"); }}
        function retourProduit(venteId) {{ if(confirm("Confirmer le retour de cette vente ?")) {{ window.location.href = "/retour/" + venteId; }} }}
        </script>
        </head><body>{build_menu(current_user, 'historique')}
    <div class='container'>
        <div class='card'>
            <h2>📜 Historique des Ventes - {total} Ventes</h2>
            <form method='get' action='/historique' class='search-bar'>
                <input id='searchHist' name='q' value='{q_esc_input}' placeholder='Recher: Client, Produit, Ref, Caissier...'>
                <button style='padding:12px 20px;background:#3498db;color:white;border:none;border-radius:5px;cursor:pointer'>Recher</button>
            </form>
            
            <div style="overflow-x:auto">
            <table>
                <thead>
                    <tr><th>Date</th><th>Client</th><th>Produits</th><th>Total</th><th>Caissier</th><th>Paiement</th><th>Reference</th><th>Action</th></tr>
                </thead>
                <tbody>{ventes_html}</tbody>
            </table>
            </div>

            <div class='info'>Page {page} sur {pages} - Affichage {debut+1} à {min(debut+par_page, total)}</div>
            <div class='pagination'>{boutons}</div>
        </div>
    </div></body></html>"""
    return HTMLResponse(html_content)
def enregistrer_paiement_vente(montant, methode, num_transaction):
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS paiements
                 (id INTEGER PRIMARY KEY, methode TEXT, montant REAL, 
                  num_transaction TEXT, statut TEXT, date TEXT)''')
    c.execute("INSERT INTO paiements (methode, montant, num_transaction, statut, date) VALUES (?, ?, ?)",
              (methode, montant, num_transaction, "paye", datetime.now().isoformat()))
    conn.commit()
    conn.close()
@app.get("/retour/{id_vente}")
async def faire_retour(id_vente: str, current_user: dict = Depends(require_permission("voir_historique"))):
    if isinstance(current_user, RedirectResponse): return current_user
    ventes = lire(F_VENTES)
    
    print("ID cherché:", id_vente) # pour debug
    print("Ventes:", [v.get('id') for v in ventes]) # pour debug
    
    vente = next((v for v in ventes if str(v.get('id')) == str(id_vente)), None)
    
    if not vente: return HTMLResponse("Vente introuvable")
    
    options_produits = ""
    for p in vente.get('panier', []):
        options_produits += f"<option value='{p['nom']}' data-max='{p['qte']}'>{p['nom']} - Max: {p['qte']}</option>"
    
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"""
    <div class='nav'>{menu}</div>
    <div style='padding:20px'>
        <div class='card'>
            <h1>Retour Produit - Vente {id_vente}</h1>
            <form method='post' action='/retour/'> 
                <input type='hidden' name='id_vente' value='{id_vente}'>
                <div class='form-group'><label>Produit à retourner</label>
                    <select name='produit_nom' id='produit_select' onchange="document.getElementById('qte_input').max=this.options[this.selectedIndex].dataset.max">
                        {options_produits}
                    </select>
                </div>
                <div class='form-group'><label>Qte</label><input name='qte' id='qte_input' type='number' min='1' value='1' required></div>
                <div class='form-group'><label>Motif</label>
                    <select name='motif'><option>Produit defectueux</option><option>Erreur caisse</option><option>Client insatisfait</option></select>
                </div>
                <button style='background:#e74c3c'>Valider Retour</button>
            </form>
        </div>
    </div>
    """)

@app.post("/retour/")
async def save_retour(id_vente: str = Form(...), produit_nom: str = Form(...), qte: int = Form(...), motif: str = Form(...), current_user: dict = Depends(require_permission("voir_historique"))):
    ventes = lire(F_VENTES); produits = lire(F_PRODUITS); retours = lire(F_RETOURS)
    vente = next((v for v in ventes if str(v.get('id'))==str(id_vente)), None)    
    if vente:
        prix_unitaire = 0
        for p_panier in vente.get('panier', []):
            if p_panier['nom'] == produit_nom: 
                prix_unitaire = p_panier.get('prix', 0)
                p_panier['qte'] -= qte
                if p_panier['qte'] <= 0: vente['panier'].remove(p_panier)

        for p in produits:
            if p['nom'] == produit_nom: 
                p['quantite'] = p.get('quantite',0) + qte # CORRIGE ICI
        
        vente['total'] = vente.get('total', 0) - (prix_unitaire * qte) # Met à jour total

        retours.append({"date": datetime.now().strftime("%d/%m/%Y %H:%M"), "vente_id": id_vente, "produit": produit_nom, "qte": qte, "motif": motif, "user": current_user['username']})
        sauver(F_VENTES, ventes) # SAUVE VENTES
        sauver(F_PRODUITS, produits); sauver(F_RETOURS, retours)
    return RedirectResponse(url="/historique?tab=retours", status_code=303)
@app.get("/migrer")
def migrer():
    ventes = lire(F_VENTES)
    for v in ventes:
        if 'produits_resume' not in v:
            v['produits_resume'] = ", ".join([f"{p['qte']}x {p['nom']}" for p in v.get('panier', [])])
        if 'caissier' not in v: v['caissier'] = 'Admin'
    sauver(F_VENTES, ventes)
    return "Migration OK"
from fastapi import Request # AJOUTE CA EN HAUT
import html # <-- AJOUTE CA EN HAUT AVEC TES AUTRES IMPORTS


import html
import json

@app.get("/caisse")
async def page_caisse(request: Request, current_user: dict = Depends(require_permission("voir_caisse"))):
    if isinstance(current_user, RedirectResponse): return current_user

    produits = lire(F_PRODUITS)
    ipm = lire(F_IPM)
    paiements = lire(F_PAIEMENT)

    noms_paiement = [p['nom'].lower() for p in paiements]
    if 'orange money' not in noms_paiement: paiements.append({'nom':'Orange Money'})
    if 'wave' not in noms_paiement: paiements.append({'nom':'Wave'})

    datalist_html = "".join([
        f"<option value='{html.escape(p.get('nom',''))}' data-id='{i}' data-prix='{p.get('prix_vente',0)}' data-stock='{p.get('stock',0)}' data-code='{html.escape(p.get('code_barre',''))}'></option>"
        for i, p in enumerate(produits)
    ])

    ipm_options = "".join([f"<option value='{html.escape(i.get('nom',''))}|{float(i.get('taux',0))}'>{html.escape(i.get('nom',''))} - {i.get('taux',0)}%</option>" for i in ipm])
    paiement_options = "".join([f"<option value='{html.escape(p.get('nom',''))}'>{html.escape(p.get('nom',''))}</option>" for p in paiements])

    html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Caisse</title>
    {CSS_GLOBAL}
    <style>
   body{{padding:0;margin:0;background:#f5f7fa}}
.caisse-wrap{{display:grid;grid-template-columns:2fr 1fr;gap:15px;padding:15px}}
.scan-bar{{background:#fff3cd;padding:15px;border-radius:8px;margin-bottom:15px}}
.scan-bar label{{font-weight:bold;color:#856404;display:block;margin-bottom:5px}}
.scan-bar input{{width:100%;padding:12px;font-size:16px;border:2px solid #ffc107;border-radius:5px}}
.ajout-produit{{background:white;padding:15px;border-radius:8px;margin-bottom:15px}}
.ajout-produit h3{{color:#27ae60;margin-top:0}}
.produit-table{{width:100%;border-collapse:collapse}}
.produit-table th{{background:#2c3e50;color:white;padding:12px;text-align:left;font-size:14px}}
.produit-table td{{padding:10px;border-bottom:1px solid #eee}}
.produit-table input{{width:100%;padding:8px;border:1px solid #ddd;border-radius:4px}}
.btn-ajout{{background:#27ae60;color:white;border:none;padding:10px 15px;border-radius:4px;cursor:pointer;font-weight:bold}}
.panier-table{{width:100%;background:white;border-radius:8px;overflow:hidden}}
.panier-table th{{background:#34495e;color:white;padding:10px;text-align:left}}
.panier-table td{{padding:8px;border-bottom:1px solid #eee}}
.col-droite.card{{background:white; padding:15px; border-radius:10px; margin-bottom:15px}}
.commande-header{{background:#2c3e50;color:white;padding:12px;text-align:center;font-weight:bold;border-radius:5px 5px 0 0}}
.total-box{{background:#27ae60;color:white;padding:15px;text-align:center;font-size:20px;font-weight:bold}}
.btn-vide{{background:#e74c3c;color:white;border:none;padding:10px;width:100%;border-radius:5px;cursor:pointer;margin-bottom:10px}}
#btn_om_wave{{display:none}}
.mobile-box{{display:none;background:#eaf2ff;padding:10px;border-radius:5px}}
    </style></head>
    <body>
    {build_menu(current_user, 'caisse')}
    <div class='container'>{"<div style='background:#27ae60;color:white;padding:10px;text-align:center'>✅ Vente enregistrée!</div>" if "success=1" in str(request.url) else ""}
    <form method='post' action='/valide_vente' id='form_caisse'>
    <div class='caisse-wrap'>

    <div class='col-gauche'>
        <div class='scan-bar'>
            <label>📷 SCAN CODE BARRE</label>
            <input id='scan' placeholder='Scannez ici' autofocus>
        </div>

        <div class='ajout-produit'>
            <h3>+ Ajouter un produit</h3>
            <table class='produit-table'>
                <thead>
                    <tr>
                        <th style="width:40%">Produit</th>
                        <th style="width:10%">Qte</th>
                        <th style="width:15%">Prix U</th>
                        <th style="width:10%">Stock</th>
                        <th style="width:15%">Total</th>
                        <th style="width:10%">+</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <input list="liste_produits" id="input_produit" placeholder="Taper ou Choisir">
                            <datalist id="liste_produits">{datalist_html}</datalist>
                        </td>
                        <td><input type="number" id="input_qte" value="1" min="1"></td>
                        <td><span id="input_prix">0</span> FCFA</td>
                        <td><span id="input_stock">0</span></td>
                        <td><span id="input_total">0</span> FCFA</td>
                        <td><button type="button" onclick="ajouterLigne()" class="btn-ajout">+</button></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <h3>Panier</h3>
        <table class='panier-table'>
            <thead><tr><th>Produit</th><th>Qte</th><th>Prix</th><th>Total</th><th>X</th></tr></thead>
            <tbody id="panier-body"></tbody>
        </table>
    </div>

    <div class='col-droite'>
        <button type='button' class='btn-vide' onclick='viderPanier()'>🗑️ VIDER PANIER</button>
        <div class='commande-header'>COMMANDE</div>
        <div class='total-box'>Total: <span id="total-general">0</span> FCFA</div>
        <input type="hidden" name="panier_data" id="panier_data">

        <div class='card'>
         <div class='form-group'><label>Client</label><input name='client' value='Client Anonyme'></div>
            <div class='form-group'><label>IPM</label><select name='ipm' id='select_ipm' onchange='majCaisse()'>{ipm_options}</select></div>
            <div class='form-group'><label>Remise FCFA</label><input name='remise' id='remise' type='number' value='0' onchange='majCaisse()'></div>
            <div class='form-group'><label>Mode Paiement</label><select name='mode_paiement' id='mode_paiement' onchange='toggleMobile()'>{paiement_options}</select></div>
            <div class='form-group' id='bloc_transaction' style='display:none;'><label>N° Transaction</label><input type='text' name='num_transaction' id='num_transaction' placeholder='Ex: 771234567'></div>
            <div class='form-group'><label><input type='checkbox' id='tva' name='tva' value='18' onchange='majCaisse()'> TVA 18%</label></div>

            <div id='mobile-box' class='mobile-box'>
                <div style="font-weight:bold;margin-bottom:5px">Paiement Mobile</div>
                <div class='form-group'><label>Numéro Client</label><input name='num_client' id='num_client'></div>
                <div class='form-group'><label>Réf Transaction</label><input id='ref_trans_input' placeholder='Sera rempli après paiement'></div>
            </div>
        </div>

        <div class='card' style='background:#3498db;color:white;text-align:center'>
            Part Client: <span id='total-client'>0</span> FCFA<br>
            Part IPM: <span id='total-ipm'>0</span> FCFA
        </div>

        <div class='form-group'><label>Montant Reçu</label><input name='montant_recu' id='montant_recu' type='number' oninput='calcMonnaie()'></div>
        <div id='monnaie-box' style='display:none;background:#f1c40f;padding:10px;text-align:center;font-weight:bold;border-radius:5px'>Monnaie: <span id='monnaie'>0</span> FCFA</div>

        <button id="btn_valider" class="btn" style="width:100%;background:#27ae60;font-size:16px;padding:12px">VALIDER VENTE CASH</button>

        <div id="btn_om_wave" style="margin-top:10px; padding:15px; border-top:2px solid #0044CC; text-align:center; background:#f5f5f5;">
            <div style="font-size:20px; font-weight:bold; color:#0044CC; margin-bottom:10px;">Total à payer: <span id="total_facture">0</span> F</div>
            <button type="button" onclick="payerV2('OM')" style="background:orange; color:white; padding:12px 20px; margin:5px; border:none; border-radius:8px; font-weight:bold;">Payer OM</button>
            <button type="button" onclick="payerV2('WAVE')" style="background:#0044CC; color:white; padding:12px 20px; margin:5px; border:none; border-radius:8px; font-weight:bold;">Payer Wave</button>
        </div>

        <div id="zone_pay_v2" style="display:none; background:#eaf2ff; padding:15px; margin-top:15px; border:2px dashed #0044CC; border-radius:10px; text-align:center;">
            <h3>Scanner pour payer <span id="mode_pay_v2"></span> : <span id="montant_pay_v2">0</span> F</h3>
            <img id="img_pay_v2" src="" width="110" height="110" alt="QR Code">
            <br><br>
            <input type="text" id="ref_pay_v2" placeholder="Coller N° Transaction ici" style="padding:8px; width:70%">
            <br><br>
            <button type="button" onclick="validerPayV2()" style="background:green; color:white; padding:10px;">Valider</button>
            <button type="button" onclick="annulerPayV2()" style="background:red; color:white; padding:10px;">Annuler</button>
        </div>
    </div>
    </div></form></div>

<script>
let panier = [];
let produits_globaux = {json.dumps(produits)};

document.getElementById('input_produit').addEventListener('input', function(){{
    let val = this.value;
    let option = document.querySelector(`#liste_produits option[value="${{val}}"]`);
    if(option){{
        document.getElementById('input_prix').innerText = option.dataset.prix;
        document.getElementById('input_stock').innerText = option.dataset.stock;
        majLigneTotal();
    }}
}});

document.getElementById('input_qte').addEventListener('input', majLigneTotal);

function majLigneTotal(){{
    let prix = parseFloat(document.getElementById('input_prix').innerText) || 0;
    let qte = parseInt(document.getElementById('input_qte').value) || 0;
    document.getElementById('input_total').innerText = (prix * qte).toFixed(0);
}}

function ajouterLigne(){{
    let nom = document.getElementById('input_produit').value;
    let qte = parseInt(document.getElementById('input_qte').value);
    let option = document.querySelector(`#liste_produits option[value="${{nom}}"]`);
    if(!option){{ alert("Produit introuvable"); return; }}
    let prix = parseFloat(option.dataset.prix);
    let exist = panier.find(x=>x.nom==nom);
    if(exist){{ exist.qte += qte; }} else {{ panier.push({{nom: nom, prix: prix, qte: qte}}); }}
    document.getElementById('input_produit').value = '';
    document.getElementById('input_qte').value = 1;
    document.getElementById('input_prix').innerText = 0;
    document.getElementById('input_stock').innerText = 0;
    majLigneTotal(); majCaisse();
}}

document.getElementById('scan').addEventListener('keypress', function(e){{
    if(e.key === 'Enter'){{
        let code = this.value.trim();
        let option = document.querySelector(`#liste_produits option[data-code="${{code}}"]`);
        if(option){{
            document.getElementById('input_produit').value = option.value;
            document.getElementById('input_qte').value = 1;
            ajouterLigne();
        }} else {{ alert("Produit non trouvé: " + code); }}
        this.value = '';
        e.preventDefault();
    }}
}});

function majCaisse(){{
    let tbody = document.getElementById('panier-body'); tbody.innerHTML=''; let total=0;
    panier.forEach((p, i)=>{{
        let t = p.prix * p.qte; total += t;
        tbody.innerHTML += `<tr><td>${{p.nom}}</td><td><input type='number' value='${{p.qte}}' style='width:60px' onchange='changerQte(${{i}}, this.value)'></td><td>${{p.prix}} FCFA</td><td>${{t.toFixed(0)}} FCFA</td><td><button type="button" onclick='supprimerDuPanier(${{i}})'>X</button></td></tr>`
    }});
    let remise = parseFloat(document.getElementById('remise').value) || 0;
    let taux = parseFloat(document.getElementById('select_ipm').value.split('|')[1]) || 0;
    let total_apres_remise = Math.max(0, total - remise);
    let part_ipm = total_apres_remise * taux / 100;
    let part_client = total_apres_remise - part_ipm;
    document.getElementById('total-general').innerText = total.toFixed(0);
    document.getElementById('total-client').innerText = part_client.toFixed(0);
    document.getElementById('total-ipm').innerText = part_ipm.toFixed(0);
    document.getElementById('panier_data').value = JSON.stringify(panier);
    document.getElementById('total_facture').innerText = part_client.toFixed(0);
    calcMonnaie();
}}

function changerQte(index, qte){{ panier[index].qte = parseInt(qte); if(panier[index].qte <= 0) panier.splice(index,1); majCaisse(); }}
function supprimerDuPanier(index){{ panier.splice(index,1); majCaisse(); }}
function viderPanier(){{ if(panier.length > 0 && confirm("Vider tout le panier?")){{ panier=[]; majCaisse(); }} }}
function calcMonnaie(){{ let a_payer = parseFloat(document.getElementById('total-client').innerText) || 0; let recu = parseFloat(document.getElementById('montant_recu').value) || 0; let monnaie = recu - a_payer; document.getElementById('monnaie').innerText = monnaie.toFixed(0); document.getElementById('monnaie-box').style.display = monnaie > 0? 'block' : 'none'; }}
function toggleMobile(){{ let mode = document.getElementById('mode_paiement').value.toLowerCase(); let divOM = document.getElementById('btn_om_wave'); let btnValider = document.getElementById('btn_valider'); let mobileBox = document.getElementById('mobile-box'); if(mode.includes('orange') || mode.includes('om') || mode.includes('wave')) {{ divOM.style.display = 'block'; btnValider.style.display = 'none'; mobileBox.style.display = 'block'; }} else {{ divOM.style.display = 'none'; btnValider.style.display = 'block'; mobileBox.style.display = 'none'; }} }}
toggleMobile();

function payerV2(mode){{ let total = document.getElementById('total_facture').innerText; document.getElementById('zone_pay_v2').style.display = 'block'; document.getElementById('mode_pay_v2').innerText = mode; document.getElementById('montant_pay_v2').innerText = total; document.getElementById('img_pay_v2').src = '/static/qr_' + mode + '.png?' + Date.now(); }}
function validerPayV2(){{ let ref = document.getElementById('ref_pay_v2').value; if(ref.trim() == ""){{ alert("Colle le N° Transaction"); return; }} let mode = document.getElementById('mode_pay_v2').innerText; if(mode == "OM"){{ document.getElementById('mode_paiement').value = "Orange Money"; }} if(mode == "WAVE"){{ document.getElementById('mode_paiement').value = "Wave"; }} document.getElementById('num_transaction').value = ref; document.getElementById('form_caisse').submit(); }}
function annulerPayV2(){{ document.getElementById('zone_pay_v2').style.display = 'none'; document.getElementById('ref_pay_v2').value = ''; }}

document.querySelector('select[name="mode_paiement"]').addEventListener('change', function(){{ let bloc = document.getElementById('bloc_transaction'); if(this.value == 'Orange Money' || this.value == 'Wave'){{ bloc.style.display = 'block'; bloc.querySelector('input').required = true; }} else {{ bloc.style.display = 'none'; bloc.querySelector('input').required = false; bloc.querySelector('input').value = ''; }} }});
</script>
</body></html>"""
    return HTMLResponse(html_content)
@app.get("/ipm/nouveau")
async def page_ipm_nouveau(current_user: dict = Depends(require_permission("gerer_parametres"))):
    if isinstance(current_user, RedirectResponse): return current_user
    menu = build_menu(current_user)
    return HTMLResponse(f"""
    <!DOCTYPE html><html><head><a href="/caisse" class="btn">+ Retour Caisse</a><meta charset="UTF-8"><title>Nouveau IPM</title>
    <style>body{{font-family:Arial; background:#f4f4f4; margin:0; padding:0}} .nav{{background:#2c3e50; padding:10px; margin-bottom:15px}} .nav a{{color:white; text-decoration:none; padding:8px 12px; display:inline-block}} .card{{background:white; padding:20px; border-radius:8px; max-width:400px; margin:20px auto}} input{{width:100%; padding:8px; margin:8px 0; box-sizing:border-box}}</style>
    </head><body><div class='nav'>{menu}</div><div class='card'>
    <h2>Ajouter un IPM</h2>
    <form method='post' action='/ipm/ajouter'>
        <label>Nom IPM</label><input name='nom' placeholder='Ex: IPM Boutique' required>
        <label>Taux %</label><input name='taux' type='number' step='0.1' placeholder='Ex: 5' required>
        <button style='width:100%; padding:10px; background:#27ae60; color:white; border:none; border-radius:5px; cursor:pointer'>Enregistrer</button>
    </form>
    </div></body></html>
    """)

@app.post("/ipm/ajouter")
async def ajouter_ipm(nom: str = Form(...), taux: float = Form(...), current_user: dict = Depends(require_permission("gerer_parametres"))):
    ipms = lire(F_IPM)
    ipms.append({"nom": nom, "taux": taux})
    ecrire(F_IPM, ipms)
    return RedirectResponse("/caisse", status_code=303)

import json, random, os
from datetime import datetime
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

F_VENTES = "ventes.json"

from fastapi import Form

from fastapi import Request
from pydantic import BaseModel
from typing import List

class LignePanier(BaseModel):
    nom: str
    qte: int
    prix: int
    total: int

class VentePayload(BaseModel):
    client: str
    mode_paiement: str
    panier: List[LignePanier]
    ipm_taux: int = 0
    part_client: int = 0
    part_empl: int = 0
@app.post("/valide_caisse")
async def valide_caisse(
    panier_data: str = Form(...),
    client: str = Form("Client Anonyme"),
    mode_paiement: str = Form("Cash"),
    ipm: str = Form("0"),
    remise: int = Form(0),
    current_user: dict = Depends(require_permission("valider_vente"))
):
    if isinstance(current_user, RedirectResponse): 
        return current_user
    
    ventes = lire(F_VENTES)
    # On nettoie au cas où il y a des strings dans ventes.json
    ventes = [v for v in ventes if isinstance(v, dict)] 
    
    panier = json.loads(panier_data)
    total = sum(int(v.get('total', int(v.get('qte',1)) * int(v.get('prix',0)))) for v in panier)
    
    # GESTION IPM
    ipm_taux = 0
    part_client = total
    part_empl = 0
    if "80" in ipm:
        ipm_taux = 80
        part_empl = int(total * 80 / 100)
        part_client = total - part_empl
    
    # NOUVEL ID SECURISE
    if ventes:
        last_id = max(int(v.get('id', 0)) for v in ventes)
        nouvelle_id = str(last_id + 1)
    else:
        nouvelle_id = "1"
    
    nouvelle_vente = {
        "id": nouvelle_id,
        "date": datetime.now().isoformat(),
        "client": client,
        "caissier": current_user['username'],
        "mode_paiement": mode_paiement,
        "panier": panier,
        "total": total,
        "ipm_taux": ipm_taux,
        "part_client": part_client,
        "part_empl": part_empl,
        "remise": remise
    }
    
    ventes.append(nouvelle_vente)
    ecrire(F_VENTES, ventes)
    
    return RedirectResponse(url=f"/ticket_caisse/{nouvelle_id}", status_code=303)
from datetime import datetime
import sqlite3
import json

from datetime import datetime
import json
from datetime import datetime
import json

@app.post("/valide_vente")
async def valide_vente(request: Request, current_user: dict = Depends(require_permission("valider_vente"))):
    if isinstance(current_user, RedirectResponse): return current_user

    form = await request.form()
    panier = json.loads(form.get("panier_data", "[]"))
    if not panier: return RedirectResponse("/caisse?error=panier_vide", status_code=303)

    ventes = lire(F_VENTES)
    new_id = max([int(v['id']) for v in ventes], default=0) + 1 # <-- CORRIGE ICI
    
    client = form.get("client", "Client Anonyme")
    mode = form.get("mode_paiement", "Cash")
    remise = float(form.get("remise", 0))
    ipm_data = form.get("ipm", "|0").split("|")
    taux_ipm = float(ipm_data[1]) if len(ipm_data) > 1 else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_brut = sum([p['prix'] * p['qte'] for p in panier])
    total_apres_remise = max(0, total_brut - remise)
    part_ipm = total_apres_remise * taux_ipm / 100
    montant = total_apres_remise - part_ipm

    nouvelle_vente = {
        "id": new_id, # <-- ET ICI ON SAUVE EN INT
        "date_heure": now,
        "reference": form.get("num_transaction") or f"V{new_id}",
        "client": client,
        "caissier": current_user.get("username","Admin"),
        "panier": panier,
        "total": montant,
        "paiement": mode,
        "remise": remise,
        "taux_ipm": taux_ipm,
        "part_ipm": part_ipm,
        "part_client": montant
    }
    ventes.append(nouvelle_vente)
    ecrire(F_VENTES, ventes)

    # Mise à jour stock
    produits = lire(F_PRODUITS)
    for item in panier:
        for p in produits:
            if p["nom"] == item["nom"]: p["stock"] -= item["qte"]
    ecrire(F_PRODUITS, produits)
    ecrire(F_PANIER, [])

    return RedirectResponse("/caisse?success=1", status_code=303)
@app.get("/voir_ventes")
async def voir_ventes():
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
    c.execute("SELECT id, date_heure, client, detail, mode_paiement, montant, reference, statut FROM paiements ORDER BY id DESC LIMIT 50")
    ventes = c.fetchall()
    conn.close()
    
    html = """<!DOCTYPE html><html><head><title>Historique Ventes</title>
    <style>body{font-family:Arial;padding:20px} table{width:100%;border-collapse:collapse;font-size:12px} 
    th,td{border:1px solid #ddd;padding:6px;text-align:left} th{background:#2c3e50;color:white}</style>
    </head><body>
    <h1>50 Dernières Ventes</h1><a href='/caisse'>← Retour Caisse</a><br><br>
    <table><tr><th>Date</th><th>Client</th><th>Détail</th><th>Mode</th><th>Montant</th><th>Ref</th><th>Statut</th></tr>"""
    
    for v in ventes:
        html += f"<tr><td>{v[1]}</td><td>{v[2]}</td><td>{v[3]}</td><td>{v[4]}</td><td>{v[5]} FCFA</td><td>{v[6]}</td><td>{v[7]}</td></tr>"
    
    html += "</table></body></html>"
    return HTMLResponse(html)
@app.get("/stats")
def stats(request: Request, current_user: dict = Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse): return current_user
    
    ventes = lire(F_VENTES)
    produits_list = lire(F_PRODUITS)
    produits_dict = {p['id']: p.get('nom','Produit') for p in produits_list if 'id' in p}
    
    # 1. FILTRE PERIODE
    periode = request.query_params.get("periode", "30")
    au = datetime.now()
    if periode == "7":
        du = au - timedelta(days=7)
        label = "7 derniers jours"
    elif periode == "365":
        du = au - timedelta(days=365)
        label = "12 derniers mois"
    else:
        du = au - timedelta(days=30)
        label = "30 derniers jours"
    
    # 2. FILTRER + COMPTER
    ventes_filtrees = []
    compteur_produits = Counter()
    for v in ventes:
        if not isinstance(v, dict): continue
        try:
            date_str = v.get('date','')
            if 'T' in date_str: d = datetime.fromisoformat(date_str)
            elif '/' in date_str: d = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            else: d = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            if d >= du and d <= au:
                ventes_filtrees.append(v)
                # Compter les produits
                for item in v.get('items', v.get('panier', [])):
                    pid = item.get('id')
                    qte = float(item.get('qte', 1))
                    compteur_produits[pid] += qte
        except: pass
    
    ca_total = sum([float(v.get('total',0)) for v in ventes_filtrees])
    nb_ventes = len(ventes_filtrees)
    
    # 3. TOP 5 PRODUITS
    top5 = compteur_produits.most_common(5)
    lignes_top = ""
    for i, (pid, qte) in enumerate(top5, 1):
        nom = produits_dict.get(pid, f"ID {pid}")
        lignes_top += f"<tr><td>{i}</td><td>{nom}</td><td><b>{qte:.0f}</b> vendus</td></tr>"
    if not lignes_top:
        lignes_top = "<tr><td colspan=3 style='text-align:center'>Aucune vente sur cette période</td></tr>"
    
    # 4. HTML
    html = f"""{CSS_GLOBAL} 
    <body>{build_menu(current_user, 'stats')}
    <div class='container'>
        <h1>📊 Statistiques</h1>
        
        <div class="filter-bar" style="display:flex; gap:10px; justify-content:flex-end; margin-bottom:20px">
            <a href="/stats?periode=7" class="btn" style="background:{'#3498db' if periode=='7' else '#bdc3c7'}; color:white">7 jours</a>
            <a href="/stats?periode=30" class="btn" style="background:{'#3498db' if periode=='30' else '#bdc3c7'}; color:white">30 jours</a>
            <a href="/stats?periode=365" class="btn" style="background:{'#3498db' if periode=='365' else '#bdc3c7'}; color:white">12 mois</a>
        </div>
        
        <h3 style="text-align:center; color:#7f8c8d; margin-bottom:20px">Période: {label}</h3>

        <div class='stats-grid'>
            <div class='card' style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color:white; text-align:center">
                <h3>CHIFFRE D'AFFAIRES</h3>
                <h2>{ca_total:.0f} FCFA</h2>
            </div>
            <div class='card' style="background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%); color:white; text-align:center">
                <h3>NOMBRE DE VENTES</h3>
                <h2>{nb_ventes}</h2>
            </div>
        </div>
        
        <div class='card'>
            <h3>🏆 Top 5 Produits les plus vendus</h3>
            <table class='top10-table' style="width:100%">
                <thead><tr style="background:#2c3e50; color:white"><th>#</th><th>Produit</th><th>Quantité</th></tr></thead>
                <tbody>{lignes_top}</tbody>
            </table>
        </div>
    </div>
    </body>"""
    return HTMLResponse(html)
from datetime import datetime



@app.get("/facturation")
async def page_facturation(date_debut: str = "", date_fin: str = "", current_user: dict = Depends(require_permission("voir_facturation"))):
    if isinstance(current_user, RedirectResponse): return current_user

    ventes = lire(F_VENTES)
    ipm_list = lire(F_IPM)

    if date_debut and date_fin:
        ventes = [v for v in ventes if date_debut <= v.get('date','')[:10] <= date_fin]

    data_ipm = {}
    for ipm in ipm_list:
        data_ipm[ipm['nom']] = {'total': 0, 'clients': {}, 'nb_ventes': 0, 'ventes_detail': []}

    for v in ventes:
        ipm_nom = v.get('ipm_nom', 'Client Anonyme')
        part_ipm = float(v.get('part_ipm', 0))
        client = v.get('client', 'Client Anonyme')

        if ipm_nom not in data_ipm:
            data_ipm[ipm_nom] = {'total': 0, 'clients': {}, 'nb_ventes': 0, 'ventes_detail': []}

        data_ipm[ipm_nom]['total'] += part_ipm
        data_ipm[ipm_nom]['nb_ventes'] += 1
        data_ipm[ipm_nom]['ventes_detail'].append(v)

        if client not in data_ipm[ipm_nom]['clients']:
            data_ipm[ipm_nom]['clients'][client] = 0
        data_ipm[ipm_nom]['clients'][client] += part_ipm

    data_ipm = dict(sorted(data_ipm.items(), key=lambda x: x[1]['total'], reverse=True))
    total_general = sum(d['total'] for d in data_ipm.values())
    menu = build_menu(current_user)

    periode_fin = date_fin or "Aujourd'hui"
    periode_debut = date_debut or "Début"

    # GENERER HTML DETAIL AVEC BOUTON IMPRIMER
    details_html = ""
    for idx, (ipm_nom, data) in enumerate(data_ipm.items()):
        if data['total'] > 0:
            clients_rows = "".join([
                f"<tr><td>{client}</td><td>{len([v for v in data['ventes_detail'] if v.get('client')==client])} ventes</td><td>{int(montant)} FCFA</td></tr>"
                for client, montant in sorted(data['clients'].items(), key=lambda x: x[1], reverse=True)
            ])

            ventes_rows = "".join([
                f"<tr><td>{v.get('date','')}</td><td>{v.get('client','')}</td><td>{v.get('produit','')}</td><td>{v.get('qte','')}</td><td>{int(v.get('part_ipm',0))} FCFA</td></tr>"
                for v in data['ventes_detail']
            ])

            details_html += f"""
            <div class='ipm-detail' id='ipm-{idx}'>
                <div class='ipm-header' onclick='toggleDetail(this)'>
                    <div>
                        <h3>{ipm_nom}</h3>
                        <span>{data['nb_ventes']} ventes • {len(data['clients'])} clients</span>
                    </div>
                    <div style='display:flex; align-items:center; gap:15px'>
                        <div class='montant'>{int(data['total'])} FCFA</div>
                        <button class='btn-facture' onclick='imprimerIPM({idx}); event.stopPropagation()'>🖨️ Facture</button>
                        <div>▼</div>
                    </div>
                </div>
                <div class='ipm-content'>
                    <h4>Détail par Client</h4>
                    <table>
                        <tr><th>Client</th><th>Nb Ventes</th><th>Montant</th></tr>
                        {clients_rows}
                    </table>

                    <div id='print-area-{idx}' style='display:none'>
                        <div class='facture-print'>
                            <h1>FACTURE {ipm_nom}</h1>
                            <p><b>Période:</b> {periode_debut} au {periode_fin}</p>
                            <p><b>Total à réclamer:</b> {int(data['total'])} FCFA</p>
                            <p><b>Nombre de ventes:</b> {data['nb_ventes']}</p>
                            <hr>
                            <table>
                                <tr><th>Date</th><th>Client</th><th>Produit</th><th>Qte</th><th>Montant IPM</th></tr>
                                {ventes_rows}
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            """

    CSS_FACT = """
    <style>
    body{font-family:Arial; background:#f5f7fa; margin:0; padding:0}
   .nav{background:#2c3e50; padding:0 10px; display:flex; flex-wrap:wrap}
   .nav a{color:white; text-decoration:none; padding:12px 15px; display:inline-block; font-weight:500}
   .nav a:hover{background:#34495e}
   .container{padding:20px}
   .card{background:white; padding:20px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1)}
   .header-top{display:flex; justify-content:space-between; align-items:center; margin-bottom:20px}
   .header-top h1{margin:0; color:#2c3e50}
   .btn-print{background:#27ae60; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold}
   .btn-facture{background:#3498db; color:white; border:none; padding:6px 12px; border-radius:5px; cursor:pointer; font-size:12px}
   .filtres{display:flex; gap:10px; margin-bottom:20px; align-items:center}
   .filtres input{padding:8px; border:1px solid #ddd; border-radius:5px}
   .filtres button{background:#3498db; color:white; border:none; padding:9px 15px; border-radius:5px; cursor:pointer}
   .total-box{background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:25px; border-radius:10px; text-align:center; margin-bottom:20px}
   .total-box h2{margin:0; font-size:14px; opacity:0.9}
   .total-box.montant{font-size:36px; font-weight:bold; margin-top:8px}
   .ipm-detail{border:1px solid #e0e0e0; border-radius:8px; margin-bottom:12px; overflow:hidden}
   .ipm-header{display:flex; justify-content:space-between; align-items:center; padding:15px 20px; background:#f8f9fa; cursor:pointer}
   .ipm-header:hover{background:#e9ecef}
   .ipm-header h3{margin:0; color:#2c3e50; font-size:16px}
   .ipm-header span{font-size:12px; color:#7f8c8d}
   .ipm-header.montant{font-size:20px; font-weight:bold; color:#27ae60}
   .ipm-content{display:none; padding:15px; background:white}
   .ipm-content table{width:100%; border-collapse:collapse; margin-top:10px}
   .ipm-content th{background:#34495e; color:white; padding:10px; text-align:left; font-size:14px}
   .ipm-content td{padding:10px; border-bottom:1px solid #eee; font-size:14px}
   .facture-print{padding:20px; font-family:Arial}
   .facture-print h1{text-align:center; color:#2c3e50}
   .facture-print table{width:100%; border-collapse:collapse; margin-top:20px}
   .facture-print th{background:#34495e; color:white; padding:10px}
   .facture-print td{padding:8px; border:1px solid #ddd}
    @media print{
       .nav,.filtres,.btn-print,.btn-facture,.ipm-header{display:none}
        body{background:white}
       .ipm-content{display:block!important}
       .card{box-shadow:none; padding:0}
       .facture-print{display:block!important}
    }
    </style>
    """

    SCRIPT = """
    <script>
    function toggleDetail(header){
        let content = header.nextElementSibling;
        content.style.display = content.style.display === 'block'? 'none' : 'block';
    }
    function imprimer(){ window.print(); }
    function imprimerIPM(idx){
        let printArea = document.getElementById('print-area-'+idx).innerHTML;
        let win = window.open('', '', 'height=700,width=900');
        win.document.write('<html><head><title>Facture IPM</title>');
        win.document.write('<style>body{font-family:Arial} table{width:100%; border-collapse:collapse} th{background:#34495e; color:white; padding:10px} td{padding:8px; border:1px solid #ddd} h1{text-align:center}</style>');
        win.document.write('</head><body>');
        win.document.write(printArea);
        win.document.write('</body></html>');
        win.document.close();
        win.print();
    }
    </script>
    """

    return HTMLResponse(CSS_FACT + f"""
    <div class='nav'>{menu}</div>
    <div class='container'>
        <div class='card'>
            <div class='header-top'>
                <h1>📊 Facturation IPM</h1>
                <button class='btn-print' onclick='imprimer()'>🖨️ Imprimer Tout</button>
            </div>

            <form method='get' action='/facturation'>
                <div class='filtres'>
                    <label>Du: </label><input type='date' name='date_debut' value='{date_debut}'>
                    <label>Au: </label><input type='date' name='date_fin' value='{date_fin}'>
                    <button type='submit'>Filtrer</button>
                </div>
            </form>

            <div class='total-box'>
                <h2>TOTAL À RÉCLAMER</h2>
                <div class='montant'>{int(total_general)} FCFA</div>
            </div>

            {details_html if details_html else "<p style='text-align:center; color:#999; padding:20px'>Aucune donnée pour cette période</p>"}

        </div>
    </div>
    {SCRIPT}
    </body></html>
    """)
from datetime import datetime
import uuid

import sqlite3 # ajoute ça en haut de main.py avec les autres imports

def enregistrer_paiement_vente(montant, methode, num_transaction):
    print(f"DEBUG DB: Tentative d'écriture: {methode} {montant} {num_transaction}")
    try:
        conn = sqlite3.connect("gestDiKo.db")
        c = conn.cursor()
        
        # ON CREE LA TABLE A CHAQUE FOIS POUR ETRE SUR
        c.execute('''CREATE TABLE IF NOT EXISTS paiements
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      methode TEXT, 
                      montant REAL, 
                      num_transaction TEXT UNIQUE, 
                      statut TEXT DEFAULT 'paye', 
                      date TEXT)''')
        
        c.execute("INSERT INTO paiements (methode, montant, num_transaction, date) VALUES (?, ?, ?)",
                  (methode, montant, num_transaction, datetime.now().isoformat()))
        conn.commit()
        print(f"DEBUG DB: ECRITURE REUSSIE !!!")
        conn.close()
    except Exception as e:
        print(f"DEBUG DB: ERREUR FATALE: {e}")
@app.post("/valider_vente")
async def valider_vente(request: Request, current_user: dict = Depends(require_permission("utiliser_caisse"))):
    form = await request.form()
    panier = json.loads(form.get("panier_json", "[]"))
    client = form.get("client")
    mode_paiement = form.get("mode_paiement")
    num_transaction = form.get("num_transaction", "")
    total = sum(p['prix'] * p['qte'] for p in panier)

    if not panier: return RedirectResponse("/caisse", status_code=303)

    vente = {
        "id": str(uuid.uuid4())[:8].upper(),
        "date": datetime.now().isoformat(),
        "client": client,
        "caissier": current_user["username"],
        "panier": panier,
        "total": total,
        "mode_paiement": mode_paiement,
        "num_transaction": num_transaction if mode_paiement in ["OM","Wave"] else "",
        "produits_resume": ", ".join([f"{p['qte']}x {p['nom']}" for p in panier]),
        "statut": "validée"
    }

    ventes = lire(F_VENTES)
    ventes.append(vente)
    ecrire(F_VENTES, ventes)

    # DEBUG + ENREGISTREMENT
    print(f"DEBUG: mode={mode_paiement}, num={num_transaction}, total={total}")
    if mode_paiement in ["OM","Wave"] and num_transaction.strip() != "":
        print("DEBUG: On entre dans le IF, on enregistre")
        enregistrer_paiement_vente(total, mode_paiement, num_transaction)
    else:
        print("DEBUG: On n'entre PAS dans le IF")

    return RedirectResponse(f"/facture/{vente['id']}", status_code=303)
@app.get("/ticket_caisse/{id_vente}")
async def ticket_caisse(id_vente: str, current_user: dict = Depends(require_permission("voir_caisse"))):
    if isinstance(current_user, RedirectResponse): 
        return current_user

    ventes = lire(F_VENTES)
    vente = next((v for v in ventes if str(v.get('id')) == str(id_vente)), None)
    
    if not vente:
        return HTMLResponse("<h1>Ticket introuvable</h1>")

    lignes = vente.get('panier', vente.get('lignes', []))
    
    # 1. ON CALCULE TOUJOURS LE TOTAL A PARTIR DES LIGNES
    total_calcule = 0
    for v in lignes:
        qte = int(v.get('qte', 1))
        prix = int(v.get('prix', v.get('prix_unitaire', 0)))
        total_ligne = int(v.get('total', prix * qte))
        total_calcule += total_ligne
    
    total = total_calcule
    
    lignes_html = ""
    for v in lignes:
        nom = v.get('nom', v.get('produit', 'Produit'))
        qte = int(v.get('qte', 1))
        prix = int(v.get('prix', v.get('prix_unitaire', 0)))
        total_ligne = int(v.get('total', prix * qte))
        lignes_html += f"<tr><td>{nom}</td><td style='text-align:center'>{qte} x {prix}F</td><td style='text-align:right'>{total_ligne}F</td></tr>"

    # 2. IPM - MODIFIE CE BLOC
    part_ipm = int(vente.get('part_ipm', 0))
    part_empl = int(vente.get('part_empl', part_ipm)) # Si tu as part_empl
    part_client = int(vente.get('part_client', 0))
    taux_ipm = int(vente.get('ipm_taux', 0))

    detail_ipm = ""
    if taux_ipm > 0 and (part_client > 0 or part_empl > 0):
        detail_ipm = f"""
        <div class='ligne'></div>
        <b>DETAIL PRISE EN CHARGE IPM {taux_ipm}%</b><br>
        Part Client: {part_client} FCFA<br>
        Part Employeur/IPM: {part_empl} FCFA<br>
        """

    # 3. CSS
    ticket_css = "<style>body{font-family:'Courier New'; width:80mm; margin:0 auto; padding:4px; font-size:11px}.center{text-align:center}.ligne{border-top:1px dashed #000; margin:4px 0}table{width:100%} td,th{text-align:left; padding:1px 0} .total{font-weight:bold; font-size:14px} @media print { body{width:80mm} button{display:none} }</style>"
    
    html = f"""
    {ticket_css}
    <div class='center'><h2 style='margin:2px; font-size:14px'>DIKOLO GESTION</h2>Rufisque, Dakar<br>Tel: 77 123 45 67</div>
    <div class='ligne'></div>
    Date: {vente.get('date_heure', vente.get('date',''))[:19]}<br>
    Ticket N°: {vente.get('reference', id_vente)}<br>
    Client: {vente.get('client', 'Anonyme')}<br>
    Caissier: {vente.get('caissier', 'N/A')}<br>
    Paiement: {vente.get('paiement', vente.get('mode_paiement', 'Cash'))}
    <div class='ligne'></div>
    <table>
        <thead><tr><th style='width:50%'>Article</th><th style='width:20%'>Qte</th><th style='width:30%; text-align:right'>Total</th></tr></thead>
        <tbody>{lignes_html}</tbody>
    </table>
    <div class='ligne'></div>
    Sous-Total: {total} FCFA<br>
    {detail_ipm}
    <div class='ligne'></div>
    <div class='total'>TOTAL TTC: {total} FCFA</div>
    <div class='ligne'></div>
    <div class='center'>Merci pour votre achat!</div>
    
    <div style='margin-top:10px; display:flex; gap:5px;' class='no-print'>
        <button onclick='window.print()' style='flex:1; padding:8px; background:#28a745; color:white; border:none; border-radius:4px;'>IMPRIMER TICKET</button>
        <button onclick="window.location.href='/caisse'" style='flex:1; padding:8px; background:#007bff; color:white; border:none; border-radius:4px;'>RETOUR CAISSE</button>
        <button onclick="if(confirm('Annuler cette vente ?')) window.location.href='/annuler_vente/{id_vente}'" style='flex:1; padding:8px; background:#dc3545; color:white; border:none; border-radius:4px;'>ANNULER</button>
    </div>
    """
    return HTMLResponse(html)
@app.get("/annuler_vente/{id_vente}")
async def annuler_vente(id_vente: str, current_user: dict = Depends(require_permission("annuler_vente"))):
    ventes = [v for v in lire(F_VENTES) if isinstance(v, dict) and str(v.get('id')) != str(id_vente)]
    ecrire(F_VENTES, ventes)
    return RedirectResponse(url="/caisse", status_code=303)
@app.get("/liste_achats") # <-- LA PROCHAINE ROUTE COMMENCE ICI
async def liste_achats(current_user: dict = Depends(require_permission("voir_achat"))):
    if isinstance(current_user, RedirectResponse): return current_user
    achats = lire(F_ACHATS); lignes = ""
    for a in achats:
        total = sum(l.get('qte',0)*l.get('prix',0) for l in a.get('lignes',[]))
        lignes += f"<tr><td>{a.get('num_bl','')}</td><td>{a.get('fournisseur','')}</td><td>{a.get('date','')}</td><td>{total} FCFA</td></tr>"
    if lignes == "": lignes = "<tr><td colspan=4>Aucun achat</td></tr>"
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Liste des Achats BL</h1><table><tr><th>N° BL</th><th>Fournisseur</th><th>Date</th><th>Total</th></tr>{lignes}</table></div></div>")

@app.get("/produits")
async def page_produits(request: Request, q: str = "", page: int = 1, current_user: dict = Depends(require_permission("voir_produits"))):
    if isinstance(current_user, RedirectResponse): return current_user
    
    produits = lire(F_PRODUITS)
    rayons = lire(F_RAYONS) # charge rayons
    etageres = lire(F_ETAGERES) # charge etageres
    
    # 1. RECHERCHE
    if q:
        produits = [p for p in produits if q.lower() in p['nom'].lower()]
    
    # 2. PAGINATION
    par_page = 20
    total = len(produits)
    pages = (total // par_page) + (1 if total % par_page > 0 else 0)
    start = (page - 1) * par_page
    produits_page = produits[start:start + par_page]
    
    # 3. TABLEAU AVEC RAYON + ETAGERE
    lignes = ""
    for i,p in enumerate(produits_page, start=start):
        stock = p.get('stock', 0)
        pa = p.get('prix_achat', p.get('prix', 0)) 
        rayon_nom = next((r['nom'] for r in rayons if r['id'] == p.get('rayon_id')), '-') # <-- NOUVEAU
        etagere_nom = next((e['nom'] for e in etageres if e['id'] == p.get('etagere_id')), '-') # <-- NOUVEAU
        alerte = "style='background:#f8d7da; color:#721c24; font-weight:bold;'" if stock < p.get('stock_min',5) else ""
        lignes += f"<tr {alerte}><td>{p['nom']}</td><td>{pa} FCFA</td><td>{stock}</td><td>{rayon_nom}</td><td>{etagere_nom}</td><td><a href='/produits/modifier/{i}'>Modifier</a></td></tr>"
    
    if lignes == "": lignes = f"<tr><td colspan=6>Aucun produit. <a href='/produits/ajouter'>Ajouter le premier</a></td></tr>" # colspan 6
    
    menu = build_menu(current_user)
    msg = request.query_params.get('msg', '')
    
    # 4. BOUTONS + BARRE RECHERCHE + PAGINATION
    pagination = ""
    for i in range(1, pages + 1):
        active = "style='font-weight:bold; background:#007bff; color:white;'" if i == page else ""
        pagination += f"<a href='/produits?q={q}&page={i}' {active} style='padding:5px 10px; border:1px solid #ccc; margin:2px;'>{i}</a>"

    boutons = f"""
    <div style='margin-bottom:15px; display:flex; gap:10px; flex-wrap:wrap;'>
        <a class='success' href='/produits/ajouter'>+ Ajouter Produit</a>
        <a class='info' href='/produits/import'>Importer CSV/Excel</a>
        <a class='warning' href='/model_produits.csv'>Telecharger Modele</a>
        <a style='background:#8e44ad; color:white; padding:8px 12px; border-radius:4px; text-decoration:none' href='/rayons/ajouter'>+ Ajouter Rayon</a> 
        <a style='background:#8e44ad; color:white; padding:8px 12px; border-radius:4px; text-decoration:none' href='/etageres/ajouter'>+ Ajouter Etagere</a> 
    </div>
    <form method='get' action='/produits' style='margin-bottom:15px;'>
        <input type='text' name='q' placeholder='Recher produit...' value='{q}' style='padding:8px; width:300px;'>
        <button>Recher</button>
    </form>
    {f"<div style='background:#d4edda; color:#155724; padding:10px; border-radius:5px; margin-bottom:10px;'>{msg}</div>" if msg else ""}
    """
    
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Produits ({total})</h1>{boutons}<table><tr><th>Nom</th><th>P.Achat</th><th>Stock</th><th>Rayon</th><th>Etagere</th><th>Action</th></tr>{lignes}</table><div style='margin-top:15px;'>{pagination}</div></div></div>")

@app.get("/produits/ajouter")
async def ajouter_produit_get(current_user: dict = Depends(require_permission("voir_produits"))):
    if isinstance(current_user, RedirectResponse): return current_user
    menu = build_menu(current_user)
    rayons = lire(F_RAYONS)
    etageres = lire(F_ETAGERES)
    options_rayon = "".join([f"<option value='{r['id']}'>{r['nom']}</option>" for r in rayons])
    options_etagere = "".join([f"<option value='{e['id']}'>{e['nom']}</option>" for e in etageres])
    
    return HTMLResponse(CSS + f"""<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'>
    <h1>Ajouter Produit</h1>
    <form method='post' action='/produits/ajouter' style='display:flex;flex-direction:column;gap:15px'>
        <input name='nom' placeholder='Nom du produit' required>
        
        <select name='rayon_id'><option value=''>-- Rayon --</option>{options_rayon}</select>
        
        <select name='etagere_id'><option value=''>-- Etagere --</option>{options_etagere}</select>
        
        <input name='prix_achat' type='number' step='0.01' placeholder='Prix Achat FCFA' required>
        
        <input name='prix_vente' type='number' step='0.01' placeholder='Prix Vente FCFA'>
        
        <label><b>Stock Initial</b></label>
        <input name='stock' type='number' placeholder='Ex: 0' value='0'>
        
        <label><b>Stock Minimum Alerte</b></label>
        <input name='stock_min' type='number' placeholder='Ex: 5' value='5'>
        
        <label><b>Date de péremption DLC</b></label>
        <input name='dlc' type='date'>
        
        <button style='padding:12px;background:#3498db;color:white;border:none;border-radius:5px'>Enregistrer</button>
    </form></div></div>""")
@app.post("/produits/ajouter")
async def ajouter_produit_post(request: Request, current_user: dict = Depends(require_permission("ajouter_produit"))):
    if isinstance(current_user, RedirectResponse): return current_user
    form = await request.form()
    produits = lire(F_PRODUITS)

    def to_float(x):
        try: return float(x)
        except: return 0.0
    def to_int(x):
        try: return int(x)
        except: return 0

    nom = form.get('nom').strip()
    nom_lower = nom.lower() # pour comparer sans majuscule

    # CONVERSION DLC 310826 -> 31/08/26
    dlc_brut = form.get('dlc','').strip()
    dlc_formatte = ""
    if len(dlc_brut) == 6 and dlc_brut.isdigit():
        dlc_formatte = f"{dlc_brut[0:2]}/{dlc_brut[2:4]}/{dlc_brut[4:6]}"

    # VERIF SI PRODUIT EXISTE DEJA
    produit_existant = next((p for p in produits if p['nom'].lower() == nom_lower), None)

    if produit_existant:
        # SI EXISTE: on additionne le stock
        produit_existant['stock'] += to_int(form.get('stock'))
        # on met à jour le prix si différent
        produit_existant['prix_achat'] = to_float(form.get('prix_achat'))
        produit_existant['prix_vente'] = to_float(form.get('prix_vente'))
        produit_existant['dlc'] = dlc_formatte or produit_existant.get('dlc','')
    else:
        # SI NOUVEAU: on crée
        new_id = max([p.get('id',0) for p in produits], default=-1) + 1
        produits.append({
            "id": new_id,
            "nom": nom,
            "prix_achat": to_float(form.get('prix_achat')),
            "prix_vente": to_float(form.get('prix_vente')),
            "stock": to_int(form.get('stock')),
            "stock_min": to_int(form.get('stock_min')),
            "dlc": dlc_formatte,
            "rayon_id": to_int(form.get('rayon_id')) if form.get('rayon_id') else None,
            "etagere_id": to_int(form.get('etagere_id')) if form.get('etagere_id') else None
        })

    sauver(F_PRODUITS, produits)
    return RedirectResponse(url="/produits", status_code=303)
@app.get("/produits/modifier/{id_prod}")
async def modifier_produit_get(id_prod: int, current_user: dict = Depends(require_permission("voir_produits"))):
    if isinstance(current_user, RedirectResponse): return current_user
    produits = lire(F_PRODUITS)
    rayons = lire(F_RAYONS)
    etageres = lire(F_ETAGERES)
    
    if id_prod >= len(produits): return HTMLResponse("Produit introuvable")
    p = produits[id_prod]
    menu = build_menu(current_user)
    
    options_rayon = "".join([f"<option value='{r['id']}' {'selected' if r['id']==p.get('rayon_id') else ''}>{r['nom']}</option>" for r in rayons])
    options_etagere = "".join([f"<option value='{e['id']}' {'selected' if e['id']==p.get('etagere_id') else ''}>{e['nom']}</option>" for e in etageres])
    
    return HTMLResponse(CSS + f"""<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'>
    <h1>Modifier {p['nom']}</h1>
    <form method='post' action='/produits/modifier/{id_prod}' style='display:flex;flex-direction:column;gap:12px'>
        
        <label><b>Nom du Produit</b></label>
        <input name='nom' value='{p['nom']}' placeholder='Ex: Amoxicilline 500mg' required>
        
        <label><b>Rayon</b></label>
        <select name='rayon_id'><option value=''>-- Choisir Rayon --</option>{options_rayon}</select>
        
        <label><b>Etagere</b></label>
        <select name='etagere_id'><option value=''>-- Choisir Etagere --</option>{options_etagere}</select>
        
        <label><b>Prix d'Achat FCFA</b></label>
        <input name='prix_achat' type='number' step='0.01' value='{p.get('prix_achat', p.get('prix',0))}' placeholder='Ex: 400' required>
        
        <label><b>Prix de Vente FCFA</b></label>
        <input name='prix_vente' type='number' step='0.01' value='{p.get('prix_vente',0)}' placeholder='Ex: 450'>
        
        <label><b>Stock Initial</b></label>
        <input name='stock' type='number' value='{p['stock']}' placeholder='Quantité en stock' required>
        
        <label><b>Stock Minimum Alerte</b></label>
        <input name='stock_min' type='number' value='{p.get('stock_min',5)}' placeholder='Alerte si stock < à'>
        
        <label><b>Date de Péremption DLC</b></label>
        <input name='dlc' type='text' value='{p.get('dlc','')}' placeholder='Ex: 310826 pour 31/08/26' maxlength='6'>
        
        <div style='display:flex;gap:10px;margin-top:10px'>
            <button style='padding:12px;background:#2ecc71;color:white;border:none;border-radius:5px;flex:1'>Enregistrer</button>
            <a href='/produits/supprimer/{id_prod}' style='padding:12px;background:#e74c3c;color:white;text-decoration:none;border-radius:5px;text-align:center;flex:1' onclick="return confirm('Supprimer?')">Supprimer</a>
        </div>
    </form></div></div>""")

@app.post("/produits/modifier/{id_prod}")
async def modifier_produit_post(id_prod: int, request: Request, current_user: dict = Depends(require_permission("voir_produits"))):
    if isinstance(current_user, RedirectResponse): return current_user
    form = await request.form()
    produits = lire(F_PRODUITS)

    def to_float(x): 
        try: return float(x) 
        except: return 0.0
    def to_int(x): 
        try: return int(x) 
        except: return 0

    # CONVERSION DLC 310826 -> 31/08/26
    dlc_brut = form.get('dlc','').strip()
    dlc_formatte = produits[id_prod].get('dlc','') # <-- CORRIGE ICI
    if len(dlc_brut) == 6 and dlc_brut.isdigit():
        dlc_formatte = f"{dlc_brut[0:2]}/{dlc_brut[2:4]}/{dlc_brut[4:6]}"
    
    produits[id_prod] = {
        "id": produits[id_prod].get('id', id_prod),
        "nom": form.get('nom'),
        "prix_achat": to_float(form.get('prix_achat')),
        "prix_vente": to_float(form.get('prix_vente')),
        "stock": to_int(form.get('stock')),
        "stock_min": to_int(form.get('stock_min')),
        "dlc": dlc_formatte,
        "rayon_id": to_int(form.get('rayon_id')) if form.get('rayon_id') else None,
        "etagere_id": to_int(form.get('etagere_id')) if form.get('etagere_id') else None
    }
    sauver(F_PRODUITS, produits)
    return RedirectResponse(url="/produits", status_code=303)
@app.get("/produits/import")
async def import_produits_get(current_user: dict = Depends(require_permission("voir_produits"))):
    if isinstance(current_user, RedirectResponse): return current_user
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"""
    <div class='nav'>{menu}</div>
    <div style='padding:20px'>
        <div class='card'>
            <h1>Importer Produits</h1>
            <p><b>Colonnes obligatoires:</b> nom, prix_achat</p>
            <p><b>Colonnes optionnelles:</b> prix_vente, stock, stock_min, dlc</p>
            <p><b>Nouveau:</b> rayon, etagere -> Ecris le nom exact du rayon/etagere</p>
            <a href='/model_produits.csv'>Télécharger modèle CSV</a><br><br>
            <form method='post' action='/produits/import' enctype='multipart/form-data'>
                <input type='file' name='fichier' accept='.csv,.xlsx,.xls' required><br><br>
                <button>Importer</button>
            </form>
        </div>
    </div>
    """)
@app.get("/produits/supprimer/{id_prod}")
async def supprimer_produit(id_prod: int, current_user: dict = Depends(require_permission("supprimer_produit"))):
    if isinstance(current_user, RedirectResponse): return current_user
    produits = lire(F_PRODUITS)
    
    if id_prod >= len(produits): 
        return HTMLResponse("Produit introuvable")
    
    nom_supprime = produits[id_prod]['nom']
    produits.pop(id_prod) # supprime par index
    sauver(F_PRODUITS, produits)
    
    return RedirectResponse(url="/produits?msg=Produit " + nom_supprime + " supprimé", status_code=303)
@app.get("/produits/liste")
async def liste_produits(q: str = "", page: int = 1, current_user: dict = Depends(require_permission("voir_produits"))):
    produits = lire(F_PRODUITS)
    rayons = {r['id']: r['nom'] for r in lire(F_RAYONS)}
    
    # 1. RECHERCHE
    if q:
        q = q.lower()
        produits = [p for p in produits if q in p['nom'].lower()]
    
    # 2. PAGINATION PAR 6
    par_page = 6
    total = len(produits)
    pages = (total + par_page - 1) // par_page
    debut = (page - 1) * par_page
    fin = debut + par_page
    produits_page = produits[debut:fin]
    
    menu = build_menu(current_user)
    
    lignes = ""
    for i, p in enumerate(produits_page):
        rayon_nom = rayons.get(p.get('rayon_id'), '-')
        lignes += f"<tr><td>{p['nom']}</td><td>{rayon_nom}</td><td>{p['stock']}</td><td>{p['prix_vente']} FCFA</td></tr>"
    
    # Boutons pagination
    boutons = ""
    for i in range(1, pages + 1):
        style = "background:#2ecc71;color:white" if i == page else ""
        boutons += f"<a href='/produits/liste?q={q}&page={i}' style='padding:8px 12px;margin:2px;border:1px solid #ccc;border-radius:4px;text-decoration:none;{style}'>{i}</a>"
    
    return HTMLResponse(CSS + f"""<div class='nav'>{menu}</div><div style='padding:20px'>
    <div class='card'>
        <h1>Produits - Page {page}/{pages}</h1>
        <form method='get' action='/produits/liste' style='margin-bottom:15px;display:flex;gap:10px'>
            <input name='q' value='{q}' placeholder='Rechercher un produit...' style='padding:10px;flex:1'>
            <button style='padding:10px 20px'>Rechercher</button>
        </form>
        <table class='table'><tr><th>Nom</th><th>Rayon</th><th>Stock</th><th>Prix</th></tr>{lignes}</table>
        <div style='margin-top:15px'>{boutons}</div>
    </div></div>""")
@app.post("/produits/import")
async def import_produits_post(fichier: UploadFile = File(...), current_user: dict = Depends(require_permission("voir_produits"))):
    if isinstance(current_user, RedirectResponse): return current_user
    produits = lire(F_PRODUITS)
    rayons = lire(F_RAYONS) # <-- CHARGER
    etageres = lire(F_ETAGERES) # <-- CHARGER
    contenu = await fichier.read()

    if fichier.filename.endswith('.csv'):
        df = pd.read_csv(io.StringIO(contenu.decode('utf-8')))
    else:
        df = pd.read_excel(io.BytesIO(contenu))

    cree = 0
    maj = 0
    erreurs = []

    for index, row in df.iterrows():
        nom = str(row.get('nom') or '').strip()
        pa = float(row.get('prix_achat') or 0)
        pv = float(row.get('prix_vente') or 0) 
        stock = int(row.get('stock') or 0) 
        stock_min = int(row.get('stock_min') or 5)
        dlc = str(row.get('dlc') or '')
        nom_rayon = str(row.get('rayon') or '').strip() # <-- NOUVEAU
        nom_etagere = str(row.get('etagere') or '').strip() # <-- NOUVEAU
        
        if nom == 'nan' or nom == '' or pa <= 0:
            continue
        
        # Trouver l'ID du rayon par nom
        rayon_id = None
        if nom_rayon:
            r = next((x for x in rayons if x['nom'].lower() == nom_rayon.lower()), None)
            if r: rayon_id = r['id']
            else: erreurs.append(f"Ligne {index+2}: Rayon '{nom_rayon}' introuvable")
        
        # Trouver l'ID de l'etagere par nom
        etagere_id = None
        if nom_etagere:
            e = next((x for x in etageres if x['nom'].lower() == nom_etagere.lower()), None)
            if e: etagere_id = e['id']
            else: erreurs.append(f"Ligne {index+2}: Etagere '{nom_etagere}' introuvable")
        
        # Trouver ou créer le produit
        prod = next((p for p in produits if p['nom'].lower() == nom.lower()), None)
        if prod: # Mise à jour
           prod['prix_achat'] = pa
           prod['prix_vente'] = pv
           prod['stock_min'] = stock_min
           prod['dlc'] = dlc
           prod['rayon_id'] = rayon_id # <-- MAJ
           prod['etagere_id'] = etagere_id # <-- MAJ
           maj += 1
        else: # Création
           produits.append({
               "nom": nom, 
               "prix_achat": pa, 
               "prix_vente": pv,
               "stock": stock,
               "stock_min": stock_min,
               "dlc": dlc,
               "rayon_id": rayon_id, # <-- AJOUT
               "etagere_id": etagere_id # <-- AJOUT
           })
           cree += 1
    
    sauver(F_PRODUITS, produits)
    msg = f"{cree} crees, {maj} maj"
    if erreurs: msg += f" | Erreurs: {'; '.join(erreurs[:3])}" # montre max 3 erreurs
    return RedirectResponse(url=f"/produits?msg={msg}", status_code=303)
@app.get("/model_produits.csv")
async def model_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['nom', 'prix_achat', 'prix_vente', 'stock', 'stock_min', 'dlc', 'rayon', 'etagere']) # <-- AJOUT
    writer.writerow(['Coca 33cl', '400', '500', '100', '10', '2026-12-31', 'Boissons', 'E1'])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=model_produits.csv"})
@app.get("/achat")
async def page_achat(current_user: dict = Depends(require_permission("voir_achat"))):
    if isinstance(current_user, RedirectResponse): return current_user
    produits = lire(F_PRODUITS)
    options = "".join([f"<option value='{i}'>{p['nom']}</option>" for i,p in enumerate(produits)])
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Achat BL</h1><form method='post' action='/achat'><input name='num_bl' placeholder='N° BL' required><br><br><input name='fournisseur' placeholder='Fournisseur' required><br><br><input name='date' type='date' required><br><br><h3>Ligne 1</h3><select name='prod_0'>{options}</select> Qte:<input name='qte_0' type='number' style='width:80px'> Prix:<input name='prix_0' type='number' style='width:100px'><br><br><button>Enregistrer BL</button></form></div></div>")

@app.post("/achat")
async def save_achat(request: Request, current_user: dict = Depends(require_permission("voir_achat"))):
    if isinstance(current_user, RedirectResponse): return current_user
    form = await request.form(); achats = lire(F_ACHATS); produits = lire(F_PRODUITS)
    lignes = []
    i = 0
    while f'prod_{i}' in form:
        pid = int(form.get(f'prod_{i}')); qte = int(form.get(f'qte_{i}')); prix = int(form.get(f'prix_{i}'))
        lignes.append({"prod_id": pid, "nom": produits[pid]['nom'], "qte": qte, "prix": prix})
        produits[pid]['stock'] += qte
        i += 1
    achats.append({"num_bl": form.get('num_bl'), "fournisseur": form.get('fournisseur'), "date": form.get('date'), "lignes": lignes})
    sauver(F_ACHATS, achats); sauver(F_PRODUITS, produits)
    return RedirectResponse(url="/liste_achats", status_code=303)
import html
import json

@app.get("/vendre")
async def page_vendre(request: Request, current_user: dict = Depends(require_permission("vendre"))):
    if isinstance(current_user, RedirectResponse): return current_user

    produits = lire(F_PRODUITS)
    paiements = lire(F_PAIEMENT) # PAS de IPM

    # Ajouter OM et Wave si pas là
    noms_paiement = [p['nom'].lower() for p in paiements]
    if 'orange money' not in noms_paiement: paiements.append({'nom':'Orange Money'})
    if 'wave' not in noms_paiement: paiements.append({'nom':'Wave'})

    # datalist avec tout: nom + prix + stock + code
    datalist_html = "".join([
        f"<option value='{html.escape(p.get('nom',''))}' data-id='{i}' data-prix='{int(p.get('prix_vente', p.get('prix_achat',0)*1.3))}' data-stock='{p.get('stock',0)}' data-code='{html.escape(p.get('code_barre',''))}'></option>"
        for i, p in enumerate(produits)
    ])

    paiement_options = "".join([f"<option value='{html.escape(p.get('nom',''))}'>{html.escape(p.get('nom',''))}</option>" for p in paiements])

    html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Vente Simple</title>
    {CSS_GLOBAL}
    <style>
   body{{padding:0;margin:0;background:#f5f7fa}}
.caisse-wrap{{display:grid;grid-template-columns:2fr 1fr;gap:15px;padding:15px}}
.scan-bar{{background:#fff3cd;padding:15px;border-radius:8px;margin-bottom:15px}}
.scan-bar label{{font-weight:bold;color:#856404;display:block;margin-bottom:5px}}
.scan-bar input{{width:100%;padding:12px;font-size:16px;border:2px solid #ffc107;border-radius:5px}}
.ajout-produit{{background:white;padding:15px;border-radius:8px;margin-bottom:15px}}
.ajout-produit h3{{color:#27ae60;margin-top:0}}
.produit-table{{width:100%;border-collapse:collapse}}
.produit-table th{{background:#2c3e50;color:white;padding:12px;text-align:left;font-size:14px}}
.produit-table td{{padding:10px;border-bottom:1px solid #eee}}
.produit-table input{{width:100%;padding:8px;border:1px solid #ddd;border-radius:4px}}
.btn-ajout{{background:#27ae60;color:white;border:none;padding:10px 15px;border-radius:4px;cursor:pointer;font-weight:bold}}
.panier-table{{width:100%;background:white;border-radius:8px;overflow:hidden}}
.panier-table th{{background:#34495e;color:white;padding:10px;text-align:left}}
.panier-table td{{padding:8px;border-bottom:1px solid #eee}}
.col-droite.card{{background:white; padding:15px; border-radius:10px; margin-bottom:15px}}
.commande-header{{background:#2c3e50;color:white;padding:12px;text-align:center;font-weight:bold;border-radius:5px 5px 0 0}}
.total-box{{background:#27ae60;color:white;padding:15px;text-align:center;font-size:20px;font-weight:bold}}
.btn-vide{{background:#e74c3c;color:white;border:none;padding:10px;width:100%;border-radius:5px;cursor:pointer;margin-bottom:10px}}
#btn_om_wave{{display:none}}
.mobile-box{{display:none;background:#eaf2ff;padding:10px;border-radius:5px}}
    </style></head>
    <body>
    {build_menu(current_user, 'vendre')}
    <div class='container'>{"<div style='background:#27ae60;color:white;padding:10px;text-align:center'>✅ Vente enregistrée!</div>" if "success=1" in str(request.url) else ""}
    <form method='post' action='/valide_vente' id='form_caisse'>
    <div class='caisse-wrap'>

    <div class='col-gauche'>
        <div class='scan-bar'>
            <label>📷 SCAN CODE BARRE</label>
            <input id='scan' placeholder='Scannez ici' autofocus>
        </div>

        <div class='ajout-produit'>
            <h3>+ Ajouter un produit</h3>
            <table class='produit-table'>
                <thead>
                    <tr>
                        <th style="width:40%">Produit</th>
                        <th style="width:10%">Qte</th>
                        <th style="width:15%">Prix U</th>
                        <th style="width:10%">Stock</th>
                        <th style="width:15%">Total</th>
                        <th style="width:10%">+</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <input list="liste_produits" id="input_produit" placeholder="Taper ou Choisir">
                            <datalist id="liste_produits">{datalist_html}</datalist>
                        </td>
                        <td><input type="number" id="input_qte" value="1" min="1"></td>
                        <td><span id="input_prix">0</span> FCFA</td>
                        <td><span id="input_stock">0</span></td>
                        <td><span id="input_total">0</span> FCFA</td>
                        <td><button type="button" onclick="ajouterLigne()" class="btn-ajout">+</button></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <h3>Panier</h3>
        <table class='panier-table'>
            <thead><tr><th>Produit</th><th>Qte</th><th>Prix</th><th>Total</th><th>X</th></tr></thead>
            <tbody id="panier-body"></tbody>
        </table>
    </div>

    <div class='col-droite'>
        <button type='button' class='btn-vide' onclick='viderPanier()'>🗑️ VIDER PANIER</button>
        <div class='commande-header'>COMMANDE</div>
        <div class='total-box'>Total: <span id="total-general">0</span> FCFA</div>
        <input type="hidden" name="panier_data" id="panier_data">

        <div class='card'>
         <div class='form-group'><label>Client</label><input name='client' value='Client Anonyme'></div>
            <div class='form-group'><label>Remise FCFA</label><input name='remise' id='remise' type='number' value='0' onchange='majCaisse()'></div>
            <div class='form-group'><label>Mode Paiement</label><select name='mode_paiement' id='mode_paiement' onchange='toggleMobile()'>{paiement_options}</select></div>
            <div class='form-group' id='bloc_transaction' style='display:none;'><label>N° Transaction</label><input type='text' name='num_transaction' id='num_transaction' placeholder='Ex: 771234567'></div>
            <div class='form-group'><label><input type='checkbox' id='tva' name='tva' value='18' onchange='majCaisse()'> TVA 18%</label></div>

            <div id='mobile-box' class='mobile-box'>
                <div style="font-weight:bold;margin-bottom:5px">Paiement Mobile</div>
                <div class='form-group'><label>Numéro Client</label><input name='num_client' id='num_client'></div>
                <div class='form-group'><label>Réf Transaction</label><input id='ref_trans_input' placeholder='Sera rempli après paiement'></div>
            </div>
        </div>

        <div class='card' style='background:#3498db;color:white;text-align:center'>
            TOTAL A PAYER: <span id='total-client'>0</span> FCFA
        </div>

        <div class='form-group'><label>Montant Reçu</label><input name='montant_recu' id='montant_recu' type='number' oninput='calcMonnaie()'></div>
        <div id='monnaie-box' style='display:none;background:#f1c40f;padding:10px;text-align:center;font-weight:bold;border-radius:5px'>Monnaie: <span id='monnaie'>0</span> FCFA</div>

        <button id="btn_valider" class="btn" style="width:100%;background:#27ae60;font-size:16px;padding:12px">VALIDER VENTE</button>

        <div id="btn_om_wave" style="margin-top:10px; padding:15px; border-top:2px solid #0044CC; text-align:center; background:#f5f5f5;">
            <div style="font-size:20px; font-weight:bold; color:#0044CC; margin-bottom:10px;">Total à payer: <span id="total_facture">0</span> F</div>
            <button type="button" onclick="payerV2('OM')" style="background:orange; color:white; padding:12px 20px; margin:5px; border:none; border-radius:8px; font-weight:bold;">Payer OM</button>
            <button type="button" onclick="payerV2('WAVE')" style="background:#0044CC; color:white; padding:12px 20px; margin:5px; border:none; border-radius:8px; font-weight:bold;">Payer Wave</button>
        </div>

        <div id="zone_pay_v2" style="display:none; background:#eaf2ff; padding:15px; margin-top:15px; border:2px dashed #0044CC; border-radius:10px; text-align:center;">
            <h3>Scanner pour payer <span id="mode_pay_v2"></span> : <span id="montant_pay_v2">0</span> F</h3>
            <img id="img_pay_v2" src="" width="110" height="110" alt="QR Code">
            <br><br>
            <input type="text" id="ref_pay_v2" placeholder="Coller N° Transaction ici" style="padding:8px; width:70%">
            <br><br>
            <button type="button" onclick="validerPayV2()" style="background:green; color:white; padding:10px;">Valider</button>
            <button type="button" onclick="annulerPayV2()" style="background:red; color:white; padding:10px;">Annuler</button>
        </div>
    </div>
    </div></form></div>

<script>
let panier = [];
let produits_globaux = {json.dumps(produits)};

document.getElementById('input_produit').addEventListener('input', function(){{
    let val = this.value;
    let option = document.querySelector(`#liste_produits option[value="${{val}}"]`);
    if(option){{
        document.getElementById('input_prix').innerText = option.dataset.prix;
        document.getElementById('input_stock').innerText = option.dataset.stock;
        majLigneTotal();
    }}
}});

document.getElementById('input_qte').addEventListener('input', majLigneTotal);

function majLigneTotal(){{
    let prix = parseFloat(document.getElementById('input_prix').innerText) || 0;
    let qte = parseInt(document.getElementById('input_qte').value) || 0;
    document.getElementById('input_total').innerText = (prix * qte).toFixed(0);
}}

function ajouterLigne(){{
    let nom = document.getElementById('input_produit').value;
    let qte = parseInt(document.getElementById('input_qte').value);
    let option = document.querySelector(`#liste_produits option[value="${{nom}}"]`);
    if(!option){{ alert("Produit introuvable"); return; }}
    let prix = parseFloat(option.dataset.prix);
    let exist = panier.find(x=>x.nom==nom);
    if(exist){{ exist.qte += qte; }} else {{ panier.push({{nom: nom, prix: prix, qte: qte}}); }}
    document.getElementById('input_produit').value = '';
    document.getElementById('input_qte').value = 1;
    document.getElementById('input_prix').innerText = 0;
    document.getElementById('input_stock').innerText = 0;
    majLigneTotal(); majCaisse();
}}

document.getElementById('scan').addEventListener('keypress', function(e){{
    if(e.key === 'Enter'){{
        let code = this.value.trim();
        let option = document.querySelector(`#liste_produits option[data-code="${{code}}"]`);
        if(option){{
            document.getElementById('input_produit').value = option.value;
            document.getElementById('input_qte').value = 1;
            ajouterLigne();
        }} else {{ alert("Produit non trouvé: " + code); }}
        this.value = '';
        e.preventDefault();
    }}
}});

function majCaisse(){{
    let tbody = document.getElementById('panier-body'); tbody.innerHTML=''; let total=0;
    panier.forEach((p, i)=>{{
        let t = p.prix * p.qte; total += t;
        tbody.innerHTML += `<tr><td>${{p.nom}}</td><td><input type='number' value='${{p.qte}}' style='width:60px' onchange='changerQte(${{i}}, this.value)'></td><td>${{p.prix}} FCFA</td><td>${{t.toFixed(0)}} FCFA</td><td><button type="button" onclick='supprimerDuPanier(${{i}})'>X</button></td></tr>`
    }});
    let remise = parseFloat(document.getElementById('remise').value) || 0;
    let total_final = Math.max(0, total - remise); // PAS DE IPM ICI

    document.getElementById('total-general').innerText = total.toFixed(0);
    document.getElementById('total-client').innerText = total_final.toFixed(0);
    document.getElementById('total_facture').innerText = total_final.toFixed(0);
    document.getElementById('panier_data').value = JSON.stringify(panier);
    calcMonnaie();
}}

function changerQte(index, qte){{ panier[index].qte = parseInt(qte); if(panier[index].qte <= 0) panier.splice(index,1); majCaisse(); }}
function supprimerDuPanier(index){{ panier.splice(index,1); majCaisse(); }}
function viderPanier(){{ if(panier.length > 0 && confirm("Vider tout le panier?")){{ panier=[]; majCaisse(); }} }}
function calcMonnaie(){{ let a_payer = parseFloat(document.getElementById('total-client').innerText) || 0; let recu = parseFloat(document.getElementById('montant_recu').value) || 0; let monnaie = recu - a_payer; document.getElementById('monnaie').innerText = monnaie.toFixed(0); document.getElementById('monnaie-box').style.display = monnaie > 0? 'block' : 'none'; }}
function toggleMobile(){{ let mode = document.getElementById('mode_paiement').value.toLowerCase(); let divOM = document.getElementById('btn_om_wave'); let btnValider = document.getElementById('btn_valider'); let mobileBox = document.getElementById('mobile-box'); if(mode.includes('orange') || mode.includes('om') || mode.includes('wave')) {{ divOM.style.display = 'block'; btnValider.style.display = 'none'; mobileBox.style.display = 'block'; }} else {{ divOM.style.display = 'none'; btnValider.style.display = 'block'; mobileBox.style.display = 'none'; }} }}
toggleMobile();

function payerV2(mode){{ let total = document.getElementById('total_facture').innerText; document.getElementById('zone_pay_v2').style.display = 'block'; document.getElementById('mode_pay_v2').innerText = mode; document.getElementById('montant_pay_v2').innerText = total; document.getElementById('img_pay_v2').src = '/static/qr_' + mode + '.png?' + Date.now(); }}
function validerPayV2(){{ let ref = document.getElementById('ref_pay_v2').value; if(ref.trim() == ""){{ alert("Colle le N° Transaction"); return; }} let mode = document.getElementById('mode_pay_v2').innerText; if(mode == "OM"){{ document.getElementById('mode_paiement').value = "Orange Money"; }} if(mode == "WAVE"){{ document.getElementById('mode_paiement').value = "Wave"; }} document.getElementById('num_transaction').value = ref; document.getElementById('form_caisse').submit(); }}
function annulerPayV2(){{ document.getElementById('zone_pay_v2').style.display = 'none'; document.getElementById('ref_pay_v2').value = ''; }}

document.querySelector('select[name="mode_paiement"]').addEventListener('change', function(){{ let bloc = document.getElementById('bloc_transaction'); if(this.value == 'Orange Money' || this.value == 'Wave'){{ bloc.style.display = 'block'; bloc.querySelector('input').required = true; }} else {{ bloc.style.display = 'none'; bloc.querySelector('input').required = false; bloc.querySelector('input').value = ''; }} }});
</script>
</body></html>"""
    return HTMLResponse(html_content)
from fastapi.responses import HTMLResponse
@app.get("/facture/{vente_id}", response_class=HTMLResponse)
async def generer_facture(vente_id: str):
    ventes = lire(F_VENTES)
    vente = next((v for v in ventes if str(v.get("id","")) == str(vente_id)), None)

    if not vente: return f"<h3>Erreur</h3><p>Vente N°{vente_id} introuvable</p><a href='/historique'>Retour</a>"

    lignes_produits = "".join([f"<tr><td>{p.get('nom','')}</td><td>{p.get('qte',0)}</td><td>{p.get('prix',0)}</td><td>{p.get('prix',0)*p.get('qte',0)}</td></tr>" 
    for p in vente.get('panier',[])])
    date_propre = vente.get('date','').replace('T',' ')[:16]

    html = f"""
    <html><head><title>Facture N°{vente.get('id','')}</title>
    <style>
        body{{font-family:Arial; padding:20px; max-width:800px; margin:auto;}}
       .header{{text-align:center; border-bottom:2px solid #000;}} table{{width:100%; border-collapse:collapse; margin-top:20px;}}
        th,td{{border:1px solid #000; padding:8px;}} th{{background:#f2f2f2;}}
       .total{{text-align:right; font-weight:bold; font-size:18px;}}.actions{{margin-top:30px; text-align:center;}}
       .btn{{padding:10px 20px; border:none; border-radius:5px; margin:5px; text-decoration:none; display:inline-block;}}
       .btn-print{{background:#4CAF50; color:white;}}.btn-back{{background:#2196F3; color:white;}}
        @media print {{.no-print{{display:none;}} }}
    </style></head><body>
        <div class="header"><h2>NOM DE L'ENTREPRISE</h2><h3>FACTURE N° {vente.get('id','')}</h3><p>{date_propre}</p></div>
        <p><b>Client:</b> {vente.get('client','')}</p>
        <p><b>Caissier:</b> {vente.get('caissier','')}</p>
        <p><b>Mode Paiement:</b> {vente.get('mode_paiement','')}</p>
        <p><b>N° Transaction:</b> {vente.get('num_transaction','')}</p>
        <table><tr><th>Désignation</th><th>Qte</th><th>P.U</th><th>Total</th></tr>{lignes_produits}</table>
        <p class="total">TOTAL: {vente.get('total',0)} FCFA</p>
        <div class="actions no-print">
            <button class="btn btn-print" onclick="window.print()">🖨️ Imprimer</button>
            <a href="/historique" class="btn btn-back">⬅️ Retour Historique</a>
        </div>
        <script>window.print()</script>
    </body></html>
    """
    return html
@app.get("/users")
async def page_users(current_user: dict = Depends(require_permission("voir_users"))):
    if isinstance(current_user, RedirectResponse): return current_user
    users = lire(F_USERS); roles = lire(F_ROLES)
    lignes = ""
    for u, data in users.items():
        lignes += f"<tr><td>{u}</td><td>{data['role']}</td></tr>"
    if lignes == "": lignes = "<tr><td colspan=2>Aucun utilisateur</td></tr>"

    options_roles = "".join([f"<option value='{r}'>{r}</option>" for r in roles.keys()])

    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Gestion Utilisateurs</h1><h3>Ajouter Utilisateur</h3><form method='post' action='/users/ajouter'><input name='username' placeholder='Login' required><br><br><input name='password' type='password' placeholder='Mot de passe' required><br><br><select name='role'>{options_roles}</select><br><br><button>Ajouter</button></form><hr><h3>Liste</h3><table><tr><th>Login</th><th>Rôle</th></tr>{lignes}</table></div></div>")

@app.post("/users/ajouter")
async def ajouter_user(username: str = Form(...), password: str = Form(...), role: str = Form(...), current_user: dict = Depends(require_permission("voir_users"))):
    if isinstance(current_user, RedirectResponse): return current_user
    users = lire(F_USERS)
    if username in users:
        return RedirectResponse(url="/users?msg=User existe deja", status_code=303)
    users[username] = {"username": username, "password": password, "role": role}
    sauver(F_USERS, users)
    return RedirectResponse(url="/users", status_code=303)
@app.get("/etatcaisse")
async def etat_caisse(date: str = None, page: int = 1, current_user: dict = Depends(require_permission("voir_historique"))):
    if isinstance(current_user, RedirectResponse): return current_user
    if not date: date = datetime.now().strftime("%Y-%m-%d")
    
    ventes = lire(F_VENTES)
    depenses = lire(F_DEPENSES)
    
    ventes_jour = [v for v in ventes if date in str(v.get('date',''))]
    depenses_jour = [d for d in depenses if date in str(d.get('date',''))]
    
    total_ventes = sum([int(v.get('total',0)) for v in ventes_jour])
    total_depenses = sum([int(d.get('montant',0)) for d in depenses_jour])
    solde = total_ventes - total_depenses
    
    # Pagination simple
    per_page = 10
    start = (page-1)*per_page
    ventes_page = ventes_jour[start:start+per_page]
    
    lignes_ventes = ""
    for v in ventes_page:
        lignes_ventes += f"<tr><td>{str(v.get('date',''))[-8:-3]}</td><td>TKT{str(v.get('id',''))[:6]}</td><td>{v.get('total',0)} FCFA</td></tr>"
    if not lignes_ventes: lignes_ventes = "<tr><td colspan=3>Aucune vente</td></tr>"
    
    lignes_dep = ""
    for d in depenses_jour:
        lignes_dep += f"<tr><td>{str(d.get('date',''))[-8:-3]}</td><td>{d.get('libelle','')}</td><td>{d.get('montant',0)} FCFA</td><td><a class='danger' href='/depense/supprimer/{d.get('id','')}'>Suppr</a></td></tr>"
    if not lignes_dep: lignes_dep = "<tr><td colspan=4>Aucune dépense</td></tr>"
    
    next_page = f"<a href='/etatcaisse?date={date}&page={page+1}'>Suivant ></a>" if start+per_page < len(ventes_jour) else ""
    prev_page = f"<a href='/etatcaisse?date={date}&page={page-1}'>< Précédent</a>" if page > 1 else ""
    
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><form method='get' action='/etatcaisse'><b>Date :</b> <input type='date' name='date' value='{date}'><button>Afficher</button></form><div style='display:flex; gap:10px; margin:20px 0'><div style='background:green; color:white; padding:15px; flex:1'>Ventes<br><b>{total_ventes} FCFA</b></div><div style='background:red; color:white; padding:15px; flex:1'>Dépenses<br><b>{total_depenses} FCFA</b></div><div style='background:blue; color:white; padding:15px; flex:1'>Solde<br><b>{solde} FCFA</b></div></div><h3>Ventes</h3><table><tr><th>Heure</th><th>Ticket</th><th>Montant</th></tr>{lignes_ventes}</table><div>{prev_page} {next_page}</div><h3>Dépenses</h3><table><tr><th>Heure</th><th>Libellé</th><th>Montant</th><th>Action</th></tr>{lignes_dep}</table><h3>Ajouter dépense</h3><form method='post' action='/depense/ajouter'><input type='hidden' name='date' value='{date}'><input name='libelle' placeholder='Libellé' required><input name='montant' type='number' placeholder='Montant' required><button>Ajouter</button></form></div></div>")


@app.post("/depense/ajouter")
async def ajouter_depense(date: str = Form(...), libelle: str = Form(...), montant: int = Form(...), current_user: dict = Depends(require_permission("voir_historique"))):
    if isinstance(current_user, RedirectResponse): return current_user
    depenses = lire(F_DEPENSES)
    depenses.append({"id": str(datetime.now().timestamp()), "date": f"{date} {datetime.now().strftime('%H:%M:%S')}", "libelle": libelle, "montant": montant, "user": current_user['username']})
    sauver(F_DEPENSES, depenses)
    return RedirectResponse(url=f"/etatcaisse?date={date}", status_code=303)

@app.get("/depense/supprimer/{id_dep}")
async def suppr_depense(id_dep: str, current_user: dict = Depends(require_permission("voir_historique"))):
    if isinstance(current_user, RedirectResponse): return current_user
    depenses = lire(F_DEPENSES)
    depenses = [d for d in depenses if d.get('id') != id_dep]
    sauver(F_DEPENSES, depenses)
    return RedirectResponse(url="/etatcaisse", status_code=303)
import json


def format_dlc(val):
    """ 010226 -> 01/02/26 """
    val = str(val).strip()
    if len(val) == 6 and val.isdigit():
        return f"{val[0:2]}/{val[2:4]}/{val[4:6]}"
    return val

@app.post("/reception/save")
async def valider_reception(request: Request, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse): return current_user
    form = await request.form()
    receptions = lire("receptions.json")
    produits = lire(F_PRODUITS)
    lots = lire(F_LOTS)

    tva_active = form.get('tva') == 'on'
    panier = []

    new_noms = form.getlist('new_nom[]')
    new_qte_cdees = form.getlist('new_qte_cdee[]') # NOUVEAU
    new_qtes = form.getlist('new_qte[]')
    new_pas = form.getlist('new_pa[]')
    new_dlcs = form.getlist('new_dlc[]')
    
    for i in range(len(new_noms)):
        if new_noms[i]:
            qte = int(new_qtes[i])
            panier.append({
                "produit": new_noms[i],
                "qte_cdee": int(new_qte_cdees[i]) if new_qte_cdees[i] else 0, # NOUVEAU
                "qte": qte,
                "pa": float(new_pas[i]) if new_pas[i] else 0,
                "ptotal": qte * float(new_pas[i]) if new_pas[i] else 0, # NOUVEAU
                "lot": "",
                "dlc": format_dlc(new_dlcs[i])
            })
            # Mise à jour stock
            for p in produits:
                if p['nom'] == new_noms[i]:
                    p['stock'] += qte
                    p['prix_achat'] = float(new_pas[i]) if new_pas[i] else p['prix_achat']

    total_ht = sum(item['ptotal'] for item in panier)
    total_ttc = int(total_ht * 1.18) if tva_active else total_ht

    nouvelle_reception = {
        "n_bl": form.get('n_bl'), "n_bc": form.get('n_bc'), "fournisseur": form.get('fournisseur'),
        "date": form.get('date'), "lignes": panier, "total_ht": total_ht,
        "total_ttc": total_ttc, "tva": tva_active
    }
    receptions.append(nouvelle_reception)
    sauver(F_PRODUITS, produits)
    sauver(F_LOTS, lots)
    sauver("receptions.json", receptions)
    return RedirectResponse(url="/reception", status_code=303)
@app.get("/reception/detail/{idx}")
async def detail_reception(idx: int, request: Request, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse): return current_user

    receptions = lire("receptions.json")

    if idx < 0 or idx >= len(receptions):
        return HTMLResponse(f"{CSS}<div class='nav'>{build_menu(current_user)}</div><div style='padding:20px'><h2>BL introuvable</h2><a href='/reception/liste'>Retour</a></div>")

    reception = receptions[idx]
    menu = build_menu(current_user)

    lignes = ""
    for l in reception.get('lignes', []):
        total_ligne = int(l['qte']) * int(l['pa'])
        pa_fmt = f"{int(l['pa']):,}".replace(",", " ")
        total_fmt = f"{total_ligne:,}".replace(",", " ")
        lignes += f"""
        <tr>
            <td style='padding:10px'>{l['produit']}</td>
            <td style='text-align:center'>{l['qte']}</td>
            <td style='text-align:right'>{pa_fmt} FCFA</td>
            <td style='text-align:right'><b>{total_fmt} FCFA</b></td>
            <td style='text-align:center'>{l.get('lot','-')}</td>
            <td style='text-align:center'>{l.get('dlc','-')}</td>
        </tr>
        """

    tva_txt = "18%" if reception.get('tva') else "0%"
    total_ht_fmt = f"{int(reception.get('total_ht',0)):,}".replace(",", " ")
    total_ttc_fmt = f"{int(reception.get('total_ttc',0)):,}".replace(",", " ")

    html = f"""
    {CSS}
    <div class='nav'>{menu}</div>
    <div style='padding:20px;background:#f4f6f9;min-height:90vh'>
        <a href='/reception/liste' style='background:#6c757d;color:white;padding:8px 12px;border-radius:5px;text-decoration:none;font-size:14px'>← Retour Liste</a>

        <div style='background:white;padding:20px;border-radius:8px;margin-top:15px;box-shadow:0 2px 4px rgba(0,0,0,0.1)'>
            <h2 style='color:#333;margin-bottom:15px'>Détail BL: {reception.get('n_bl')}</h2>

            <div style='display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap:15px; margin-bottom:20px; padding:15px; background:#f8f9fa; border-radius:5px'>
                <div><b>Date:</b><br>{reception.get('date')}</div>
                <div><b>N° BC:</b><br>{reception.get('n_bc','-')}</div>
                <div><b>Fournisseur:</b><br>{reception.get('fournisseur','-')}</div>
                <div><b>TVA:</b><br>{tva_txt}</div>
            </div>

            <table width='100%' style='border-collapse:collapse'>
                <tr style='background:#2c3e50;color:white'>
                    <th style='padding:10px;text-align:left'>Produit</th>
                    <th style='padding:10px;text-align:center'>Qte</th>
                    <th style='padding:10px;text-align:right'>PA U</th>
                    <th style='padding:10px;text-align:right'>Total HT</th>
                    <th style='padding:10px;text-align:center'>Lot</th>
                    <th style='padding:10px;text-align:center'>DLC</th>
                </tr>
                {lignes}
                <tr style='background:#e9ecef; font-weight:bold'>
                    <td colspan='3' style='padding:10px;text-align:right'>TOTAL HT:</td>
                    <td style='padding:10px;text-align:right'>{total_ht_fmt} FCFA</td>
                    <td colspan='2'></td>
                </tr>
                <tr style='background:#d4edda; font-weight:bold; font-size:16px'>
                    <td colspan='3' style='padding:10px;text-align:right'>TOTAL TTC:</td>
                    <td style='padding:10px;text-align:right'>{total_ttc_fmt} FCFA</td>
                    <td colspan='2'></td>
                </tr>
            </table>
        </div>
    </div>
    """
    return HTMLResponse(html)
@app.post("/reception/ajouter")
async def ajouter_reception(request: Request):
    form = await request.form()
    # ici tu ajoutes form['nom'] dans une session/panier
    return RedirectResponse("/reception?msg=Ajoute: "+form['nom'], status_code=303)
@app.post("/valider_reception")
async def valider_reception(request: Request, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse): return current_user
    form = await request.form()
    panier = json.loads(form.get('reception', '[]'))
    produits = lire(F_PRODUITS); achats = lire(F_ACHATS); lots = lire(F_LOTS)
    tva_active = form.get('tva') == 'on'

    lignes_achat = []
    total_ht = 0
    for i, item in enumerate(panier):
        qte = int(form.get(f'qte_{i}', 0))
        lot = form.get(f'lot_{i}', '')
        dlc = form.get(f'dlc_{i}', '')
        prix_achat = int(form.get(f'prix_achat_{i}', 0))

        pid = item['id']
        produits[pid]['stock'] += qte
        produits[pid]['prix_achat'] = prix_achat # Sauvegarde le dernier PA

        total_ht += qte * prix_achat
        lots.append({"produit_id": pid, "produit_nom": produits[pid]['nom'], "qte": qte, "lot": lot, "dlc": dlc, "prix_achat": prix_achat, "date": str(datetime.now())})
        lignes_achat.append({"prod_id": pid, "nom": produits[pid]['nom'], "qte": qte, "prix": prix_achat})

    total_ttc = total_ht * 1.18 if tva_active else total_ht

    achats.append({
        "num_bl": form.get('num_bl'),
        "fournisseur": form.get('fournisseur'),
        "date": str(date.today()),
        "lignes": lignes_achat,
        "total_ht": total_ht,
        "total_ttc": total_ttc,
        "tva": tva_active
    })

    sauver(F_PRODUITS, produits); sauver(F_ACHATS, achats); sauver(F_LOTS, lots)
    return RedirectResponse(url="/liste_achats", status_code=303)

@app.post("/produit_rapide")
async def produit_rapide(nom: str = Form(...), prix: int = Form(...), prix_achat: int = Form(0), stock: int = Form(0)):
    produits = lire(F_PRODUITS)
    produits.append({"nom": nom, "prix": prix, "prix_achat": prix_achat, "stock": stock, "stock_min": 5, "dlc": ""})
    sauver(F_PRODUITS, produits)
    return JSONResponse({"status": "ok"})
    lignes_achat = []
    for i, item in enumerate(panier):
        qte = int(form.get(f'qte_{i}', 0))
        lot = form.get(f'lot_{i}', '')
        dlc = form.get(f'dlc_{i}', '')

        pid = item['id']
        produits[pid]['stock'] += qte # Augmente stock

        # Crée le lot
        lots.append({"produit_id": pid, "produit_nom": produits[pid]['nom'], "qte": qte, "lot": lot, "dlc": dlc, "date": str(datetime.now())})
        lignes_achat.append({"prod_id": pid, "nom": produits[pid]['nom'], "qte": qte, "prix": 0}) # Prix à 0 pour l'instant

    achats.append({"num_bl": form.get('num_bl'), "fournisseur": form.get('fournisseur'), "date": str(date.today()), "lignes": lignes_achat})

    sauver(F_PRODUITS, produits); sauver(F_ACHATS, achats); sauver(F_LOTS, lots)
    return RedirectResponse(url="/liste_achats", status_code=303)
from datetime import datetime

import html
import json
from datetime import datetime

@app.get("/reception")
async def page_reception(request: Request, page: int = 1, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse): return current_user

    receptions = lire("receptions.json")
    receptions.reverse() 
    produits = lire(F_PRODUITS)
    menu = build_menu(current_user)

    # PAGINATION 10 par page
    par_page = 10
    total_bl = len(receptions)
    pages = (total_bl + par_page - 1) // par_page if total_bl > 0 else 1
    page = max(1, min(page, pages))
    debut = (page - 1) * par_page
    receptions_page = receptions[debut:debut + par_page]

    options_produits = "".join([f"<option value='{html.escape(p['nom'])}'></option>" for p in produits])
    produits_json = json.dumps(produits)

    lignes_bl = ""
    if not receptions_page:
        lignes_bl = "<tr><td colspan='8' style='text-align:center;padding:15px'>Aucun BL enregistré</td></tr>"
    else:
        for r in receptions_page:
            n_bl = r.get('n_bl','')
            lignes_bl += f"""
            <tr style='border-bottom:1px solid #eee'>
                <td style='padding:10px;text-align:left'><b>{html.escape(n_bl)}</b></td>
                <td style='padding:10px;text-align:center'>{html.escape(r.get('n_bc',''))}</td>
                <td style='padding:10px;text-align:center'>{html.escape(r.get('fournisseur',''))}</td>
                <td style='padding:10px;text-align:center'>{html.escape(r.get('date',''))}</td>
                <td style='padding:10px;text-align:right'>{int(r.get('total_ht',0)):,} FCFA</td>
                <td style='padding:10px;text-align:right'>{int(r.get('total_ttc',0)):,} FCFA</td>
                <td style='padding:10px;text-align:center'>{len(r.get('lignes',[]))}</td>
                <td style='padding:10px;text-align:center'>
                    <a href='/reception/imprimer/{html.escape(n_bl)}' target='_blank' 
                       style='padding:5px 10px;background:#007bff;color:white;text-decoration:none;border-radius:4px;font-size:12px'>
                       Imprimer
                    </a>
                </td>
            </tr>
            """
    
    # BOUTONS PAGINATION
    boutons_pagination = ""
    if pages > 1:
        for i in range(1, pages + 1):
            style = "background:#007bff;color:white;border-color:#007bff" if i == page else "background:white;color:#007bff"
            boutons_pagination += f"<a href='/reception?page={i}' style='padding:8px 12px;margin:2px;border:1px solid #007bff;border-radius:4px;text-decoration:none;{style}'>{i}</a>"

    html_content = f"""
    {CSS}
    <div class='nav'>{menu}</div>
    <div style='padding:20px;background:#f4f6f9;min-height:90vh'>
        <div style='display:flex; gap:10px; margin-bottom:20px;'>
            <a href='/reception/import' style='background:#17a2b8;color:white;padding:8px 12px;border-radius:5px;text-decoration:none;font-weight:bold;font-size:14px'>Importer BL</a>
            <a href='/model_reception.csv' style='background:#ffc107;color:#333;padding:8px 12px;border-radius:5px;text-decoration:none;font-weight:bold;font-size:14px'>Modèle BL</a>
            <a href='/produits/ajouter' style='background:#28a745;color:white;padding:8px 12px;border-radius:5px;text-decoration:none;font-weight:bold;font-size:14px'>+ Produit</a>
        </div>

        <h2 style='color:#333;margin-bottom:15px'>Reception Marchandises</h2>
        <form method='POST' action='/reception/valider' id='form_bl'>
            <input type='hidden' name='panier_json' id='panier_json'>
            <div style='background:white;padding:15px;border-radius:8px;margin-bottom:15px;box-shadow:0 2px 4px rgba(0,0,0,0.1)'>
                <div style='display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap:15px; margin-bottom:15px;'>
                    <div><label style='font-weight:bold;font-size:14px'>N° BL</label><input name='n_bl' required style='width:100%;padding:8px'></div>
                    <div><label style='font-weight:bold;font-size:14px'>N° Bon Cde</label><input name='n_bc' style='width:100%;padding:8px'></div>
                    <div><label style='font-weight:bold;font-size:14px'>Fournisseur</label><input name='fournisseur' style='width:100%;padding:8px'></div>
                    <div><label style='font-weight:bold;font-size:14px'>Date</label><input type='date' name='date' value='{datetime.now().strftime("%Y-%m-%d")}' style='width:100%;padding:8px'></div>
                </div>

                <div style='background:#fff3cd;padding:5px 8px;border-radius:5px;margin-bottom:10px'>
                    <label style='font-weight:bold;color:#856404;font-size:11px;display:block;margin-bottom:2px'>📷 SCAN CODE BARRE</label>
                    <div style='width:350px;max-width:100%'>
                        <input type='text' id='scan_input' placeholder='Scannez ici' autofocus style='width:100%!important;padding:4px 6px!important;font-size:12px!important;height:26px!important;border:1px solid #ccc'>
                    </div>
                </div>

                <div style='background:#e8f5e9;padding:12px;border-radius:5px;margin-bottom:10px'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px'>
                        <label style='font-weight:bold;color:#2e7d32;font-size:14px'>+ Ajouter un nouveau produit au BL</label>
                        <div style='border:1px solid #ccc;padding:8px;border-radius:5px;background:white'>
                            <label><b>TVA</b></label><br>
                            <input type="text" id="tva_taux" name="tva_taux" list="liste_tva" value="18" 
                                   style="width:80px;padding:4px" placeholder="Taper ou Choisir" onchange="calculPtotal()">
                            <datalist id="liste_tva">
                                <option value="0">Exonéré</option><option value="5"></option>
                                <option value="10"></option><option value="18"></option><option value="20"></option>
                            </datalist>
                            %
                        </div>
                    </div>
                    <div style='display:flex; gap:8px; margin-top:5px; flex-wrap:wrap; align-items:end'>
                        <div><label style='font-size:12px'>Produit</label><br>
                        <input list='liste_produits' type='text' id='new_nom' placeholder='Taper ou Choisir' onchange='remplirPrixAuto()' style='width:200px;padding:6px;font-size:14px'></div>
                        <datalist id='liste_produits'>{options_produits}</datalist>
                        
                        <div><label style='font-size:12px'>Qte Cdee</label><br><input type='number' id='new_qte_cdee' value='1' style='width:80px;padding:6px;font-size:14px'></div>
                        <div><label style='font-size:12px'>Qte Reçue</label><br><input type='number' id='new_qte' value='1' style='width:80px;padding:6px;font-size:14px'></div>
                        <div><label style='font-size:12px'>PA</label><br><input type='number' id='new_pa' placeholder='0' step='0.01' style='width:90px;padding:6px;font-size:14px'></div>
                        <div><label style='font-size:12px'>PV</label><br><input type='number' id='new_pv' placeholder='0' step='0.01' style='width:90px;padding:6px;font-size:14px'></div>
                        <div><label style='font-size:12px'>DLC</label><br><input type='text' id='new_dlc' placeholder='010226' style='width:100px;padding:6px;font-size:14px'></div>
                        <div><label style='font-size:12px'>P.Total</label><br><input type='text' id='new_ptotal' readonly style='width:110px;padding:6px;font-size:14px;background:#eee;font-weight:bold'></div>
                        <button type='button' onclick='ajouterNouveauProduit()' style='background:#007bff;color:white;border:none;padding:8px 12px;border-radius:4px;cursor:pointer;font-size:14px;height:34px'>+ Ajouter</button>
                    </div>
                </div>

                <div id='panier' style='background:#f8f9fa;padding:10px;border-radius:5px;margin-bottom:10px;min-height:50px'>
                    <b>Produits dans ce BL:</b>
                    <div id='liste_panier'><i>Aucun produit ajouté</i></div>
                </div>

                <div style='text-align:right'>
                    <button type='submit' onclick="document.getElementById('panier_json').value=JSON.stringify(window.panierBL)" style='background:#28a745;color:white;padding:10px 18px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;font-size:14px'>ENREGISTRER LE BL</button>
                </div>
            </div>
        </form>

        <h2 style='color:#333;margin-bottom:15px'>Liste des BL enregistres - Page {page}/{pages} - Total: {total_bl}</h2>
        <div style='background:white;padding:15px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)'>
            <table width='100%' style='border-collapse:collapse'>
                <tr style='background:#2c3e50;color:white'>
                    <th style='padding:10px;text-align:left;font-size:14px'>N° BL</th><th style='padding:10px;font-size:14px'>N° BC</th>
                    <th style='padding:10px;font-size:14px'>Fournisseur</th><th style='padding:10px;font-size:14px'>Date</th>
                    <th style='padding:10px;font-size:14px'>Total HT</th><th style='padding:10px;font-size:14px'>Total TTC</th>
                    <th style='padding:10px;font-size:14px'>Nb Produits</th><th style='padding:10px;font-size:14px'>Action</th>
                </tr>
                {lignes_bl}
            </table>
            <div style='display:flex;flex-wrap:wrap;gap:5px;justify-content:center;margin-top:15px'>{boutons_pagination}</div>
        </div>
    </div>

    <script>
(function() {{
    if (window.panierBL) return; 
    window.panierBL = [];
    const produitsData = {produits_json};
    // ... le reste du JS identique ...
}})();
</script>
    """
    return HTMLResponse(html_content)
@app.get("/reception/import")
async def page_import_bl(request: Request, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse): return current_user
    menu = build_menu(current_user)
    html = f"""
    {CSS}
    <div class='nav'>{menu}</div>
    <div style='padding:20px; max-width:700px; margin:auto'>
        <h2>Importer un BL via CSV</h2>
        <div style='background:#fff3cd; padding:12px; border-radius:5px; margin-bottom:15px'>
            <b>Format CSV obligatoire:</b><br>
            <code>n_bl,n_bc,fournisseur,date,nom_produit,code_barre,qte_cdee,qte_recue,pa,pv,dcl,tva</code><br>
            <a href='/model_reception.csv' style='display:inline-block;margin-top:8px;background:#007bff;color:white;padding:6px 12px;border-radius:4px;text-decoration:none'>Télécharger le modèle</a>
        </div>
        <form method='POST' action='/reception/import' enctype='multipart/form-data' style='background:white; padding:20px; border-radius:8px'>
            <div style='margin-bottom:15px'>
                <label><b>Fichier CSV du BL</b></label><br>
                <input type='file' name='fichier' accept='.csv' required style='padding:8px; width:100%'>
            </div>
            <button type='submit' style='background:#17a2b8; color:white; padding:10px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer'>IMPORTER ET ENREGISTRER BL</button>
        </form>
    </div>
    """
    return HTMLResponse(html)
@app.post("/reception/valider")
async def valider_reception(request: Request, current_user: dict = Depends(require_permission("ajouter_reception"))):
    form = await request.form()
    panier_json = form.get('panier_json')
    if not panier_json: return RedirectResponse(url="/reception", status_code=303)
    
    lignes = json.loads(panier_json)
    produits = lire(F_PRODUITS)
    receptions = lire("receptions.json")

    total_ht = 0
    total_ttc = 0

    for ligne in lignes:
        nom = ligne['nom']
        qte = float(ligne['qte'])
        pa = float(ligne['pa'])
        pv = float(ligne['pv'])
        tva = float(ligne['tva'])

        # 1. Mettre à jour stock + PA + PV du produit
        prod = next((p for p in produits if p['nom'] == nom), None)
        if prod:
            prod['stock'] = prod.get('stock', 0) + qte
            if pa > 0: prod['prix_achat'] = pa
            if pv > 0: prod['prix_vente'] = pv
        else: # Si créé via scan mais pas encore sauvé
            produits.append({"nom":nom, "code_barre":"", "stock":qte, "prix_achat":pa, "prix_vente":pv})

        total_ht += float(ligne['qte']) * float(ligne['pa'])
        total_ttc += float(ligne['ptotal'])

    ecrire(F_PRODUITS, produits)

    # 2. Sauvegarder le BL
    new_bl = {
        "n_bl": form.get('n_bl'),
        "n_bc": form.get('n_bc'),
        "fournisseur": form.get('fournisseur'),
        "date": form.get('date'),
        "total_ht": total_ht,
        "total_ttc": total_ttc,
        "lignes": lignes,
        "user": current_user.get('username')
    }
    receptions.append(new_bl)
    ecrire("receptions.json", receptions)

    return RedirectResponse(url="/reception", status_code=303)
@app.post("/reception/import")
async def import_bl(request: Request, fichier: UploadFile = File(...), current_user: dict = Depends(require_permission("ajouter_reception"))):
    contenu = await fichier.read()
    stream = io.StringIO(contenu.decode("utf-8-sig"))
    reader = csv.DictReader(stream)
    
    produits = lire(F_PRODUITS)
    receptions = lire("receptions.json")
    
    lignes = []
    n_bl = n_bc = fournisseur = ""
    date = datetime.now().strftime("%Y-%m-%d")
    total_ht = 0
    total_ttc = 0

    for row in reader:
        # On prend les infos du BL dès qu'on les trouve
        n_bl = row.get('n_bl','').strip() or n_bl
        n_bc = row.get('n_bc','').strip() or n_bc
        fournisseur = row.get('fournisseur','').strip() or fournisseur
        date = row.get('date','').strip() or date

        nom = row.get('nom_produit','').strip()
        if not nom: 
            continue # on saute les lignes vides

        code = row.get('code_barre','').strip()
        qte_cdee = float(row.get('qte_cdee',0) or 0)
        qte = float(row.get('qte_recue',0) or 0)
        pa = float(row.get('pa',0) or 0)
        pv = float(row.get('pv',0) or 0)
        dlc = row.get('dcl','')
        tva = float(row.get('tva',18) or 18)

        # 1. Chercher ou Créer le produit
        prod = next((p for p in produits if str(p.get('code_barre','')) == code and code != ""), None)
        if not prod:
            prod = next((p for p in produits if p['nom'] == nom), None)
        if not prod:
            prod = {"nom": nom, "code_barre": code, "prix_achat": pa, "prix_vente": pv, "stock": 0}
            produits.append(prod)
        
        # 2. Mettre à jour stock + PA + PV
        prod['stock'] = prod.get('stock',0) + qte
        if pa > 0: prod['prix_achat'] = pa
        if pv > 0: prod['prix_vente'] = pv

        ptotal = qte * pa * (1 + tva/100)
        total_ht += qte * pa
        total_ttc += ptotal

        lignes.append({
            "nom": nom, "code_barre": code, "qte_cdee": qte_cdee, "qte": qte,
            "pa": pa, "pv": pv, "ptotal": ptotal, "dlc": dlc, "tva": tva
        })

    # Bloquer si pas de N° BL
    if not n_bl:
        return HTMLResponse("<h3>Erreur: Le champ n_bl est obligatoire dans le CSV</h3><a href='/reception/import'>Retour</a>", status_code=400)

    ecrire(F_PRODUITS, produits)

    # 3. Sauvegarder le BL
    new_bl = {
        "n_bl": n_bl, "n_bc": n_bc, "fournisseur": fournisseur, "date": date,
        "total_ht": total_ht, "total_ttc": total_ttc, "lignes": lignes,
        "user": current_user.get('username'), "source": "import_csv"
    }
    receptions.append(new_bl)
    ecrire("receptions.json", receptions)

    return RedirectResponse(url=f"/reception?msg=BL {n_bl} importé avec {len(lignes)} produits", status_code=303)
@app.get("/reception/liste")
async def liste_receptions(request: Request, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    receptions = lire("receptions.json")
    receptions.reverse() # Les plus récents en premier

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Liste des BL</title>
        <style>
            body{{font-family:Arial;padding:20px;background:#f5f5f5}}
            table{{width:100%;border-collapse:collapse;background:white}}
            th,td{{padding:10px;border:1px solid #ddd;text-align:left}}
            th{{background:#007bff;color:white}}
            .btn{{padding:8px 15px;background:#28a745;color:white;text-decoration:none;border-radius:4px}}
        </style>
    </head>
    <body>
        <h1>📦 Liste des Bons de Livraison</h1>
        <a href="/reception" class="btn">+ Nouveau BL</a>
        <br><br>
        <table>
            <tr>
                <th>N° BL</th>
                <th>N° BC</th>
                <th>Fournisseur</th>
                <th>Date</th>
                <th>Total HT</th>
                <th>Total TTC</th>
                <th>Nb Produits</th>
            </tr>
    """
    
    if not receptions:
        html += "<tr><td colspan='7' style='text-align:center'>Aucun BL enregistré</td></tr>"
    else:
        for r in receptions:
            html += f"""
            <tr>
                <td><b>{r.get('n_bl','')}</b></td>
                <td>{r.get('n_bc','')}</td>
                <td>{r.get('fournisseur','')}</td>
                <td>{r.get('date','')}</td>
                <td>{r.get('total_ht',0):,} FCFA</td>
                <td>{r.get('total_ttc',0):,} FCFA</td>
                <td>{len(r.get('lignes',[]))}</td>
                <td><a href="/reception/imprimer/{r.get('n_bl')}" target="_blank" style="padding:5px 10px;background:#007bff;color:white;text-decoration:none;border-radius:4px">🖨️ Imprimer</a></td>
            </tr>
            """
    
    html += """
        </table>
    </body>
    </html>
    """
    return HTMLResponse(html)
@app.get("/model_reception.csv")
async def download_model():
    contenu = "n_bl,n_bc,fournisseur,date,nom_produit,code_barre,qte_cdee,qte_recue,pa,pv,dcl,tva\n"
    contenu += "BL2025001,BC123,SONATEL,2026-08-20,ECRAN 24'',123456789,10,10,50000,75000,010226,18\n"
    return Response(content=contenu, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=model_reception.csv"})


@app.get("/export")
async def page_export(current_user: dict = Depends(require_permission("voir_export"))):
    if isinstance(current_user, RedirectResponse): return current_user
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"""
    <div class='nav'>{menu}</div>
    <div style='padding:20px'>
        <div class='card'>
            <h1>Exports</h1>
            <a class='success' href='/export/ventes'>📥 Exporter Ventes CSV</a>
            <a class='success' href='/export/produits'>📥 Exporter Produits CSV</a>
            <a class='info' href='/export/achats'>📥 Exporter Achats CSV</a>
        </div>
    </div>
    """)

@app.get("/export/ventes")
async def export_ventes(current_user: dict = Depends(require_permission("voir_export"))):
    ventes = lire(F_VENTES)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Client', 'Produit', 'Qte', 'Prix Unitaire', 'Total', 'Paiement', 'Caissier'])
    for v in ventes:
        writer.writerow([
            v.get('id',''), v.get('date',''), v.get('client',''), v.get('produit',''), 
            v.get('qte',''), v.get('prix',''), v.get('total',''), v.get('mode_paiement',''), v.get('caissier','')
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=ventes.csv"})

@app.get("/export/produits")
async def export_produits(current_user: dict = Depends(require_permission("voir_export"))):
    produits = lire(F_PRODUITS)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nom', 'Prix', 'Prix Achat', 'Stock', 'Stock Min', 'DLC'])
    for p in produits:
        writer.writerow([p.get('nom',''), p.get('prix',''), p.get('prix_achat',''), p.get('stock',''), p.get('stock_min',''), p.get('dlc','')])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=produits.csv"})

@app.get("/export/achats")
async def export_achats(current_user: dict = Depends(require_permission("voir_export"))):
    achats = lire(F_ACHATS)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['N° BL', 'Fournisseur', 'Date', 'Produit', 'Qte', 'Prix'])
    for a in achats:
        for l in a.get('lignes', []):
            writer.writerow([a.get('num_bl',''), a.get('fournisseur',''), a.get('date',''), l.get('nom',''), l.get('qte',''), l.get('prix','')])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=achats.csv"})

@app.get("/model_bl.csv")
async def download_model_bl():
    return FileResponse("model_bl.csv", filename="model_bl.csv")

@app.get("/reception/imprimer/{n_bl}")
async def imprimer_bl(request: Request, n_bl: str, current_user: dict = Depends(require_permission("voir_reception"))):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    receptions = lire("receptions.json")
    bl = next((r for r in receptions if r.get('n_bl') == n_bl), None) 
    
    if not bl:
        return HTMLResponse(f"<h1>BL {n_bl} introuvable</h1>")

    lignes = bl.get('lignes', [])
    
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BL {n_bl}</title>
            <style>
                body{{font-family:Arial;padding:30px}}
                h1{{text-align:center}}
                .info{{margin-bottom:20px}}
                table{{width:100%;border-collapse:collapse}}
                th,td{{padding:8px;border:1px solid #000}}
                th{{background:#eee}}
                .total{{text-align:right;font-weight:bold;font-size:16px}}
                .btn-retour{{padding:8px 15px;background:#6c757d;color:white;text-decoration:none;border-radius:5px;margin-right:10px}}
                .btn-imprimer{{padding:10px 20px;background:#28a745;color:white;border:none;border-radius:5px;cursor:pointer;float:right}}
                @media print {{ 
                    .btn-retour, .btn-imprimer {{display:none}} 
                }}
            </style>
        </head>
        <body>
            <a href="/reception" class="btn-retour">← Retour Liste</a>
            <button onclick="window.print()" class="btn-imprimer">Imprimer</button>
            <div style="clear:both"></div>
            <h1>BON DE RECEPTION</h1>
            <div class="info">
                <b>N° BL:</b> {bl.get('n_bl','-')} <br>
                <b>N° BC:</b> {bl.get('n_bc','-')} <br>
                <b>Fournisseur:</b> {bl.get('fournisseur','-')} <br>
                <b>Date:</b> {bl.get('date','-')}
            </div>
            <table>
                <tr>
                    <th>Produit</th><th>Qte</th><th>PA</th><th>Lot</th><th>DLC</th><th>Total</th>
                </tr>
    """
    
    for l in lignes:
        total_ligne = l.get('qte',0) * l.get('pa',0)
        html += f"""
            <tr>
                <td>{l.get('produit','')}</td>
                <td>{l.get('qte',0)}</td>
                <td>{l.get('pa',0):,} FCFA</td>
                <td>{l.get('lot','')}</td>
                <td>{l.get('dlc','')}</td>
                <td>{total_ligne:,} FCFA</td>
            </tr>
        """
    
    html += f"""
                <tr>
                    <td colspan="5" class="total">TOTAL HT</td>
                    <td class="total">{bl.get('total_ht',0):,} FCFA</td>
                </tr>
            </table>
        </body>
        </html>
    """
    return HTMLResponse(html)

@app.post("/modes_paiement/ajouter")
async def ajouter_mode_paiement(nom: str = Form(...), current_user: dict = Depends(require_permission("gerer_parametres"))):
    paiements = lire(F_PAIEMENT)
    if any(p['nom'].lower() == nom.lower() for p in paiements):
        return JSONResponse({"status":"existe"})
    paiements.append({"nom": nom})
    ecrire(F_PAIEMENT, paiements)
    return JSONResponse({"status":"ok"})

# RAYONS
@app.get("/rayons/ajouter")
async def ajouter_rayon_get(current_user: dict = Depends(require_permission("voir_produits"))):
    menu = build_menu(current_user)
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Ajouter Rayon</h1><form method='post' action='/rayons/ajouter'><input name='nom' placeholder='Nom Rayon: Boissons' required><button>Enregistrer</button></form></div></div>")

@app.post("/rayons/ajouter")
async def ajouter_rayon_post(nom: str = Form(...)):
    rayons = lire(F_RAYONS)
    rayons.append({"id": len(rayons)+1, "nom": nom})
    sauver(F_RAYONS, rayons)
    return RedirectResponse(url="/produits", status_code=303)

# ETAGERES
@app.get("/etageres/ajouter")
async def ajouter_etagere_get(current_user: dict = Depends(require_permission("voir_produits"))):
    menu = build_menu(current_user)
    rayons = lire(F_RAYONS)
    options = "".join([f"<option value='{r['id']}'>{r['nom']}</option>" for r in rayons])
    return HTMLResponse(CSS + f"<div class='nav'>{menu}</div><div style='padding:20px'><div class='card'><h1>Ajouter Etagere</h1><form method='post' action='/etageres/ajouter'><select name='rayon_id'>{options}</select><input name='nom' placeholder='Nom Etagere: E1' required><button>Enregistrer</button></form></div></div>")

@app.post("/etageres/ajouter")
async def ajouter_etagere_post(rayon_id: int = Form(...), nom: str = Form(...)):
    etageres = lire(F_ETAGERES)
    etageres.append({"id": len(etageres)+1, "rayon_id": rayon_id, "nom": nom})
    sauver(F_ETAGERES, etageres)
    return RedirectResponse(url="/produits", status_code=303)

def open_browser():
    url = "http://127.0.0.1:8001"
    try:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        subprocess.Popen([chrome_path, f'--app={url}', '--start-fullscreen', '--disable-infobars'])
    except:
        webbrowser.open_new(url)

# CONFIG TEST
PARAMETRES_PAIEMENT = {
    "om_marchand": "770000001",
    "wave_marchand": "780000001", 
    "nom_pharmacie": "PHARMACIE DIKOLO TEST"
}


import qrcode
import base64
from io import BytesIO

@app.get("/api/generer_qr")
async def generer_qr(mode: str, montant: int):
    numero_marchand = "778030996" # <-- METS TON NUMERO OM
    
    if mode == "OM":
        data = f"OM*{numero_marchand}*{montant}#"
    else:
        data = f"WV*{numero_marchand}*{montant}#" # pour Wave
    
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    
    return {"qr_image": f"data:image/png;base64,{qr_b64}"}
import requests
import uuid

OM_API_KEY = "TA_CLE_OM_COLLECT"
OM_CLIENT_ID = "TON_CLIENT_ID"
OM_TOKEN_URL = "https://api.orange.com/oauth/v3/token"
OM_PAY_URL = "https://api.orange.com/orange-money-webpay/v1/webpayment"

WAVE_API_KEY = "TA_CLE_WAVE_SECRET_KEY"
WAVE_PAY_URL = "https://api.wave.com/v1/commerce/checkouts"

# 1. GENERER QR OM
@app.get("/api/generer_qr")
async def generer_qr(mode: str, montant: float):
    ref = str(uuid.uuid4())[:8]
    
    if mode == "OM":
        # Récupérer token OM
        token_res = requests.post(OM_TOKEN_URL, data={
            'grant_type': 'client_credentials',
            'client_id': OM_CLIENT_ID,
            'client_secret': OM_API_KEY
        })
        access_token = token_res.json()['access_token']
        
        # Demander paiement
        pay_res = requests.post(OM_PAY_URL, 
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "amount": int(montant),
                "currency": "XOF",
                "order_id": ref,
                "return_url": "http://127.0.0.1:8000/api/callback_om",
                "cancel_url": "http://127.0.0.1:8000"
            }
        )
        data = pay_res.json()
        qr_url = data['payment_url'] # OM donne un lien, on le met en QR
        
    elif mode == "WAVE":
        pay_res = requests.post(WAVE_PAY_URL,
            headers={"Authorization": f"Bearer {WAVE_API_KEY}"},
            json={
                "amount": int(montant),
                "currency": "XOF",
                "client_reference": ref,
                "success_url": "http://127.0.0.1:8000/api/callback_wave?status=success",
                "error_url": "http://127.0.0.1:8000/api/callback_wave?status=error"
            }
        )
        data = pay_res.json()
        qr_url = data['wave_launch_url']
    
    # On convertit le lien en QR
    import qrcode, base64, io
    img = qrcode.make(qr_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    
    return {"qr_image": f"data:image/png;base64,{qr_b64}", "ref": ref}


# 2. WEBHOOK DE CONFIRMATION
@app.get("/api/callback_om")
async def callback_om(order_id: str):
    sauvegarder_vente_paye(order_id, "OM")
    return {"status": "ok", "ref": order_id}


@app.get("/api/callback_wave")
async def callback_wave(client_reference: str):
    sauvegarder_vente_paye(client_reference, "WAVE")
    return {"status": "ok", "ref": client_reference}
@app.get("/api/creer_vente_om")
async def creer_vente_om(total: int = 450):
    ventes = charger_json("data/ventes.json")
    ref_temp = str(uuid.uuid4())[:8]
    
    nouvelle_vente = {
        "id": str(len(ventes) + 1),
        "date": datetime.now().isoformat(),
        "client": "Client Anonyme",
        "caissier": "admin",
        "mode_paiement": "OM_EN_ATTENTE",
        "panier": [{"nom": "Test Produit", "prix": total, "qte": 1}],
        "total": total,
        "ref_temp": ref_temp,
        "statut": "en_attente_paiement"
    }
    ventes.append(nouvelle_vente)
    sauvegarder_json("data/ventes.json", ventes)
    
    return {"ref_temp": ref_temp, "montant": total}
@app.get("/voir_table")
async def voir_table():
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
    c.execute("PRAGMA table_info(paiements)")
    colonnes = c.fetchall()
    conn.close()
    return {"colonnes_paiements": colonnes}
    
if __name__ == "__main__":
    threading.Timer(1.25, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8001)