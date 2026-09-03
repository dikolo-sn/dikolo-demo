document.getElementById("btnValiderPaiement").addEventListener("click", async () => {
    const mode = document.getElementById("modePaiement").value;
    const montant = document.getElementById("totalPayer").innerText.replace(" F", "");
    const ref = document.getElementById("refTransaction").value;

    if (!ref) {
        alert("Collez d'abord le N° de Transaction");
        return;
    }

    const data = {
        mode_paiement: mode,
        montant: parseInt(montant),
        reference: ref,
        statut: "paye"
    };

    try {
        const response = await fetch("/api/paiements", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert("Paiement enregistré avec succès !");
            document.getElementById("zonePaiement").style.display = "none";
            // Ici tu peux vider le panier ou imprimer le ticket
        } else {
            alert("Erreur lors de l'enregistrement");
        }
    } catch (error) {
        alert("Erreur connexion serveur");
    }
});