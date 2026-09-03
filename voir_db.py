import sqlite3

conn = sqlite3.connect("gestdiko.db")
c = conn.cursor()

c.execute("SELECT * FROM paiements ORDER BY id DESC")
lignes = c.fetchall()

print("=== DERNIERS PAIEMENTS ===")
for ligne in lignes:
    print(ligne)

conn.close()
input("Appuie sur Entrée pour fermer")