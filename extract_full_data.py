import re
import json
from bs4 import BeautifulSoup

with open("sample_establishment.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Let's inspect the main HTML sections for Prestations / Categories
# On Planity, category titles and service items are rendered in specific DOM structures
print("--- PRESTATIONS IN DOM ---")

# Let's search for category containers and service cards/items
# Find category titles or headers
headings = soup.find_all(['h2', 'h3', 'h4', 'div'], text=True)

# Let's inspect headers or service elements
for h in soup.find_all(['h2', 'h3']):
    title = h.get_text(strip=True)
    print("Heading:", title)

# Let's check all text blocks that look like services (e.g. name + duration + price)
# e.g., "Shampooing, coupe, coiffage" "35 min" "32 €"
print("\n--- FINDING ALL SERVICES & PRICES ---")
service_list = []

# Planity renders service cards or list items. Let's look for divs containing price (€) and duration (min)
for div in soup.find_all('div'):
    # Check if div contains price pattern like "30 €" or "30,00 €" or "à partir de"
    text = div.get_text(" ", strip=True)
    if '€' in text and ('min' in text or 'h' in text) and len(text) < 200:
        if text not in service_list:
            service_list.append(text)

print(f"Total service blocks found: {len(service_list)}")
for s in service_list[:20]:
    print(" ->", s)

# Also let's check for Email inside the full page or scripts or text
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
print("\nEmails found:", set(emails))

# Check for telephone
phones = re.findall(r'(?:tel:|phone|telephone)[\"\'\:\=s]*([\+\d\s\.\-\/]{9,15})', html, re.I)
print("\nPhones found in regex:", set(phones))
