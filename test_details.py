import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

async def test_samples():
    with open("planity_urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()][:50]
        
    async with aiohttp.ClientSession() as session:
        for url in urls[:10]:
            try:
                async with session.get(url, headers=HEADERS, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors='ignore')
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Check JSON-LD @type
                        json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
                        ld_types = []
                        for jld in json_ld_matches:
                            try:
                                ld = json.loads(jld)
                                ld_types.append(ld.get('@type'))
                            except:
                                pass
                                
                        # Check breadcrumbs or categories in HTML
                        breadcrumbs = [a.get_text(strip=True) for a in soup.find_all('a') if '/coiffeur' in a.get('href', '') or 'coiffeur' in a.get_text().lower()]
                        
                        # Check website / social links
                        all_a = soup.find_all('a')
                        ext_links = []
                        for a in all_a:
                            href = a.get('href', '')
                            if href.startswith('http') and not any(d in href for d in ['planity.com', 'schema.org', 'w3.org', 'google', 'facebook.com', 'instagram.com']):
                                ext_links.append(href)
                        
                        fb = [a.get('href') for a in all_a if 'facebook.com' in a.get('href', '')]
                        ig = [a.get('href') for a in all_a if 'instagram.com' in a.get('href', '')]
                        
                        # Check email
                        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
                        valid_emails = [e for e in emails if not any(d in e.lower() for d in ['planity.com', 'schema.org', 'sentry.io', 'w3.org'])]
                        
                        print(f"URL: {url}")
                        print(f"  LD Types: {ld_types}")
                        print(f"  Breadcrumbs/Coiffeur links: {breadcrumbs[:3]}")
                        print(f"  Ext Websites: {ext_links}")
                        print(f"  Socials: FB={fb}, IG={ig}")
                        print(f"  Emails: {valid_emails}")
                        print("-" * 50)
            except Exception as e:
                print(f"Error {url}: {e}")

asyncio.run(test_samples())
