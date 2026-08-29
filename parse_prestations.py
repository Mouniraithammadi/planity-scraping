import re
import json

with open("sample_establishment.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for prestation items, category items, or service lists in HTML / script data
print("Searching for prestations...")

# Check if there is a script containing prestations or categories
for match in re.finditer(r'<script.*?>(.*?)</script>', html, re.DOTALL):
    s = match.group(1)
    if 'category' in s.lower() or 'prestation' in s.lower() or 'service' in s.lower():
        if len(s) > 1000:
            print("Found script snippet with categories/services, length:", len(s))
            # search for JSON structure in script
            json_matches = re.findall(r'(\{[^{}]*"name"[^{}]*\})', s)
            print("Sample json matches in script:", json_matches[:5])

# Let's also check BeautifulSoup HTML tags for Prestations
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find elements related to prestations/services
services = []
# Planity usually displays service groups and service items with titles and prices
for item in soup.find_all(True, class_=re.compile(r'service|prestation|category|offering|card', re.I)):
    text = item.get_text(strip=True)
    if any(k in text.lower() for k in ['€', 'min', 'coiffure', 'coupe', 'brushing', 'soin']):
        services.append(text)

print(f"BS4 found {len(services)} candidate service elements. Top 10:")
for s in services[:10]:
    print(" -", s[:150])
