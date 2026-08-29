import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# User provided city links
SEED_LINKS = [
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

async def test_crawl():
    visited_cat = set()
    found_est = set()
    queue = ["https://www.planity.com" + link for link in SEED_LINKS[:5]]

    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for url in queue:
            visited_cat.add(url)
            try:
                async with session.get(url, headers=HEADERS, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors='ignore')
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find establishment links
                        for a in soup.find_all('a', href=True):
                            href = a['href']
                            if href.startswith('/'):
                                full_url = "https://www.planity.com" + href
                            else:
                                full_url = href
                                
                            if full_url.startswith("https://www.planity.com/"):
                                path = full_url.replace("https://www.planity.com/", "")
                                if path.startswith("coiffeur/"):
                                    pass # Category or sub-city
                                elif not any(path.startswith(x) for x in ['barbier', 'institut', 'manucure', 'spa', 'tatoueur', 'static', '_next', 'api', 'blog', 'a-propos', 'rejoindre', 'mentions', 'cgu']):
                                    if re.search(r'\d{4,5}', path):
                                        found_est.add(full_url)
                        print(f"URL {url}: Found {len(found_est)} establishments total so far.")
            except Exception as e:
                print(f"Error {url}: {e}")

    print(f"Total establishment URLs found from top 5 cities: {len(found_est)}")

asyncio.run(test_crawl())
