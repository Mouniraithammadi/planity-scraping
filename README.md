# Planity Coiffeur Scraper ✂️💈

Ce projet permet de scraper automatiquement l'ensemble des salons **Coiffeurs & Barbiers** référencés sur [Planity.com](https://www.planity.com/coiffeur/france).

---

## 📌 Informations extraites

1. **Nom de l'entreprise** (`nom`)
2. **Lien Planity** (`url`)
3. **Ville** (`ville`, `code_postal`, `adresse`)
4. **Numéro de Téléphone** (`telephone`)
5. **Email** (`email` si disponible)
6. **Website** (`website` - site externe pour extraction d'emails au prochain step)
7. **Réseaux Sociaux** (`facebook`, `instagram`)
8. **Prestations & Tarifs** (`prestations_summary` - catégories, durées et prix)
9. **Note & Nombre d'avis** (`note`, `nombre_avis`)

---

## 📁 Fichiers générés

| Fichier | Description |
|---|---|
| [planity_resultats.json](file:///c:/Users/hp/Desktop/axel/planity_resultats.json) | Export JSON structuré avec auto-sauvegarde batch |
| [planity_resultats.csv](file:///c:/Users/hp/Desktop/axel/planity_resultats.csv) | Export CSV UTF-8 avec BOM (Excel/Google Sheets) |
| [planity_resultats.xlsx](file:///c:/Users/hp/Desktop/axel/planity_resultats.xlsx) | Classeur Excel propre prêt à l'emploi |
| [planity_urls.txt](file:///c:/Users/hp/Desktop/axel/planity_urls.txt) | Index des URLs d'établissements Planity |

---

## 🚀 Utilisation sur Serveur

### 1. Installation des dépendances (Linux/Windows Server)
```bash
pip install aiohttp beautifulsoup4 pandas openpyxl
```

### 2. Exécution du scraper complet (53 961 Coiffeurs)
```bash
# Sur serveur avec concurrence élevée (ex: 50 ou 100 travailleurs simultanés)
python coiffeur_scraper.py --concurrency 50
```

### 3. Exécution en arrière-plan (Linux nohup / screen)
```bash
nohup python coiffeur_scraper.py --concurrency 100 > scraper.log 2>&1 &
```

---

## ⚙️ Options du Scraper

- `--concurrency N` : Nombre de requêtes HTTP parallèles (par défaut `50`). Sur serveur rapide, vous pouvez monter à `100`.
- `--max-urls N` : Limite optionnelle si besoin de tester un sous-ensemble.
- `--output NOM` : Nom du préfixe des fichiers (par défaut `planity_resultats`).
