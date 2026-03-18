from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import os
from typing import Optional

app = FastAPI(title="CAC 40 Screener & Portfolio Optimizer API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSSIER_HISTORIQUE = os.path.join(BASE_DIR, "historique")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CAC40_TICKERS = [
    "AC.PA", "ACA.PA", "AI.PA", "AIR.PA", "BN.PA", "BNP.PA", "BVI.PA", "CA.PA",
    "CAP.PA", "CS.PA", "DG.PA", "DSY.PA", "EL.PA", "EN.PA", "ENGI.PA", "ENX.PA",
    "ERF.PA", "FGR.PA", "GLE.PA", "HO.PA", "KER.PA", "LR.PA", "MC.PA", "ML.PA",
    "MT.AS", "OR.PA", "ORA.PA", "PUB.PA", "RI.PA", "RMS.PA", "RNO.PA", "SAF.PA",
    "SAN.PA", "SGO.PA", "STLAP.PA", "STMPA.PA", "SU.PA", "TTE.PA", "URW.PA", "VIE.PA"
]

# ──────────────────────────────────────────────────────────────────
# UTILITAIRES : lecture et nettoyage des fichiers CSV
# ──────────────────────────────────────────────────────────────────

def lire_cours(ticker: str, annees: int = 5) -> Optional[pd.Series]:
    """
    Lit {ticker}_cours.csv et retourne la série de prix Close hebdomadaires.
    Gère le format MultiIndex produit par yfinance.download().
    """
    chemin = os.path.join(DOSSIER_HISTORIQUE, f"{ticker}_cours.csv")
    if not os.path.exists(chemin):
        return None
    try:
        # yfinance produit un CSV avec 2 lignes d'en-tête : ('Price'/'Close', 'TICKER')
        df = pd.read_csv(chemin, header=[0, 1], index_col=0)

        # Chercher la colonne Close ou Price (les deux noms possibles selon version yfinance)
        series = None
        for label in ["Close", "Price"]:
            if (label, ticker) in df.columns:
                series = df[(label, ticker)].copy()
                break
        if series is None:
            # Dernier recours : première colonne disponible
            series = df.iloc[:, 0].copy()

        # Nettoyage des index de dates
        idx = pd.to_datetime(df.index, errors="coerce")
        if idx.tz is not None:
            idx = idx.tz_convert(None)
        series.index = idx

        series = pd.to_numeric(series, errors="coerce").dropna().sort_index()

        # Filtrage sur N années (0 = tout l'historique)
        if annees and annees > 0:
            date_limite = pd.Timestamp.now() - pd.DateOffset(years=annees)
            series = series[series.index >= date_limite]

        return series if not series.empty else None

    except Exception as e:
        print(f"[COURS] Erreur {ticker}: {e}")
        return None


