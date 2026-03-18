import os
import yfinance as yf
import pandas as pd

# La liste parfaite des 40 entreprises du CAC 40
CAC40_TICKERS = [
    "AC.PA", "ACA.PA", "AI.PA", "AIR.PA", "BN.PA", "BNP.PA", "BVI.PA", "CA.PA", 
    "CAP.PA", "CS.PA", "DG.PA", "DSY.PA", "EL.PA", "EN.PA", "ENGI.PA", "ENX.PA", 
    "ERF.PA", "FGR.PA", "GLE.PA", "HO.PA", "KER.PA", "LR.PA", "MC.PA", "ML.PA", 
    "MT.AS", "OR.PA", "ORA.PA", "PUB.PA", "RI.PA", "RMS.PA", "RNO.PA", "SAF.PA", 
    "SAN.PA", "SGO.PA", "STLAP.PA", "STMPA.PA", "SU.PA", "TTE.PA", "URW.PA", "VIE.PA"
]

def telecharger_fondamentaux():
    dossier = "historique"
    if not os.path.exists(dossier):
        os.makedirs(dossier)

    print("🚀 Début du téléchargement des données financières (Annuelles et Trimestrielles)...")

    for ticker in CAC40_TICKERS:
        print(f"\nTraitement de {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            
            # ==========================================
            # 1. DONNÉES ANNUELLES (_year)
            # ==========================================
            cr_year = stock.financials.dropna(how='all')
            bilan_year = stock.balance_sheet.dropna(how='all')
            cf_year = stock.cashflow.dropna(how='all')
            
            if not (cr_year.empty and bilan_year.empty):
                cr_year['Catégorie'] = 'Compte de Résultat'
                bilan_year['Catégorie'] = 'Bilan'
                cf_year['Catégorie'] = 'Flux de Trésorerie'
                
                df_year = pd.concat([cr_year, bilan_year, cf_year])
                # Réorganisation des colonnes pour mettre "Catégorie" en premier
                cols_year = ['Catégorie'] + [col for col in df_year.columns if col != 'Catégorie']
                df_year = df_year[cols_year]
                df_year.index.name = 'Métrique'
                
                chemin_year = os.path.join(dossier, f"{ticker}_year.csv")
                df_year.to_csv(chemin_year)
                print(f"   ✅ Annuel sauvegardé      : {ticker}_year.csv")
            else:
                print(f"   ⚠️ Aucune donnée annuelle trouvée pour {ticker}.")


            # ==========================================
            # 2. DONNÉES TRIMESTRIELLES (_quar)
            # ==========================================
            cr_quar = stock.quarterly_financials.dropna(how='all')
            bilan_quar = stock.quarterly_balance_sheet.dropna(how='all')
            cf_quar = stock.quarterly_cashflow.dropna(how='all')
            
            if not (cr_quar.empty and bilan_quar.empty):
                cr_quar['Catégorie'] = 'Compte de Résultat'
                bilan_quar['Catégorie'] = 'Bilan'
                cf_quar['Catégorie'] = 'Flux de Trésorerie'
                
                df_quar = pd.concat([cr_quar, bilan_quar, cf_quar])
                # Réorganisation des colonnes pour mettre "Catégorie" en premier
                cols_quar = ['Catégorie'] + [col for col in df_quar.columns if col != 'Catégorie']
                df_quar = df_quar[cols_quar]
                df_quar.index.name = 'Métrique'
                
                chemin_quar = os.path.join(dossier, f"{ticker}_quar.csv")
                df_quar.to_csv(chemin_quar)
                print(f"   ✅ Trimestriel sauvegardé : {ticker}_quar.csv")
            else:
                print(f"   ⚠️ Aucune donnée trimestrielle trouvée pour {ticker}.")
                
        except Exception as e:
            print(f"   ❌ Erreur technique sur {ticker} : {e}")

if __name__ == "__main__":
    telecharger_fondamentaux()