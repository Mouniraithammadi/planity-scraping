import urllib.request
import json
import re

url = 'https://www.planity.com/adivinange-latelier-coiffure-trets-13530'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')

print("HTML length:", len(html))

# Save html for inspection if needed
with open("sample_establishment.html", "w", encoding="utf-8") as f:
    f.write(html)

json_lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print("JSON-LD count:", len(json_lds))
for i, jld in enumerate(json_lds):
    print(f"--- JSON-LD {i} ---")
    try:
        data = json.loads(jld)
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    except Exception as e:
        print(jld[:500])

# Check for window.__INITIAL_STATE__ or __NEXT_DATA__ or similar
for line in html.split('\n'):
    if 'window.__' in line or 'INITIAL_STATE' in line or '__NEXT_DATA__' in line or 'telephone' in line.lower() or 'phone' in line.lower() or 'email' in line.lower():
        if len(line) < 300:
            print("Found line:", line)
