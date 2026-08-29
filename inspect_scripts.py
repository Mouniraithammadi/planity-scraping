import urllib.request
import re
from bs4 import BeautifulSoup

url = 'https://www.planity.com/adivinange-latelier-coiffure-trets-13530'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
print(f"Total script tags: {len(scripts)}")
for i, s in enumerate(scripts):
    stype = s.get('type', '')
    sid = s.get('id', '')
    src = s.get('src', '')
    content = s.string or ""
    print(f"Script {i}: type='{stype}' id='{sid}' src='{src[:50]}' len={len(content)}")
    if 'window.' in content or 'initial' in content.lower() or 'state' in content.lower():
        print("  Snippet:", content[:200])