def lire_fondamentaux(ticker: str) -> dict:
    """
    Lit {ticker}_year.csv et extrait les métriques financières réelles.
    Structure attendue : lignes = métriques (noms yfinance anglais), colonnes = dates annuelles.
    Retourne un dict avec les valeurs numériques disponibles.
    """
    chemin = os.path.join(DOSSIER_HISTORIQUE, f"{ticker}_year.csv")
    if not os.path.exists(chemin):
        return {}

    try:
        df = pd.read_csv(chemin, index_col=0)

        # Supprimer la colonne « Catégorie » ajoutée par le scrapper
        if "Catégorie" in df.columns:
            df = df.drop(columns=["Catégorie"])

        # Tout convertir en numérique
        df = df.apply(pd.to_numeric, errors="coerce")

        # Trier les colonnes (dates ISO) décroissant → colonne 0 = exercice le plus récent
        df = df.reindex(sorted(df.columns, reverse=True), axis=1)

        def get(row_candidates, col=0):
            """Retourne la première valeur non-NaN trouvée parmi les noms de lignes candidats."""
            for name in row_candidates:
                if name in df.index:
                    vals = df.loc[name].dropna()
                    if col < len(vals):
                        v = float(vals.iloc[col])
                        if v != 0:
                            return v
            return np.nan

        # ── Extraction des métriques ──────────────────────────────
        total_revenue = get(["Total Revenue", "TotalRevenue"])
        net_income    = get(["Net Income", "NetIncome",
                              "Net Income Common Stockholders"])
        equity        = get(["Stockholders Equity", "Common Stock Equity",
                              "Total Equity Gross Minority Interest"])
        total_debt    = get(["Total Debt", "TotalDebt",
                              "Long Term Debt", "LongTermDebt"])
        basic_eps     = get(["Basic EPS", "BasicEPS",
                              "Diluted EPS", "DilutedEPS"])
        shares        = get(["Basic Average Shares", "Diluted Average Shares",
                              "Ordinary Shares Number", "Share Issued"])
        div_paid      = get(["Dividends Paid", "Cash Dividends Paid",
                              "Common Stock Dividend Paid"])

        # ── Calcul des ratios ─────────────────────────────────────
        metrics = {}

        if pd.notna(net_income) and pd.notna(total_revenue) and total_revenue != 0:
            metrics["Net_Margin"] = net_income / total_revenue

        if pd.notna(net_income) and pd.notna(equity) and equity > 0:
            metrics["ROE"] = net_income / equity

        if pd.notna(total_debt) and pd.notna(equity) and equity > 0:
            metrics["Debt_Equity"] = abs(total_debt) / abs(equity)

        # PER = dernier prix / BPA  (nécessite aussi le fichier cours)
        series_cours = lire_cours(ticker, annees=0)
        if series_cours is not None:
            dernier_prix = float(series_cours.iloc[-1])
            if pd.notna(basic_eps) and basic_eps > 0:
                metrics["PER"] = dernier_prix / basic_eps

            # Dividend Yield = DPS / dernier prix
            if pd.notna(div_paid) and pd.notna(shares) and shares > 0 and dernier_prix > 0:
                dps = abs(div_paid) / shares
                metrics["Dividend_Yield"] = dps / dernier_prix

        return metrics

    except Exception as e:
        print(f"[FONDAMENTAUX] Erreur {ticker}: {e}")
        return {}


# ──────────────────────────────────────────────────────────────────
# LOGIQUE DE NOTATION (inchangée, étendue pour gérer les NaN)
# ──────────────────────────────────────────────────────────────────

def calculer_note(metrics: dict):
    score = 0
    detail = {}

    # 1. Marge nette (20 pts)
    marge = metrics.get("Net_Margin", np.nan)
    if pd.notna(marge):
        if marge > 0.15: pts = 20
        elif marge > 0.10: pts = 15
        elif marge > 0.05: pts = 10
        elif marge > 0: pts = 5
        else: pts = 0
    else:
        pts = 0
    score += pts
    detail["pts_marge"] = pts

    # 2. ROE (20 pts)
    roe = metrics.get("ROE", np.nan)
    if pd.notna(roe):
        if roe > 0.15: pts = 20
        elif roe > 0.10: pts = 15
        elif roe > 0.05: pts = 10
        elif roe > 0: pts = 5
        else: pts = 0
    else:
        pts = 0
    score += pts
    detail["pts_roe"] = pts

    # 3. PER (20 pts) — non noté si indisponible
    per = metrics.get("PER", np.nan)
    if pd.notna(per):
        if 10 <= per <= 25: pts = 20
        elif (8 <= per < 10) or (25 < per <= 35): pts = 15
        elif (5 <= per < 8) or (35 < per <= 45): pts = 10
        elif per > 0: pts = 5
        else: pts = 0
    else:
        pts = 0  # donnée manquante → 0 pt
    score += pts
    detail["pts_per"] = pts

    # 4. Dette / Capitaux propres (20 pts)
    de = metrics.get("Debt_Equity", np.nan)
    if pd.notna(de):
        if de < 0.5: pts = 20
        elif de < 1.0: pts = 15
        elif de < 1.5: pts = 10
        elif de < 2.0: pts = 5
        else: pts = 0
    else:
        pts = 0
    score += pts
    detail["pts_dette"] = pts

    # 5. Rendement dividende (20 pts)
    dy = metrics.get("Dividend_Yield", np.nan)
    if pd.notna(dy):
        if dy > 0.04: pts = 20
        elif dy > 0.02: pts = 15
        elif dy > 0.01: pts = 10
        elif dy > 0: pts = 5
        else: pts = 0
    else:
        pts = 0
    score += pts
    detail["pts_dividende"] = pts

    if score >= 80: note = "AAA"
    elif score >= 65: note = "AA"
    elif score >= 50: note = "A"
    elif score >= 35: note = "BBB"
    elif score >= 20: note = "BB"
    else: note = "B"

    return note, score, detail


