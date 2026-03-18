import os
import yfinance as yf
import pandas as pd

# Liste des 40 entreprises du CAC 40 (Tickers Yahoo Finance - suffixe .PA pour Paris)
CAC40_TICKERS = [
    "AC.PA", "ACA.PA", "AI.PA", "AIR.PA", "BN.PA", "BNP.PA", "BVI.PA", "CA.PA", 
    "CAP.PA", "CS.PA", "DG.PA", "DSY.PA", "EL.PA", "EN.PA", "ENGI.PA", "ENX.PA", 
    "ERF.PA", "FGR.PA", "GLE.PA", "HO.PA", "KER.PA", "LR.PA", "MC.PA", "ML.PA", 
    "MT.AS", "OR.PA", "ORA.PA", "PUB.PA", "RI.PA", "RMS.PA", "RNO.PA", "SAF.PA", 
    "SAN.PA", "SGO.PA", "STLAP.PA", "STMPA.PA", "SU.PA", "TTE.PA", "URW.PA", "VIE.PA"
]

def telecharger_donnees_historiques():
    # 1. Création du dossier "historique" s'il n'existe pas
    dossier_historique = "historique"
    if not os.path.exists(dossier_historique):
        os.makedirs(dossier_historique)
        print(f"📁 Dossier '{dossier_historique}' créé avec succès.")
    else:
        print(f"📁 Le dossier '{dossier_historique}' existe déjà.")

    # 2. Boucle sur chaque entreprise pour télécharger et sauvegarder les données
    print("🚀 Début du téléchargement des données hebdomadaires...")
    
    for ticker in CAC40_TICKERS:
        try:
            print(f"Téléchargement pour {ticker}...")
            
            # Téléchargement via Yahoo Finance (interval='1wk' pour weekly, period='max' pour tout l'historique)
            # Vous pouvez changer period='max' par period='5y' ou '10y' si vous voulez moins lourd.
            data = yf.download(ticker, period="max", interval="1wk", progress=False)
            
            # Vérification si des données ont bien été trouvées
            if not data.empty:
                # Chemin de sauvegarde (ex: historique/MC.PA.csv)
                chemin_fichier = os.path.join(dossier_historique, f"{ticker}_cours.csv")
                
                # Sauvegarde en CSV
                data.to_csv(chemin_fichier)
                print(f"   ✅ Sauvegardé : {chemin_fichier}")
            else:
                print(f"   ⚠️ Aucune donnée trouvée pour {ticker}.")
                
        except Exception as e:
            print(f"   ❌ Erreur lors du téléchargement de {ticker} : {e}")

    print("🎉 Téléchargement terminé pour toutes les entreprises !")

if __name__ == "__main__":
    telecharger_donnees_historiques()