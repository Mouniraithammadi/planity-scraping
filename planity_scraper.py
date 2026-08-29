"""
Planity Scraper - Scrape le maximum d'établissements sur Planity.com
Information extraites:
- Nom de l'entreprise
- Lien Planity
- Prestations (liste complète des services, catégories, durées et tarifs)
- Ville (et Code Postal / Adresse)
- Email (si présent)
- Numéro de téléphone
- Note moyenne & Nombre d'avis
"""

import asyncio
import aiohttp
import re
import json
import csv
import sys
import time
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

# Ensure stdout supports unicode without crashing on Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

SITEMAP_INDEX_URL = "https://www.planity.com/sitemap.xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

GENERIC_CATEGORIES = {
    'https://www.planity.com/coiffeur',
    'https://www.planity.com/barbier',
    'https://www.planity.com/manucure-et-pedicure',
    'https://www.planity.com/institut-de-beaute',
    'https://www.planity.com/coach-de-vie',
    'https://www.planity.com/spa',
    'https://www.planity.com/tatoueur'
}

def is_establishment_url(url):
    if url in GENERIC_CATEGORIES:
        return False
    if any(url.startswith(f"https://www.planity.com/{lang}") for lang in ['de-DE', 'nl-BE', 'en-GB', 'es-ES']):
        return False
    # Establishment URLs on Planity end with slug containing zipcode or name-city-zipcode
    # e.g., https://www.planity.com/corps-a-coeur-83980-le-lavandou
    parts = url.replace('https://www.planity.com/', '').split('/')
    if len(parts) == 1 and parts[0]:
        # Check if slug contains numbers (postal code or ID) or dashes
        slug = parts[0]
        if re.search(r'\d{4,5}', slug) or '-' in slug:
            return True
    return False

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def parse_establishment_html(html, url):
    data = {
        "nom": None,
        "url": url,
        "ville": None,
        "code_postal": None,
        "adresse": None,
        "telephone": None,
        "email": None,
        "prestations": [],
        "prestations_summary": "",
        "note": None,
        "nombre_avis": None
    }

    # 1. JSON-LD Extraction
    json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for jld in json_ld_matches:
        try:
            ld = json.loads(jld)
            if isinstance(ld, dict) and ld.get('@type') in ['HealthAndBeautyBusiness', 'BeautySalon', 'HairSalon', 'LocalBusiness', 'MedicalBusiness']:
                data["nom"] = clean_text(ld.get("name"))
                data["telephone"] = clean_text(ld.get("telephone"))
                
                addr = ld.get("address", {})
                if isinstance(addr, dict):
                    data["adresse"] = clean_text(addr.get("streetAddress"))
                    data["ville"] = clean_text(addr.get("addressLocality"))
                    data["code_postal"] = clean_text(addr.get("postalCode"))
                    
                agg = ld.get("aggregateRating", {})
                if isinstance(agg, dict):
                    data["note"] = agg.get("ratingValue")
                    data["nombre_avis"] = agg.get("reviewCount")
        except Exception:
            pass

    # Fallback for Nom
    if not data["nom"]:
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I)
        if title_match:
            title = title_match.group(1).split('|')[0].split('-')[0].strip()
            data["nom"] = title

    # 2. Email extraction
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
    valid_emails = [
        e for e in emails 
        if not any(domain in e.lower() for domain in ['planity.com', 'schema.org', 'sentry.io', 'w3.org', 'example.com', 'facebook.com', 'instagram.com'])
    ]
    if valid_emails:
        data["email"] = ", ".join(valid_emails)

    # 3. Prestations extraction (Services, Categories, Prices, Durations)
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    current_cat = "Général"

    for elem in soup.find_all(['h2', 'h3', 'div']):
        if elem.name in ['h2', 'h3']:
            txt = elem.get_text(strip=True)
            if txt and len(txt) < 80 and not any(k in txt.lower() for k in ['horaire', 'avis', 'information', 'où se situe', 'collaborateur', 'à-propos', 'réserver', 'dans cet']):
                current_cat = clean_text(txt)
        elif elem.name == 'div':
            text = elem.get_text(" | ", strip=True)
            if '€' in text and ('min' in text or 'h' in text) and len(text) < 300:
                clean = re.sub(r'Choisir', '', text)
                clean = re.sub(r'Cette prestation ne peut pas être réservée en ligne\.', '', clean)
                clean = re.sub(r'\s+', ' ', clean).strip(' |')
                clean = re.sub(r'\|\s*\|+', '|', clean)

                # Ensure it's not a generic container or button
                text_without_price_dur = re.sub(r'\b\d+\s*min\b|\b\d+\s*h\s*\d*m?i?n?\b|\d+\s*€|à partir de|de|à|\||\s+', '', clean, flags=re.I)
                if len(text_without_price_dur) >= 3 and any(c.isalpha() for c in text_without_price_dur):
                    formatted = f"[{current_cat}] {clean}"
                    if not any(skip in clean.lower() for skip in ['voir les', 'prendre rdv', 'avis', 'carte bancaire']):
                        results.append(formatted)

    # Deduplicate while preserving order
    final_prestations = []
    for r in results:
        if not any(r == existing or (r in existing and len(r) < len(existing)) for existing in final_prestations):
            final_prestations.append(r)

    data["prestations"] = final_prestations
    data["prestations_summary"] = " ; ".join(final_prestations)

    return data

