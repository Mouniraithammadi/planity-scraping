import urllib.request
import re

def count_establishment_urls_in_sitemap(sitemap_url):
    req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        content = urllib.request.urlopen(req).read().decode('utf-8')
        urls = re.findall(r'<loc>(.*?)</loc>', content)
        # Establishments on planity don't have category path like /coiffeur/ or /de-DE/
        # Establishment URLs are like https://www.planity.com/<name>-<zipcode> or <name>-<city>-<zipcode>
        # Let's count how many URLs match establishment pattern vs category pattern
        est_urls = [u for u in urls if u.count('/') == 3 and not any(u.startswith(f"https://www.planity.com/{lang}") for lang in ['de-DE', 'nl-BE', 'en-GB', 'es-ES'])]
        return len(urls), len(est_urls), urls[:3]
    except Exception as e:
        return 0, 0, [str(e)]

for i in range(10):
    total, est, samples = count_establishment_urls_in_sitemap(f"https://www.planity.com/sitemap-{i}.xml")
    print(f"Sitemap-{i}: Total={total}, Establishments={est}")
    if est > 0:
        print("  Sample est:", samples[0])
