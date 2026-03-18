# 📈 CGP Optimizer — CAC 40 Intelligence Platform

**CGP Optimizer** est une plateforme d'analyse financière dédiée à l'univers du **CAC 40**. Outil d'aide à la décision pour Conseillers en Gestion de Patrimoine (CGP), cette application automatise la collecte de données financières, propose un scoring fondamental, et calcule une optimisation de portefeuille basée sur la théorie moderne de Markowitz.

L'application repose sur une architecture client-serveur : un back-end **FastAPI** (Python) traite les données financières réelles extraites de **yFinance**, tandis qu'un front-end dynamique affiche les analyses et graphiques.

---

## 🔗 Accès à l'outil
**[🚀 Découvrir l'application en direct ici](https://thomashossen.github.io/cgp-optimizer/)**

---

## 🚀 Stack Technique
* **Back-end** : Python 3.9+, FastAPI, Uvicorn
* **Analyse de données** : Pandas, NumPy, SciPy (Optimisation SLSQP)
* **Data Source** : yFinance API (Données réelles)
* **Front-end** : HTML5, CSS3, JavaScript, Chart.js
* **DevOps (CI/CD)** : GitHub Actions (Scraping auto), Render (Hébergement API), GitHub Pages (Hébergement Front)

---

## 📋 Architecture & Fonctionnalités

La plateforme est organisée en six modules clés alimentés par l'API REST :

| Onglet | Contenu | Source des données |
| :--- | :--- | :--- |
| **① Tableau de bord** | KPIs globaux, distribution des notes, top/flop 5. | API `/screener` |
| **② Screener Fondamental**| Ratios financiers, notation AAA→B, détails par action. | Fichiers `_year.csv` |
| **③ Notation & Rating** | Grille de scoring multicritère détaillée. | Algorithme Python |
| **④ Données Historiques** | Prix hebdo, volatilité, drawdown, distribution. | Fichiers `_cours.csv` |
| **⑤ Matrice de Corrélation**| Corrélations de Pearson pour la diversification. | API `/correlations` |
| **⑥ Portefeuille Optimal** | Markowitz Max Sharpe & Frontière efficiente. | API `/portfolio` |

---

## ⚙️ Automatisation Totale (CI/CD)

Le projet est entièrement autonome grâce à une chaîne d'intégration continue :
1. **GitHub Actions** : Un script planifié (`cron`) s'exécute chaque lundi à minuit pour télécharger les dernières données boursières via yFinance.
2. **Stockage Auto** : Les nouveaux fichiers CSV sont automatiquement commitiés sur le dépôt GitHub.
3. **Deploy Hook** : GitHub notifie **Render** via un Webhook pour redéployer l'API avec les données fraîches.
4. **Mise à jour Live** : Le site web affiche les données de la semaine sans aucune intervention manuelle.

---

## 📊 Méthodologie de Scoring (0 à 100 pts)

Le score est calculé selon cinq critères financiers (20 pts chacun) :
* **Rentabilité** : Marge nette (> 15%) & ROE (> 15%).
* **Valorisation** : PER (idéal entre 10x et 25x).
* **Solvabilité** : Ratio Dette / Capitaux Propres (< 0,5x).
* **Dividende** : Rendement (> 4%).

**Grille de Rating :**
* **AAA (≥ 80 pts)** : Qualité exceptionnelle (Cœur de portefeuille).
* **A (50-64 pts)** : Bonne qualité.
* **BBB (35-49 pts)** : Qualité correcte.
* **B (< 20 pts)** : Profil dégradé.

---

## 📉 Optimisation de Markowitz

L'optimisation repose sur les rendements hebdomadaires des 5 dernières années. Le solveur **SLSQP** cherche à maximiser le **Ratio de Sharpe** en ajustant les poids de chaque actif sous contrainte de somme égale à 100%.
* **Taux sans risque (Rf)** : 2% (OAT 10 ans).
* **Frontière efficiente** : Simulation de Monte Carlo (2 000 points) générée côté front-end pour la visualisation.

---

## 🛠️ Installation Locale (Pour les développeurs)

### 1. Prérequis
```bash```
```pip install fastapi uvicorn pandas numpy scipy yfinance```

### 2. Initialisation des données (Optionnel si CSV déjà présents)
```python scrapper_yfinance_cours.py```
```python scrapper_yfinance_macro.py```

### 3. Lancement du Serveur
```uvicorn main:app --reload```
