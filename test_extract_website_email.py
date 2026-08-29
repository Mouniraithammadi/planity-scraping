import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Test a few URLs
urls = [
    "https://www.planity.com/adivinange-latelier-coiffure-trets-13530",
    "https://www.planity.com/le-salon-12-toulon-83000",
    "https://www.planity.com/coiffure-du-port-13002-marseille",
    "https://www.planity.com/l-atelier-coiffure-33000-bordeaux",
    "https://www.planity.com/studio-coiffure-69006-lyon"
]

async def inspect_url(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as resp:
            if resp.status == 200:
                html = await resp.text(errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                
                print(f"=== URL: {url} ===")
                # 1. JSON-LD
                json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
                same_as = []
                ld_types = []
                for jld in json_ld_matches:
                    try:
                        ld = json.loads(jld)
                        ld_types.append(ld.get('@type'))
                        if 'sameAs' in ld:
                            same_as.append(ld['sameAs'])
                        if 'url' in ld and ld['url'] != url:
                            same_as.append(ld['url'])
                    except:
                        pass
                print("JSON-LD Types:", ld_types)
                print("JSON-LD sameAs/url:", same_as)
                
                # 2. Check NEXT_DATA
                next_data = soup.find('script', id='__NEXT_DATA__')
                website = None
                facebook = None
                instagram = None
                if next_data:
                    nd_str = next_data.string
                    # search for website, site, sameAs, facebook, instagram
                    web_matches = re.findall(r'"(?:website|site|url|link|externalUrl|sameAs)":\s*"([^"]+)"', nd_str, re.I)
                    print("NEXT_DATA website matches:", web_matches)
                    
                    # search for social
                    fb_matches = re.findall(r'https?://(?:www\.)?facebook\.com/[^\s"\'<>]+', nd_str, re.I)
                    ig_matches = re.findall(r'https?://(?:www\.)?instagram\.com/[^\s"\'<>]+', nd_str, re.I)
                    print("NEXT_DATA FB:", set(fb_matches))
                    print("NEXT_DATA IG:", set(ig_matches))

                # 3. HTML Links
                all_a = soup.find_all('a')
                ext_sites = []
                for a in all_a:
                    href = a.get('href', '')
                    text = a.get_text(strip=True).lower()
                    if href.startswith('http') and not any(d in href for d in ['planity.com', 'schema.org', 'w3.org', 'google', 'onelink.me', 'apps.apple', 'play.google']):
                        ext_sites.append((href, text))
                print("HTML External Links:", ext_sites)

                # 4. Email
                emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
                valid_emails = [e for e in emails if not any(d in e.lower() for d in ['planity.com', 'schema.org', 'sentry.io', 'w3.org', 'example.com', 'facebook.com', 'instagram.com', 'cloudinary.com'])]
                print("Emails found:", valid_emails)
                
                # 5. Is Coiffeur check
                # Check categories / prestations / breadcrumbs
                is_coiffeur = False
                breads = [a.get_text(strip=True) for a in soup.find_all('a') if '/coiffeur' in a.get('href', '')]
                if breads or 'HairSalon' in ld_types or any(k in html.lower() for k in ['coiffeur', 'coiffure', 'barbier', 'coupe', 'shampooing', 'brushing', 'coloration', 'balayage', 'mèches', 'barbe']):
                    is_coiffeur = True
                print("Is Coiffeur:", is_coiffeur, "| Breadcrumbs:", breads)
                print()
    except Exception as e:
        print(f"Error {url}: {e}")

async def main():
    async with aiohttp.ClientSession() as session:
        for url in urls:
            await inspect_url(session, url)

asyncio.run(main())
