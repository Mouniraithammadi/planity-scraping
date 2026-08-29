import urllib.request
import json
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

url = 'https://www.planity.com/coiffeur/13080-aix-en-provence'
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req).read().decode('utf-8')

next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if next_data:
    data = json.loads(next_data.group(1))
    page_props = data.get('props', {}).get('pageProps', {})
    print("Keys in pageProps:", list(page_props.keys()))
    
    # Check establishments array if any
    ests = page_props.get('establishments', [])
    print(f"Establishments count in NEXT_DATA: {len(ests)}")
    if ests:
        print("Sample establishment keys:", list(ests[0].keys()))
        print("Sample establishment data:", json.dumps(ests[0], indent=2, ensure_ascii=False)[:1000])

    # Check searchResult / pagination / meta
    for k in page_props:
        if 'search' in k.lower() or 'page' in k.lower() or 'pagi' in k.lower() or 'meta' in k.lower() or 'total' in k.lower():
            print(f"Key {k}:", page_props[k])

# Check if there is pagination on the page HTML (e.g. page 2, page 3, next page links)
pagination_links = re.findall(r'href=["\'](/coiffeur/[^"\']*\?page=\d+)[ "\']', html)
print("Pagination links with ?page=:", pagination_links)

pagination_links2 = re.findall(r'href=["\'](/coiffeur/[^"\']+)["\']', html)
print("Other category links count:", len(pagination_links2))
page_links = [l for l in pagination_links2 if 'page' in l or 'p=' in l or re.search(r'-\d+$', l)]
print("Page-like links:", page_links[:10])
