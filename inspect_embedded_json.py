import urllib.request
from bs4 import BeautifulSoup
import json
import re

url = 'https://www.planity.com/adivinange-latelier-coiffure-trets-13530'
headers = {'User-Agent': 'Mozilla/5.0'}
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers)).read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')

for s in scripts:
    content = s.string or ""
    # Find any JSON object with "phoneNumber" or "locality" or "mainType" or "siretNumber"
    matches = re.findall(r'(\{[^{}]*"phoneNumber"[^{}]*\})', content)
    for m in matches[:5]:
        print("Found JSON match:", m[:200])

# Let's search for any JSON objects with "website" or "email" or "social" or "facebook" or "instagram"
matches_web = re.findall(r'(\{[^{}]*(?:website|email|facebook|instagram|url)[^{}]*\})', html, re.I)
print("Total matching JSON blocks in HTML:", len(matches_web))
for m in matches_web[:10]:
    if len(m) < 500:
        print(" ->", m)