def fmt(v, decimals=2):
    """Formate une valeur numérique, retourne None si NaN."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), decimals)


# ──────────────────────────────────────────────────────────────────
# ROUTES API
# ──────────────────────────────────────────────────────────────────

@app.get("/api/tickers")
def get_tickers():
    """Retourne la liste des tickers pour lesquels un fichier de cours existe."""
    disponibles = []
    for ticker in CAC40_TICKERS:
        chemin = os.path.join(DOSSIER_HISTORIQUE, f"{ticker}_cours.csv")
        if os.path.exists(chemin):
            disponibles.append(ticker)
    return {"tickers": disponibles, "total": len(disponibles)}


@app.get("/api/screener")
def get_screener():
    """
    Lit les fichiers _year.csv et _cours.csv pour calculer les vrais ratios
    fondamentaux et la notation de chaque composante du CAC 40.
    Aucune valeur aléatoire — tout vient du dossier historique/.
    """
    resultats = []

    for ticker in CAC40_TICKERS:
        metrics_brutes = lire_fondamentaux(ticker)
        note, score, detail = calculer_note(metrics_brutes)

        resultats.append({
            "ticker": ticker,
            "nom": ticker.replace(".PA", "").replace(".AS", ""),
            "note": note,
            "score_num": score,
            "detail_points": detail,
            "source": "csv" if metrics_brutes else "indisponible",
            "metrics": {
                "Net_Margin":     fmt(metrics_brutes.get("Net_Margin")),
                "ROE":            fmt(metrics_brutes.get("ROE")),
                "PER":            fmt(metrics_brutes.get("PER"), 1),
                "Debt_Equity":    fmt(metrics_brutes.get("Debt_Equity")),
                "Dividend_Yield": fmt(metrics_brutes.get("Dividend_Yield")),
            },
        })

    resultats.sort(key=lambda x: x["score_num"], reverse=True)
    return {"data": resultats}


@app.get("/api/prix/{ticker}")
def get_prix(ticker: str, annees: int = 5):
    """
    Retourne la série de prix hebdomadaires pour un ticker donné.
    Calcule également les statistiques dérivées (rendement, volatilité, drawdown).
    """
    series = lire_cours(ticker, annees=annees)
    if series is None:
        raise HTTPException(status_code=404, detail=f"Données introuvables pour {ticker}")

    prices = series.values.tolist()
    dates  = series.index.strftime("%Y-%m-%d").tolist()

    # ── Statistiques ─────────────────────────────────────────────
    rets = np.diff(prices) / prices[:-1]           # rendements hebdomadaires

    ret_1y, ret_total, vol_ann, max_dd = None, None, None, None

    if len(prices) >= 2:
        ret_total = (prices[-1] / prices[0] - 1) * 100

    if len(prices) >= 52:
        ret_1y = (prices[-1] / prices[-52] - 1) * 100

    if len(rets) >= 4:
        vol_ann = float(np.std(rets) * np.sqrt(52) * 100)

    if len(prices) >= 2:
        peak, drawdown = prices[0], 0.0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak
            if dd > drawdown:
                drawdown = dd
        max_dd = float(drawdown * 100)

    return {
        "ticker": ticker,
        "dates":  dates,
        "prices": [round(p, 2) for p in prices],
        "stats": {
            "dernier_prix": round(prices[-1], 2),
            "rendement_1an":   fmt(ret_1y),
            "rendement_total": fmt(ret_total),
            "volatilite_ann":  fmt(vol_ann),
            "max_drawdown":    fmt(max_dd),
            "nb_points":       len(prices),
        },
    }


@app.get("/api/correlations")
def get_correlations(annees: int = 5):
    """
    Calcule la matrice de corrélation de Pearson des rendements hebdomadaires
    à partir des fichiers _cours.csv réels. Utilise les tickers disponibles.
    """
    # Charger tous les tickers disponibles
    series_dict = {}
    for ticker in CAC40_TICKERS:
        s = lire_cours(ticker, annees=annees)
        if s is not None:
            series_dict[ticker] = s

    if len(series_dict) < 2:
        raise HTTPException(status_code=503, detail="Données insuffisantes pour calculer les corrélations")

    # Construire le DataFrame des rendements (aligné sur les dates communes)
    prix_df = pd.concat(series_dict, axis=1).dropna()
    rendements = prix_df.pct_change().dropna()

    corr_matrix = rendements.corr()
    tickers_utilisés = list(corr_matrix.columns)
    labels = [t.replace(".PA", "").replace(".AS", "") for t in tickers_utilisés]

    # Matrice en liste de listes (JSON-sérialisable)
    mat = corr_matrix.round(3).values.tolist()

    # Paires les moins corrélées (hors diagonale)
    paires = []
    n = len(tickers_utilisés)
    for i in range(n):
        for j in range(i + 1, n):
            paires.append({
                "a": labels[i],
                "b": labels[j],
                "corr": round(float(corr_matrix.iloc[i, j]), 3),
            })
    paires.sort(key=lambda x: x["corr"])

    return {
        "tickers": labels,
        "matrice": mat,
        "paires_faibles": paires[:10],
        "nb_actifs": n,
        "nb_semaines": len(rendements),
    }


@app.get("/api/portfolio")
def get_portfolio():
    """
    Calcule le portefeuille Max Sharpe de Markowitz sur 5 ans de données réelles.
    Tout vient du dossier historique/_cours.csv — aucune simulation.
    """
    print("Optimisation Markowitz en cours…")
    series_list = []
    tickers_valides = []

    for ticker in CAC40_TICKERS:
        s = lire_cours(ticker, annees=5)
        if s is not None:
            series_list.append(s.rename(ticker))
            tickers_valides.append(ticker)

    if len(tickers_valides) < 2:
        raise HTTPException(status_code=503, detail="Pas assez de données pour l'optimisation")

    # Aligner les séries sur les dates communes
    prix_df = pd.concat(series_list, axis=1).dropna()
    rendements = prix_df.pct_change().dropna()

    mu    = rendements.mean() * 52          # rendements annualisés
    sigma = rendements.cov() * 52           # matrice de covariance annualisée
    Rf    = 0.02                            # taux sans risque OAT 10 ans

    n = len(tickers_valides)

    def neg_sharpe(w):
        ret  = np.sum(mu * w)
        vol  = np.sqrt(w @ sigma.values @ w)
        return -(ret - Rf) / vol if vol > 1e-9 else 0

    contraintes = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    bornes       = tuple((0.0, 1.0) for _ in range(n))
    w0           = np.full(n, 1.0 / n)

    res = minimize(neg_sharpe, w0, method="SLSQP", bounds=bornes, constraints=contraintes)
    w   = res.x

    # Composition (seuil > 1 %)
    composition = sorted(
        [{"ticker": tickers_valides[i], "poids": round(w[i] * 100, 2)}
         for i in range(n) if w[i] > 0.01],
        key=lambda x: x["poids"], reverse=True
    )

    ret_opti = float(np.sum(mu * w))
    vol_opti = float(np.sqrt(w @ sigma.values @ w))

    return {
        "metrics": {
            "rendement_espere": round(ret_opti * 100, 2),
            "volatilite":       round(vol_opti * 100, 2),
            "ratio_sharpe":     round((ret_opti - Rf) / vol_opti, 2),
        },
        "composition": composition,
        "nb_actifs_total": len(tickers_valides),
    }
