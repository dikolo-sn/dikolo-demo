import os, sys, json, csv, io, random, time, threading, webbrowser, subprocess
from datetime import datetime, date, timedelta
from collections import Counter
from io import BytesIO

from fastapi import FastAPI, Form, UploadFile, File, Depends, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import pandas as pd
import qrcode
import base64
import uuid
import sqlite3

FICHIER_VENTES = "data/ventes.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

app = FastAPI()
app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")
print("Dossier static:", resource_path("static"))

# CHEMINS
F_PRODUITS = resource_path("data/produits.json")
F_VENTES = resource_path("data/ventes.json")
F_PANIER = "panier.json"
F_ACHATS = resource_path("data/achats.json")
F_USERS = resource_path("data/users.json")
F_ROLES = resource_path("data/roles.json")
F_IPM = resource_path("data/ipm.json")
F_PAIEMENT = resource_path("data/paiements.json")
F_RETOURS = resource_path("data/retours.json")
F_INVENTAIRE = resource_path("data/inventaire.json")
F_DEPENSES = resource_path("data/depenses.json")
F_BLS = resource_path("data/bls.json")
F_LOTS = resource_path("data/lots.json")
F_RAYONS = resource_path("data/rayons.json")
F_ETAGERES = resource_path("data/etageres.json")

# DB
def init_db():
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
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
    c.execute("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_heure TEXT,
        client TEXT,
        produits TEXT,
        total REAL,
        caissier TEXT,
        paiement TEXT,
        reference TEXT,
        statut TEXT DEFAULT 'validee'
    )""")
    conn.commit()
    conn.close()

init_db()

class Paiement(BaseModel):
    mode_paiement: str
    montant: int
    reference: str
    statut: str

@app.post("/api/paiements")
def enregistrer_paiement(p: Paiement):
    conn = sqlite3.connect("gestDiKo.db")
    c = conn.cursor()
    c.execute("INSERT INTO paiements (date_heure, client, montant, mode_paiement, reference, statut) VALUES (?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", p.montant, p.mode_paiement, p.reference, p.statut))
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

CSS_GLOBAL = """<style>
body{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin:0; background:#ecf0f1}
.container{max-width:1200px; margin:auto; padding:20px}
.nav{background: #00BFFF; padding: 10px 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
.nav-top{display: flex; align-items: center; gap: 10px; margin-bottom: 8px;}
.nav-links{display: flex; flex-wrap: wrap; gap: 5px; align-items: center;}
.nav a{color: white; background: transparent; text-decoration: none; padding: 7px 12px; font-weight: 600; font-size: 14px; border-radius: 5px; white-space: nowrap;}
.nav a:hover{background: #1E90FF;}
.nav a.active{background: #1E90FF;}
.logo-text{color: white; font-size: 20px; font-weight: bold;}
.logout-btn{background: #e74c3c!important; margin-left: auto;}
.logout-btn:hover{background: #c0392b!important;}
.welcome-box{background: linear-gradient(135deg, #00BFFF, #1E90FF); color: white; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 20px;}
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
button,.btn{background:#3498db; color:white; padding:10px 18px; border:none; border-radius:6px; margin:4px; cursor:pointer}
.btn-danger{background:#e74c3c}
.btn-success{background:#27ae60}
</style>"""

PERMISSIONS_LISTE = {
    "voir_dashboard": "Voir Dashboard", "voir_produits": "Gérer Produits", "voir_achat": "Gérer Achats BL",
    "voir_vente": "Faire Vente", "voir_historique": "Voir Historique", "voir_export": "Faire Exports",
    "voir_users": "Gérer Utilisateurs", "voir_caisse": "Accès Caisse", "gerer_ipm": "Gérer IPM/Paiement",
    "voir_alertes": "Voir Alertes", "voir_reception": "Faire Réception", "voir_inventaire": "Faire Inventaire"
}

if not os.path.exists("data"):
    os.mkdir("data")

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
        else:
            with open(f, "w", encoding="utf-8") as file:
                json.dump([], file)

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
    if not isinstance(data, list):
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
    menu += "<div class='nav-top'>"
    menu += "<span class='logo-text'>DiKoLo (Digante-Koungheul-Lour)</span>"
    menu += "</div>"
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
.nav{background: #00BFFF; padding: 10px 20px;}
.nav-top{display: flex; align-items: center; gap: 10px; margin-bottom: 8px;}
.nav-links{display: flex; flex-wrap: wrap; gap: 5px; align-items: center;}
.nav a{color: white; background: transparent; text-decoration: none; padding: 7px 12px; font-weight: 600; font-size: 14px; border-radius: 5px; white-space: nowrap;}
.nav a:hover{background: #1E90FF;}
.nav a.active{background: #1E90FF;}
.logo-text{color: white; font-size: 20px; font-weight: bold;}
.logout-btn{background: #e74c3c!important;}
.logout-btn:hover{background: #c0392b!important;}
.welcome-box{background: linear-gradient(135deg, #00BFFF, #1E90FF); color: white; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 20px;}
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
    if(typeof toggleMobile === 'function'){ toggleMobile(); }
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
}
function toggleRoleInput(){var s=document.getElementById('role_select');var d=document.getElementById('new_role_div');d.style.display=s.value=='__new__'?'block':'none';}
</script>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    template_path = resource_path('templates/index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# ICI COLLE TOUTES TES AUTRES ROUTES @app.get @app.post
#...
