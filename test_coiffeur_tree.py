import urllib.request
import json
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls_to_test = [
    'https://www.planity.com/coiffeur/france',
    'https://www.planity.com/coiffeur/47000-agen'
]

for url in urls_to_test:
    print(f"=== Fetching {url} ===")
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req).read().decode('utf-8')
        print(f"HTML length: {len(html)}")
        
        # Check links
        coiffeur_links = set(re.findall(r'href=["\'](/coiffeur/[^"\']+)["\']', html))
        print(f"Coiffeur category links found: {len(coiffeur_links)}")
        print("Sample category links:", list(coiffeur_links)[:10])
        
        # Check establishment links
        # Establishment URLs: /name-zipcode-city or similar, or full URLs
        est_links = set(re.findall(r'href=["\'](/[^"\']+)["\']', html))
        establishment_links = [
            l for l in est_links 
            if not l.startswith('/coiffeur') 
            and not l.startswith('/barbier') 
            and not l.startswith('/institut') 
            and not l.startswith('/manucure') 
            and not l.startswith('/spa')
            and not l.startswith('/tatoueur')
            and not l.startswith('/static')
            and not l.startswith('/_next')
            and not l.startswith('/api')
            and not l.startswith('/blog')
            and not l.startswith('/a-propos')
            and not l.startswith('/rejoindre')
            and not l.startswith('/mentions')
            and not l.startswith('/cgu')
            and re.search(r'\d{4,5}', l)
        ]
        print(f"Establishment links found: {len(establishment_links)}")
        print("Sample establishment links:", establishment_links[:10])

        # Check __NEXT_DATA__
        next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if next_data:
            data = json.loads(next_data.group(1))
            page_props = data.get('props', {}).get('pageProps', {})
            print("NEXT_DATA pageProps keys:", list(page_props.keys()))
            if 'establishments' in page_props:
                print("Count of establishments in pageProps:", len(page_props['establishments']))
            if 'pagination' in page_props:
                print("Pagination:", page_props['pagination'])
    except Exception as e:
        print(f"Error fetching {url}: {e}")
