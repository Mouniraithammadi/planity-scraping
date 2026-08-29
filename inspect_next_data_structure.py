import urllib.request
import json
import re

url = 'https://www.planity.com/adivinange-latelier-coiffure-trets-13530'
headers = {'User-Agent': 'Mozilla/5.0'}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode('utf-8')

next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if next_data:
    data = json.loads(next_data.group(1))
    print("Top keys:", data.keys())
    page_props = data.get('props', {}).get('pageProps', {})
    print("pageProps keys:", page_props.keys())
    for k in page_props:
        print(f"Key: {k}, type: {type(page_props[k])}")
else:
    print("NEXT_DATA script not found")
