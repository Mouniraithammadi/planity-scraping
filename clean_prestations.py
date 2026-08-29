import re
from bs4 import BeautifulSoup

def extract_clean_prestations(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    current_cat = "Prestations"
    
    for elem in soup.find_all(['h2', 'h3', 'div']):
        if elem.name in ['h2', 'h3']:
            txt = elem.get_text(strip=True)
            if txt and len(txt) < 80 and not any(k in txt.lower() for k in ['horaire', 'avis', 'information', 'où se situe', 'collaborateur', 'à-propos', 'réserver']):
                current_cat = txt
        elif elem.name == 'div':
            text = elem.get_text(" | ", strip=True)
            if '€' in text and ('min' in text or 'h' in text) and len(text) < 300:
                clean = re.sub(r'Choisir', '', text)
                clean = re.sub(r'Cette prestation ne peut pas être réservée en ligne\.', '', clean)
                clean = re.sub(r'\s+', ' ', clean).strip(' |')
                clean = re.sub(r'\|\s*\|+', '|', clean)
                
                # Check if it has actual title text (not just "15min | 20 €")
                text_without_price_dur = re.sub(r'\b\d+\s*min\b|\b\d+\s*h\s*\d*m?i?n?\b|\d+\s*€|à partir de|de|à|\||\s+', '', clean, flags=re.I)
                if len(text_without_price_dur) >= 3 and any(c.isalpha() for c in text_without_price_dur):
                    formatted = f"[{current_cat}] {clean}"
                    if not any(skip in clean.lower() for skip in ['voir les', 'prendre rdv', 'avis', 'carte bancaire']):
                        results.append(formatted)

    # Filter duplicates and fragments
    final_prestations = []
    for r in results:
        if not any(r == existing or (r in existing and len(r) < len(existing)) for existing in final_prestations):
            final_prestations.append(r)
            
    return final_prestations

with open("sample_establishment.html", "r", encoding="utf-8") as f:
    html = f.read()

prestations = extract_clean_prestations(html)
print(f"Extracted {len(prestations)} clean prestations:")
for i, p in enumerate(prestations[:10]):
    print(f" {i+1}. {p.encode('ascii', 'replace').decode()}")
