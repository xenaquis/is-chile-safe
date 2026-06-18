"""Phase 17 Wave 0 — S3: resolve real SII download URLs + reachability."""
import re
import requests
from urllib.parse import urljoin

PAGE = "https://www.sii.cl/sobre_el_sii/estadisticas_de_empresas.html"
H = {
    "User-Agent": "Mozilla/5.0 (compatible; IsChileSafe data pipeline; +https://ischilesafe.com)",
    "Accept-Language": "es-CL,es;q=0.9",
}

r = requests.get(PAGE, headers=H, timeout=40)
html = r.content.decode("utf-8", errors="replace")
links = re.findall(r'href=["\']([^"\']+\.(?:xlsb|xlsx|xls|zip|csv|txt))["\']', html, re.I)
links = sorted(set(urljoin(PAGE, l) for l in links))
print(f"found {len(links)} data links:")
for l in links:
    print(" ", l)

# reachability for comuna-relevant ones
print("\nreachability of comuna/empresa files:")
for l in links:
    low = l.lower()
    if any(k in low for k in ("comu", "empresas.zip", "trtrab", "reg_com")):
        try:
            h = requests.get(l, headers=H, timeout=40, stream=True)
            print(f"  {h.status_code}  len={h.headers.get('content-length','?')}  type={h.headers.get('content-type','?')}  {l}")
            h.close()
        except Exception as e:
            print(f"  FAIL {type(e).__name__}: {e}  {l}")
