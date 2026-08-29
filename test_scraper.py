import urllib.request
import re
import json
import concurrent.futures
import time
from bs4 import BeautifulSoup

def get_establishment_urls():
    urls = []
    # Collect establishment URLs from Sitemap-8 and Sitemap-9
    for sm_id in [8, 9]:
        sm_url = f"https://www.planity.com/sitemap-{sm_id}.xml"
        req = urllib.request.Request(sm_url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            content = urllib.request.urlopen(req).read().decode('utf-8')
            locs = re.findall(r'<loc>(.*?)</loc>', content)
            for u in locs:
                # Est URLs don't have subcategory slashes in French
                if u.count('/') == 3 and not any(u.startswith(f"https://www.planity.com/{lang}") for lang in ['de-DE', 'nl-BE', 'en-GB', 'es-ES']):
                    urls.append(u)
        except Exception as e:
            print(f"Error fetching sitemap {sm_id}: {e}")
    return urls

def extract_planity_establishment(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
    except Exception as e:
        return {'url': url, 'error': str(e)}

    data = {
        'url': url,
        'nom': None,
        'ville': None,
        'code_postal': None,
        'adresse': None,
        'telephone': None,
        'email': None,
        'prestations': [],
        'note': None,
        'nombre_avis': None
    }

    # 1. Extract JSON-LD
    json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for jld in json_ld_matches:
        try:
            ld = json.loads(jld)
            if ld.get('@type') in ['HealthAndBeautyBusiness', 'BeautySalon', 'HairSalon', 'LocalBusiness']:
                data['nom'] = ld.get('name')
                data['telephone'] = ld.get('telephone')
                addr = ld.get('address', {})
                if isinstance(addr, dict):
                    data['adresse'] = addr.get('streetAddress')
                    data['ville'] = addr.get('addressLocality')
                    data['code_postal'] = addr.get('postalCode')
                agg = ld.get('aggregateRating', {})
                if isinstance(agg, dict):
                    data['note'] = agg.get('ratingValue')
                    data['nombre_avis'] = agg.get('reviewCount')
        except Exception:
            pass

    # Fallback for Nom
    if not data['nom']:
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I)
        if title_match:
            data['nom'] = title_match.group(1).split('|')[0].strip()

    # 2. Extract Email if present
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
    # Exclude common static asset or domain emails if any
    clean_emails = [e for e in emails if not any(domain in e for domain in ['planity.com', 'schema.org', 'sentry.io', 'example.com', 'w3.org'])]
    if clean_emails:
        data['email'] = ', '.join(clean_emails)

    # 3. Extract Prestations (Services & Prices)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Prestations extraction: Find headers and service items
    prestations_list = []
    
    # Try finding categories and service items in DOM
    # Planity structure: category headings and service items with name, duration, price
    current_category = "Général"
    for element in soup.find_all(['h2', 'h3', 'div']):
        if element.name in ['h2', 'h3']:
            txt = element.get_text(strip=True)
            if txt and len(txt) < 100 and not any(skip in txt for skip in ['Horaires', 'Avis', 'Informations', 'Où se situe', 'Collaborateurs', 'À-propos']):
                current_category = txt
        
        # Check if element represents a service line
        if element.name == 'div':
            txt = element.get_text(" ", strip=True)
            # Match service pattern e.g. "Coupe Homme 20min 25 €"
            if '€' in txt and ('min' in txt or 'h' in txt) and len(txt) < 180 and 'Avis' not in txt and 'Voir les' not in txt:
                # Avoid duplicate parent/child text
                if not any(txt in existing for existing in prestations_list):
                    prestations_list.append(f"[{current_category}] {txt}")

    # Deduplicate prestations while preserving order
    unique_prestations = []
    for p in prestations_list:
        if not any(p in u or u in p for u in unique_prestations):
            unique_prestations.append(p)
            
    data['prestations'] = unique_prestations[:30] # Keep top 30
    return data

if __name__ == "__main__":
    print("Collecting URLs from sitemap...")
    all_urls = get_establishment_urls()
    print(f"Total establishment URLs found: {len(all_urls)}")

    sample_urls = all_urls[:20]
    print(f"Testing extraction on {len(sample_urls)} samples...")

    start_t = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(extract_planity_establishment, url) for url in sample_urls]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            results.append(res)
            print(f"Scraped: {res.get('nom')} | Ville: {res.get('ville')} | Tel: {res.get('telephone')} | Prestations: {len(res.get('prestations', []))}")

    print(f"Time taken for 20 URLs: {time.time() - start_t:.2f}s")
    
    with open("sample_scraped.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
