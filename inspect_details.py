import json
import re
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open('sample_establishment.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("HTML length:", len(html))

# Check for JSON-LD
json_lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print("JSON-LD count:", len(json_lds))
for i, jld in enumerate(json_lds):
    try:
        data = json.loads(jld)
        print(f"--- JSON-LD {i} ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error reading json ld:", e)

soup = BeautifulSoup(html, 'html.parser')
next_data = soup.find('script', id='__NEXT_DATA__')
if next_data:
    print("Found __NEXT_DATA__")
    try:
        data = json.loads(next_data.string)
        print("NEXT_DATA keys:", data.keys())
        page_props = data.get('props', {}).get('pageProps', {})
        print("pageProps keys:", page_props.keys())
        # Print top level keys of pageProps
        for k, v in page_props.items():
            if isinstance(v, dict):
                print(f"Key {k} dict keys:", v.keys())
            elif isinstance(v, list):
                print(f"Key {k} list length:", len(v))
            else:
                print(f"Key {k}:", str(v)[:100])
    except Exception as e:
        print("Error parsing NEXT_DATA:", e)

# Search for any text containing website, site, http, www, email, etc.
print("Searching for website/site/email in NEXT_DATA text...")
if next_data:
    nd_str = next_data.string
    # find keys related to website, site, email, url, social
    matches = re.findall(r'"([^"]*(?:website|site|email|url|facebook|instagram|social)[^"]*)":\s*("[^"]*")', nd_str, re.IGNORECASE)
    print("Found matches in NEXT_DATA:", len(matches))
    for m in set(matches[:30]):
        print("  ", m)
