import urllib.request
from bs4 import BeautifulSoup
import json
import re

url = 'https://www.planity.com/adivinange-latelier-coiffure-trets-13530'
headers = {'User-Agent': 'Mozilla/5.0'}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
s10 = scripts[10].string

print("Script 10 length:", len(s10))
print("First 500 chars:", s10[:500])

# Look for website, email, phone, social, instagram, facebook, etc.
keywords = ['website', 'site', 'email', 'facebook', 'instagram', 'phone']
for kw in keywords:
    matches = [m.start() for m in re.finditer(kw, s10, re.I)]
    print(f"Keyword '{kw}': {len(matches)} occurrences")
    for idx in matches[:5]:
        snippet = s10[max(0, idx-50):min(len(s10), idx+150)]
        print("  Snippet:", snippet.replace('\n', ' '))
