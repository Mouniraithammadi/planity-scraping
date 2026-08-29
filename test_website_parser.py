import asyncio
import aiohttp
import re
import json
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def extract_website_and_email(html, url):
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
    valid_emails = [
        e for e in emails 
        if not any(d in e.lower() for d in ['planity.com', 'schema.org', 'sentry.io', 'w3.org', 'example.com', 'facebook.com', 'instagram.com', 'cloudinary.com', 'global.prodsharedsvc', 'labsharedsvc'])
    ]
    
    # 1. JSON-LD external websites
    json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    same_as_sites = []
    for jld in json_ld_matches:
        try:
            ld = json.loads(jld)
            s = ld.get("sameAs")
            if isinstance(s, list):
                same_as_sites.extend(s)
            elif isinstance(s, str):
                same_as_sites.append(s)
            u = ld.get("url")
            if u and isinstance(u, str) and u != url and 'planity.com' not in u:
                same_as_sites.append(u)
        except Exception:
            pass

    # 2. BeautifulSoup HTML links
    soup = BeautifulSoup(html, 'html.parser')
    html_websites = []
    social_websites = []
    
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        text = a.get_text(strip=True).lower()
        if href.startswith('http') and 'planity.com' not in href and 'schema.org' not in href and 'w3.org' not in href:
            if any(s in href for s in ['facebook.com', 'instagram.com', 'linktr.ee']):
                social_websites.append(href)
            elif not any(ignore in href for ignore in ['google.com/maps', 'apple.com', 'onelink.me', 'cloudinary.com', 'sentry.io']):
                html_websites.append(href)

    # Search raw HTML for external website pattern or site web link
    site_web_matches = re.findall(r'href=["\'](https?://(?!www\.planity\.com)[^"\']+)["\'][^>]*>(?:[^<]*site|[^<]*web|[^<]*officiel)', html, re.I)

    all_websites = list(dict.fromkeys(same_as_sites + site_web_matches + html_websites + social_websites))
    
    return {
        "email": ", ".join(valid_emails) if valid_emails else None,
        "website": ", ".join(all_websites) if all_websites else None
    }

async def main():
    with open("planity_urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and '/coiffeur' not in line][:30]
        
    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for u in urls[5:15]:
            try:
                async with session.get(u, headers=HEADERS, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors='ignore')
                        res = extract_website_and_email(html, u)
                        print(f"URL: {u}")
                        print(f"  Email: {res['email']}")
                        print(f"  Website: {res['website']}")
            except Exception as e:
                print(f"Error {u}: {e}")

asyncio.run(main())
