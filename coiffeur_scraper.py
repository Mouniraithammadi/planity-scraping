"""
Planity Coiffeur Scraper - Scrape ALL Coiffeur establishments across France
Filters strictly for Coiffeur / Hair salons.
Extracts:
- Nom de l'entreprise
- URL Planity
- Ville, Code Postal, Adresse
- Numéro de Téléphone
- Email (extracted from page)
- Website (Official site / external URL for future email extraction)
- Facebook & Instagram social URLs
- Prestations / Services summary
- Note & Nombre d'avis

Saves incrementally batch-by-batch (every 200 items).
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

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

SEED_CITY_LINKS = [
    "/coiffeur/france",
    "/coiffeur/47000-agen", "/coiffeur/13080-aix-en-provence", "/coiffeur/20000-ajaccio", "/coiffeur/81990-albi",
    "/coiffeur/61000-alencon", "/coiffeur/80000-amiens", "/coiffeur/49000-angers", "/coiffeur/16000-angouleme",
    "/coiffeur/74000-annecy", "/coiffeur/07100-annonay", "/coiffeur/95100-argenteuil", "/coiffeur/32810-auch",
    "/coiffeur/15000-aurillac", "/coiffeur/89000-auxerre", "/coiffeur/84000-avignon", "/coiffeur/20200-bastia",
    "/coiffeur/60155-beauvais", "/coiffeur/90000-belfort", "/coiffeur/25000-besancon", "/coiffeur/41000-blois",
    "/coiffeur/92100-boulogne-billancourt", "/coiffeur/01000-bourg-en-bresse", "/coiffeur/18000-bourges", "/coiffeur/19100-brive-la-gaillarde",
    "/coiffeur/14000-caen", "/coiffeur/46000-cahors", "/coiffeur/62100-calais", "/coiffeur/97300-cayenne",
    "/coiffeur/71100-chalon-sur-saone", "/coiffeur/73000-chambery", "/coiffeur/08090-charleville-mezieres", "/coiffeur/28000-chartres",
    "/coiffeur/36000-chateauroux", "/coiffeur/77500-chelles", "/coiffeur/50100-cherbourg-octeville", "/coiffeur/63000-clermont-ferrand",
    "/coiffeur/91100-corbeil-essonnes", "/coiffeur/94000-creteil", "/coiffeur/21000-dijon", "/coiffeur/39100-dole",
    "/coiffeur/88000-epinal", "/coiffeur/27000-evreux", "/coiffeur/05000-gap", "/coiffeur/38000-grenoble",
    "/coiffeur/23000-gueret", "/coiffeur/85000-la-roche-sur-yon", "/coiffeur/53000-laval", "/coiffeur/76600-le-havre",
    "/coiffeur/72000-le-mans", "/coiffeur/43000-le-puy-en-velay", "/coiffeur/87000-limoges", "/coiffeur/56100-lorient",
    "/coiffeur/04100-manosque", "/coiffeur/48000-mende", "/coiffeur/57000-metz", "/coiffeur/40000-mont-de-marsan",
    "/coiffeur/82000-montauban", "/coiffeur/03100-montlucon", "/coiffeur/68100-mulhouse", "/coiffeur/54100-nancy",
    "/coiffeur/44000-nantes", "/coiffeur/58000-nevers", "/coiffeur/30000-nimes", "/coiffeur/79000-niort",
    "/coiffeur/45000-orleans", "/coiffeur/09100-pamiers", "/coiffeur/64000-pau", "/coiffeur/24000-perigueux",
    "/coiffeur/66000-perpignan", "/coiffeur/86000-poitiers", "/coiffeur/51100-reims", "/coiffeur/35000-rennes",
    "/coiffeur/12000-rodez", "/coiffeur/22000-saint-brieuc", "/coiffeur/93200-saint-denis", "/coiffeur/52100-saint-dizier",
    "/coiffeur/42000-saint-etienne", "/coiffeur/97150-saint-martin", "/coiffeur/02100-saint-quentin", "/coiffeur/65000-tarbes",
    "/coiffeur/83000-toulon", "/coiffeur/37000-tours", "/coiffeur/10000-troyes", "/coiffeur/26000-valence",
    "/coiffeur/55100-verdun", "/coiffeur/78000-versailles", "/coiffeur/70000-vesoul", "/coiffeur/69100-villeurbanne"
]

TRACKING_DOMAINS = [
    'planity.com', 'planityapp.com', 'planity.services', 'cloudfront.net',
    'schema.org', 'w3.org', 'google.', 'googletagmanager', 'google-analytics',
    'sentry.io', 'didomi.io', 'topsort.com', 'cloudinary.com', 'onelink.me',
    'apple.com', 'facebook.net', 'facebook.com/tr', 'hotjar.com', 'gstatic.com',
    'doubleclick.net', 'connect.facebook.net', 'criteo.com', 'hotjar-', 'tiktok.com'
]

COIFFEUR_KEYWORDS = [
    'coiffeur', 'coiffure', 'barbier', 'barber', 'cheveux', 'coupe', 'shampooing',
    'brushing', 'coloration', 'balayage', 'mèches', 'meches', 'barbe', 'permanent',
    'patine', 'chignon', 'lissages', 'lissage', 'hair'
]

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def is_coiffeur_establishment(html, url, ld_data, soup):
    if '/coiffeur' in url:
        return True
    if isinstance(ld_data, dict):
        ld_type = ld_data.get('@type')
        if ld_type == 'HairSalon':
            return True
    if 'mainType":"hair_care"' in html or 'mainType":"barber"' in html:
        return True
    breads = [a.get_text(strip=True).lower() for a in soup.find_all('a') if '/coiffeur' in a.get('href', '') or 'coiffeur' in a.get_text().lower()]
    if breads:
        return True
    html_lower = html.lower()
    matches = sum(1 for kw in COIFFEUR_KEYWORDS if kw in html_lower)
    if matches >= 2:
        return True
    return False

def parse_coiffeur_page(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    
    ld_data = {}
    json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for jld in json_ld_matches:
        try:
            ld = json.loads(jld)
            if isinstance(ld, dict) and ld.get('@type') in ['HealthAndBeautyBusiness', 'BeautySalon', 'HairSalon', 'LocalBusiness', 'MedicalBusiness']:
                ld_data = ld
                break
        except Exception:
            pass

    if not is_coiffeur_establishment(html, url, ld_data, soup):
        return None

    data = {
        "nom": None,
        "url": url,
        "ville": None,
        "code_postal": None,
        "adresse": None,
        "telephone": None,
        "email": None,
        "website": None,
        "facebook": None,
        "instagram": None,
        "prestations_summary": "",
        "note": None,
        "nombre_avis": None
    }

    if ld_data:
        data["nom"] = clean_text(ld_data.get("name"))
        data["telephone"] = clean_text(ld_data.get("telephone"))
        
        addr = ld_data.get("address", {})
        if isinstance(addr, dict):
            data["adresse"] = clean_text(addr.get("streetAddress"))
            data["ville"] = clean_text(addr.get("addressLocality"))
            data["code_postal"] = clean_text(addr.get("postalCode"))
            
        agg = ld_data.get("aggregateRating", {})
        if isinstance(agg, dict):
            data["note"] = agg.get("ratingValue")
            data["nombre_avis"] = agg.get("reviewCount")

    if not data["nom"]:
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I)
        if title_match:
            title = title_match.group(1).split('|')[0].split('-')[0].strip()
            data["nom"] = title

    if not data["telephone"]:
        phone_match = re.search(r'"phoneNumber":"(\+?\d[\d\s]+)"', html)
        if phone_match:
            data["telephone"] = phone_match.group(1).strip()

    # Emails
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
    valid_emails = [
        e for e in emails 
        if not any(d in e.lower() for d in TRACKING_DOMAINS)
    ]
    if valid_emails:
        data["email"] = ", ".join(sorted(valid_emails))

    # Websites & Social Links (Cleaned)
    raw_websites = []
    facebook_pages = []
    instagram_profiles = []

    if ld_data:
        same_as = ld_data.get("sameAs", [])
        if isinstance(same_as, str):
            same_as = [same_as]
        for s in same_as:
            if isinstance(s, str) and s.startswith('http'):
                s_lower = s.lower()
                if 'facebook.com' in s_lower and '/tr?' not in s_lower:
                    facebook_pages.append(s)
                elif 'instagram.com' in s_lower:
                    instagram_profiles.append(s)
                elif not any(tr in s_lower for tr in TRACKING_DOMAINS):
                    raw_websites.append(s)

        u = ld_data.get("url")
        if u and isinstance(u, str) and u != url and u.startswith('http'):
            if not any(tr in u.lower() for tr in TRACKING_DOMAINS):
                raw_websites.append(u)

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        href_lower = href.lower()
        if href_lower.startswith('http'):
            if any(tr in href_lower for tr in TRACKING_DOMAINS):
                continue
            if 'facebook.com' in href_lower and '/tr?' not in href_lower:
                facebook_pages.append(href)
            elif 'instagram.com' in href_lower:
                instagram_profiles.append(href)
            else:
                raw_websites.append(href)

    def format_clean_list(links):
        res = []
        for l in links:
            l = l.strip().rstrip('\\').rstrip('/')
            if l and l not in res:
                res.append(l)
        return ", ".join(res) if res else None

    data["website"] = format_clean_list(raw_websites)
    data["facebook"] = format_clean_list(facebook_pages)
    data["instagram"] = format_clean_list(instagram_profiles)

    # Prestations
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

                text_without_price_dur = re.sub(r'\b\d+\s*min\b|\b\d+\s*h\s*\d*m?i?n?\b|\d+\s*€|à partir de|de|à|\||\s+', '', clean, flags=re.I)
                if len(text_without_price_dur) >= 3 and any(c.isalpha() for c in text_without_price_dur):
                    formatted = f"[{current_cat}] {clean}"
                    if not any(skip in clean.lower() for skip in ['voir les', 'prendre rdv', 'avis', 'carte bancaire']):
                        results.append(formatted)

    final_prestations = []
    for r in results:
        if not any(r == existing or (r in existing and len(r) < len(existing)) for existing in final_prestations):
            final_prestations.append(r)

    data["prestations_summary"] = " ; ".join(final_prestations)

    return data

async def discover_urls_from_seed(session):
    print("Scan rapide de l'arborescence coiffeurs (villes & catégories)...")
    found_est_urls = set()
    sem = asyncio.Semaphore(25)

    async def fetch_city_page(link):
        url = "https://www.planity.com" + link if link.startswith('/') else link
        async with sem:
            try:
                async with session.get(url, headers=HEADERS, timeout=12) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors='ignore')
                        soup = BeautifulSoup(html, 'html.parser')
                        for a in soup.find_all('a', href=True):
                            href = a['href'].strip()
                            path = href.replace("https://www.planity.com/", "") if href.startswith("https://www.planity.com/") else href.lstrip('/')
                            if not path.startswith("coiffeur") and not any(path.startswith(x) for x in ['barbier', 'institut', 'manucure', 'spa', 'tatoueur', 'static', '_next', 'api', 'blog', 'a-propos', 'rejoindre', 'mentions', 'cgu']):
                                if re.search(r'\d{4,5}', path):
                                    full_url = "https://www.planity.com/" + path
                                    found_est_urls.add(full_url)
            except Exception:
                pass

    tasks = [fetch_city_page(link) for link in SEED_CITY_LINKS]
    await asyncio.gather(*tasks)
    print(f" -> {len(found_est_urls)} URLs de coiffeurs découvertes via les villes.")
    return found_est_urls

def load_sitemap_urls():
    urls_file = Path("planity_urls.txt")
    if urls_file.exists():
        with open(urls_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not any(line.strip().startswith(f"https://www.planity.com/{x}") for x in ['barbier', 'institut', 'manucure', 'spa', 'tatoueur'])]
    return []

def save_exports(data, prefix="planity_resultats", quiet=False):
    json_file = f"{prefix}.json"
    csv_file = f"{prefix}.csv"
    xlsx_file = f"{prefix}.xlsx"

    # 1. JSON Export
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 2. CSV Export
    fieldnames = ["nom", "url", "ville", "code_postal", "adresse", "telephone", "email", "website", "facebook", "instagram", "prestations_summary", "note", "nombre_avis"]
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for item in data:
            writer.writerow(item)

    # 3. Excel Export
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_excel(xlsx_file, index=False)
    except Exception:
        pass

    if not quiet:
        print(f"\n [AUTO-SAVE] Export mis à jour : {len(data)} coiffeurs sauvegardés dans {json_file}, {csv_file}, {xlsx_file}")

async def scrape_coiffeurs(urls, concurrency=50, prefix="planity_resultats"):
    connector = aiohttp.TCPConnector(limit=concurrency, ssl=False)
    timeout = aiohttp.ClientTimeout(total=20)
    completed = 0
    total = len(urls)
    start_time = time.time()
    valid_results = []

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
                                res = parse_coiffeur_page(html, url)
                                completed += 1
                                if res and res.get("nom") and res.get("nom") != "Planity":
                                    valid_results.append(res)

                                # Auto-save batch every 200 items scraped
                                if len(valid_results) > 0 and len(valid_results) % 200 == 0:
                                    save_exports(valid_results, prefix=prefix, quiet=True)

                                if completed % 50 == 0 or completed == total:
                                    elapsed = time.time() - start_time
                                    speed = completed / elapsed if elapsed > 0 else 0
                                    print(f"Scraping Coiffeurs: [{completed}/{total}] {completed/total*100:.1f}% | Coiffeurs extraits: {len(valid_results)} | Vitesse: {speed:.1f} p/s", end='\r', flush=True)
                                return res
                            elif resp.status == 429:
                                await asyncio.sleep(2 * (attempt + 1))
                    except Exception:
                        await asyncio.sleep(1)
                completed += 1
                return None

        tasks = [fetch_and_parse(url) for url in urls]
        await asyncio.gather(*tasks)

    print()
    # Final save
    save_exports(valid_results, prefix=prefix, quiet=False)
    return valid_results

async def main():
    parser = argparse.ArgumentParser(description="Scraper Coiffeurs Planity.com")
    parser.add_argument("--max-urls", type=int, default=None, help="Nombre max de coiffeurs à scraper")
    parser.add_argument("--concurrency", type=int, default=50, help="Nombre de requêtes simultanées")
    parser.add_argument("--output", type=str, default="planity_resultats", help="Nom des fichiers de sortie")
    args = parser.parse_args()

    print("============================================================")
    print(" SCRAPER COIFFEURS PLANITY.COM (FRANCE)")
    print("============================================================")

    # 1. Load Sitemap candidate URLs
    sitemap_urls = load_sitemap_urls()
    print(f"URLs issues du sitemap: {len(sitemap_urls)}")

    # 2. Fast scan of city tree
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tree_urls = await discover_urls_from_seed(session)

    # Merge & deduplicate
    all_candidate_urls = list(dict.fromkeys(list(tree_urls) + sitemap_urls))
    print(f"Total URLs uniques de salons à vérifier/scraper: {len(all_candidate_urls)}")

    if args.max_urls:
        print(f"Limite max appliquée: {args.max_urls} URLs")
        all_candidate_urls = all_candidate_urls[:args.max_urls]

    print(f"\nLancement du scraping avec auto-sauvegarde par batch (concurrence = {args.concurrency})...")
    start_t = time.time()
    results = await scrape_coiffeurs(all_candidate_urls, concurrency=args.concurrency, prefix=args.output)
    duration = time.time() - start_t

    print(f"\nScraping terminé en {duration:.2f} secondes ({len(results)} Coiffeurs validés et extraits) !")
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(main())
