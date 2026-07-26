"""
Spike 008 secondary check — Granite vs production (DeepSeek-generated) incidents.

data/incidents/current.json stores only processed output (no original RSS text),
so this feeds title_es as a proxy headline and measures AGREEMENT with the
DeepSeek-produced cut/family — not accuracy against human labels.

Usage: python .planning/spikes/008-granite-openrouter-classifier/run_agreement_prod.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).parents[3]
sys.path.insert(0, str(_REPO_ROOT))
os.environ.setdefault("DEEPSEEK_API_KEY", "unused")

import pipeline.news.classifier as clf
from openai import OpenAI
from pipeline.news.resolver import resolve_cut

env = (_REPO_ROOT / ".env").read_text(encoding="utf-8")
KEY = re.search(r"OPENROUTER_API_KEY=(\S+)", env).group(1).strip()
clf.client = OpenAI(api_key=KEY, base_url="https://openrouter.ai/api/v1")
clf._MODEL = "ibm-granite/granite-4.1-8b"
clf._PROVIDER = "granite-openrouter"

# family whitespace fix (same as run_granite_golden --normalize-family)
_orig = clf._strip_json_fence
def _fix(raw: str) -> str:
    s = _orig(raw)
    try:
        d = json.loads(s)
        if isinstance(d.get("family"), str):
            d["family"] = d["family"].replace(" ", "")
        return json.dumps(d, ensure_ascii=False)
    except Exception:
        return s
clf._strip_json_fence = _fix

incidents = json.loads(
    (_REPO_ROOT / "data" / "incidents" / "current.json").read_text(encoding="utf-8")
)["incidents"]

cut_agree = fam_agree = rejected = 0
rows = []
for i, inc in enumerate(incidents):
    r = clf.classify(inc["title_es"], "")
    if r is None:
        rejected += 1
        rows.append({"id": inc["id"], "status": "rejected", "title": inc["title_es"]})
        continue
    resolved = resolve_cut(r.commune_name, r.region_hint)
    pcut = resolved[0] if resolved else None
    ca, fa = pcut == inc["cut"], r.family == inc["family"]
    cut_agree += ca
    fam_agree += fa
    rows.append({"id": inc["id"], "cut_agree": ca, "fam_agree": fa,
                 "pred_cut": pcut, "prod_cut": inc["cut"],
                 "pred_family": r.family, "prod_family": inc["family"],
                 "title": inc["title_es"]})
    if (i + 1) % 25 == 0:
        print(f"  {i+1}/{len(incidents)}", flush=True)

n = len(incidents)
ok = n - rejected
out = {
    "n": n, "rejected": rejected,
    "cut_agreement_of_accepted": round(cut_agree / ok, 4) if ok else None,
    "family_agreement_of_accepted": round(fam_agree / ok, 4) if ok else None,
    "note": "input = title_es proxy (original RSS text not stored); agreement vs DeepSeek output, not human ground truth",
    "rows": rows,
}
p = _REPO_ROOT / ".planning/spikes/008-granite-openrouter-classifier/results_agreement_prod.json"
p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
print("written:", p)
