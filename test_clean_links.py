import re
from bs4 import BeautifulSoup
import json

def extract_clean_links(html, url, ld_data):
    soup = BeautifulSoup(html, 'html.parser')
    
    TRACKING_DOMAINS = [
        'planity.com', 'planityapp.com', 'planity.services', 'cloudfront.net',
        'schema.org', 'w3.org', 'google.', 'googletagmanager', 'google-analytics',
        'sentry.io', 'didomi.io', 'topsort.com', 'cloudinary.com', 'onelink.me',
        'apple.com', 'facebook.net', 'facebook.com/tr', 'hotjar.com', 'gstatic.com',
        'doubleclick.net', 'connect.facebook.net', 'criteo.com', 'hotjar-'
    ]

    raw_websites = []
    facebook_pages = []
    instagram_profiles = []

    # 1. From JSON-LD sameAs / url
    if ld_data:
        same_as = ld_data.get("sameAs", [])
        if isinstance(same_as, str):
            same_as = [same_as]
        for s in same_as:
            if isinstance(s, str) and s.startswith('http'):
                s_lower = s.lower()
                if 'facebook.com' in s_lower and '/tr?' not in s_lower:
                    facebook_pages.append(s)
                elif 'instagram.com' in s_lower:
                    instagram_profiles.append(s)
                elif not any(tr in s_lower for tr in TRACKING_DOMAINS):
                    raw_websites.append(s)

        u = ld_data.get("url")
        if u and isinstance(u, str) and u != url and u.startswith('http'):
            if not any(tr in u.lower() for tr in TRACKING_DOMAINS):
                raw_websites.append(u)

    # 2. From HTML <a> hrefs
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        href_lower = href.lower()
        if href_lower.startswith('http'):
            if any(tr in href_lower for tr in TRACKING_DOMAINS):
                continue
            if 'facebook.com' in href_lower and '/tr?' not in href_lower:
                facebook_pages.append(href)
            elif 'instagram.com' in href_lower:
                instagram_profiles.append(href)
            else:
                raw_websites.append(href)

    # Clean & Deduplicate
    def clean_list(links):
        res = []
        for l in links:
            l = l.strip().rstrip('\\').rstrip('/')
            if l and l not in res:
                res.append(l)
        return ", ".join(res) if res else None

    return {
        "website": clean_list(raw_websites),
        "facebook": clean_list(facebook_pages),
        "instagram": clean_list(instagram_profiles)
    }

# Test on html of an establishment
with open("sample_establishment.html", "r", encoding="utf-8") as f:
    html = f.read()

res = extract_clean_links(html, "https://www.planity.com/adivinange-latelier-coiffure-trets-13530", {})
print("Cleaned extraction result:")
print(json.dumps(res, indent=2))
