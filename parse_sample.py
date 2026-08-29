import json
import re

with open("sample_establishment.html", "r", encoding="utf-8") as f:
    html = f.read()

# Parse JSON-LD
json_lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
if json_lds:
    try:
        data = json.loads(json_lds[0])
        with open("json_ld_dump.json", "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, indent=2, ensure_ascii=False)
        print("JSON-LD successfully written to json_ld_dump.json")
    except Exception as e:
        print("JSON-LD parse error:", e)

# Check for state scripts
for i, match in enumerate(re.finditer(r'<script.*?>(.*?)</script>', html, re.DOTALL)):
    script_text = match.group(1)
    if 'window.__' in script_text or 'window.INIT' in script_text or 'self.__NEXT_DATA__' in script_text or '__APOLLO_STATE__' in script_text:
        print(f"Script {i} has state, length: {len(script_text)}")
        with open(f"script_state_{i}.txt", "w", encoding="utf-8") as f_out:
            f_out.write(script_text[:100000])

# Also search for telephone, email, address in HTML text/regex
telephones = re.findall(r'(\+39|\+33|0[1-9])(?:[\s\.\-\/]?\d{2}){4}', html)
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
print("Regex Telephones found:", set(telephones))
print("Regex Emails found:", set(emails))