async def fetch_sitemap_urls(session):
    print("Recherche des sitemaps sur planity.com...")
    urls = []
    sitemap_list = [f"https://www.planity.com/sitemap-{i}.xml" for i in range(10)]
    
    async def process_sitemap(sm_url):
        try:
            async with session.get(sm_url, headers=HEADERS, timeout=30) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    locs = re.findall(r'<loc>(.*?)</loc>', text)
                    est_urls = [u for u in locs if is_establishment_url(u)]
                    print(f"  -> {sm_url}: {len(est_urls)} établissements trouvés sur {len(locs)} URLs")
                    return est_urls
        except Exception as e:
            print(f"  -> Erreur sur {sm_url}: {e}")
        return []

    results = await asyncio.gather(*[process_sitemap(url) for url in sitemap_list])
    for res in results:
        urls.extend(res)

    unique_urls = list(dict.fromkeys(urls))
    print(f"Total d'établissements uniques trouvés: {len(unique_urls)}")
    
    with open("planity_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(unique_urls))
    return unique_urls

async def scrape_batch(urls, concurrency=25):
    connector = aiohttp.TCPConnector(limit=concurrency, ssl=False)
    timeout = aiohttp.ClientTimeout(total=20)
    results = []
    completed = 0
    total = len(urls)
    start_time = time.time()

    semaphore = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async def fetch_and_parse(url):
            nonlocal completed
            async with semaphore:
                for attempt in range(3):
                    try:
                        async with session.get(url, headers=HEADERS) as resp:
                            if resp.status == 200:
                                html = await resp.text(errors='ignore')
                                res = parse_establishment_html(html, url)
                                completed += 1
                                if completed % 20 == 0 or completed == total:
                                    elapsed = time.time() - start_time
                                    speed = completed / elapsed if elapsed > 0 else 0
                                    print(f"Progression: [{completed}/{total}] {completed/total*100:.1f}% | Vitesse: {speed:.1f} pages/sec", end='\r', flush=True)
                                return res
                            elif resp.status == 429:
                                await asyncio.sleep(2 * (attempt + 1))
                    except Exception:
                        await asyncio.sleep(1)
                completed += 1
                return {"url": url, "error": "Failed after 3 retries"}

        tasks = [fetch_and_parse(url) for url in urls]
        results = await asyncio.gather(*tasks)

    print()
    return [r for r in results if "error" not in r and r.get("nom") and r.get("nom") != "Planity"]

def save_exports(data, prefix="planity_resultats"):
    json_file = f"{prefix}.json"
    csv_file = f"{prefix}.csv"
    xlsx_file = f"{prefix}.xlsx"

    # 1. JSON Export
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" Export JSON : [planity_resultats.json](file:///{Path(json_file).absolute()}) ({len(data)} établissements)")

    # 2. CSV Export
    fieldnames = ["nom", "url", "ville", "code_postal", "adresse", "telephone", "email", "prestations_summary", "note", "nombre_avis"]
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for item in data:
            writer.writerow(item)
    print(f" Export CSV  : [planity_resultats.csv](file:///{Path(csv_file).absolute()})")

    # 3. Excel Export
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        if "prestations" in df.columns:
            df_excel = df.drop(columns=["prestations"])
        else:
            df_excel = df
        df_excel.to_excel(xlsx_file, index=False)
        print(f" Export Excel: [planity_resultats.xlsx](file:///{Path(xlsx_file).absolute()})")
    except Exception as e:
        print(f" Export Excel ignoré: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Scraper Planity.com")
    parser.add_argument("--max-urls", type=int, default=None, help="Nombre max d'établissements à scraper (ex: 100, 1000, 5000)")
    parser.add_argument("--concurrency", type=int, default=25, help="Nombre de requêtes simultanées (default: 25)")
    parser.add_argument("--output", type=str, default="planity_resultats", help="Nom des fichiers de sortie")
    args = parser.parse_args()

    print("============================================================")
    print(" SCRAPER PLANITY.COM")
    print("============================================================")

    urls_file = Path("planity_urls.txt")
    if urls_file.exists():
        print("Chargement des URLs d'établissements depuis planity_urls.txt...")
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if is_establishment_url(line.strip())]
        print(f" -> {len(urls)} URLs d'établissements chargées.")
    else:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            urls = await fetch_sitemap_urls(session)

    if args.max_urls:
        print(f"Limite appliquée: {args.max_urls} établissements sur {len(urls)} disponibles.")
        urls = urls[:args.max_urls]

    print(f"\nLancement du scraping de {len(urls)} établissements (concurrence = {args.concurrency})...")
    start_t = time.time()
    results = await scrape_batch(urls, concurrency=args.concurrency)
    duration = time.time() - start_t

    print(f"\nScraping terminé en {duration:.2f} secondes ({len(results)} établissements scrapés) !")

    print("\nGénération des fichiers d'exportation...")
    save_exports(results, prefix=args.output)
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(main())
