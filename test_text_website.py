import urllib.request
import re
from bs4 import BeautifulSoup

urls = [
    "https://www.planity.com/essentiel-coiffure-83400-hyeres",
    "https://www.planity.com/hotel-bastide-de-lourmarin-luberon-84160",
    "https://www.planity.com/adivinange-latelier-coiffure-trets-13530",
    "https://www.planity.com/le-salon-12-toulon-83000"
]

headers = {'User-Agent': 'Mozilla/5.0'}

for u in urls:
    html = urllib.request.urlopen(urllib.request.Request(u, headers=headers)).read().decode('utf-8')
    
    # Regex for website domains in text (e.g. www.domain.fr, domain.fr, http://...)
    # Exclude planity.com, schema.org, w3.org, google.com, etc.
    raw_urls = re.findall(r'(?:https?://|www\.)[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(?:/[^\s"<>]*)?', html)
    valid_websites = set()
    for w in raw_urls:
        w_lower = w.lower()
        if not any(ignore in w_lower for ignore in ['planity.com', 'schema.org', 'w3.org', 'google', 'facebook.com', 'instagram.com', 'cloudinary', 'sentry.io', 'cloudflare', 'onelink.me', 'apps.apple.com', 'play.google.com']):
            valid_websites.add(w)
            
    print(f"URL: {u}")
    print("  Found Websites:", list(valid_websites))
