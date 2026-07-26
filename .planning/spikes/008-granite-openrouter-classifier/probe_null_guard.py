"""
Spike 008 probe — why does Granite ignore the non-crime rule, and does an
explicit is_crime_incident field fix it?

Runs non-crime + traffic-accident probes through:
  A) the production SYSTEM_PROMPT verbatim
  B) a variant that adds "is_crime_incident" as the FIRST output field

Prints raw model JSON for each, so we see family/confidence on the failures.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).parents[3]
sys.path.insert(0, str(_REPO_ROOT))

import os
os.environ.setdefault("DEEPSEEK_API_KEY", "unused")

import pipeline.news.classifier as clf
from openai import OpenAI

MODEL = "ibm-granite/granite-4.1-8b"

env = (_REPO_ROOT / ".env").read_text(encoding="utf-8")
KEY = re.search(r"OPENROUTER_API_KEY=(\S+)", env).group(1).strip()
client = OpenAI(api_key=KEY, base_url="https://openrouter.ai/api/v1")

PROBES = [
    ("null-recycle", "Campaña de reciclaje en Santiago convoca a miles de familias",
     "La Municipalidad de Santiago junto a organizaciones ambientales realizó una masiva campaña de reciclaje en el Parque O'Higgins, convocando a más de 5.000 familias."),
    ("null-hospital", "Inauguran nuevo hospital en Calama con modernas unidades de emergencia",
     "El Presidente de la República inauguró el nuevo Hospital Dr. Carlos Cisternas de Calama, con capacidad para 300 camas."),
    ("null-heat", "Nuevo récord de temperaturas en Chile central: ola de calor sin precedentes",
     "El servicio meteorológico confirmó que varias comunas de Chile central alcanzaron temperaturas récord esta semana."),
    ("traffic-1", "Fatal colisión en Ruta 5 Sur deja dos muertos en Rancagua",
     "Una colisión frontal entre un camión y un automóvil dejó dos personas fallecidas la madrugada de hoy en la Ruta 5 Sur, a la altura de Rancagua. El tránsito estuvo cortado por horas."),
    ("traffic-2", "Atropello en Ñuñoa: adulto mayor grave tras cruzar la calzada",
     "Un adulto mayor resultó gravemente herido tras ser atropellado por un vehículo particular en Ñuñoa. El conductor se mantuvo en el lugar y colaboró con Carabineros."),
    ("crime-ctrl", "Portonazo en Las Condes: delincuentes roban camioneta a punta de pistola",
     "Un hombre fue víctima de un portonazo en la comuna de Las Condes. Los delincuentes, armados, lo obligaron a salir de su vehículo."),
]

VARIANT_PROMPT = clf.SYSTEM_PROMPT.replace(
    '{\n  "commune_name":',
    '{\n  "is_crime_incident": <true or false — false for non-crime news (sports, weather, health, inaugurations, campaigns) AND for traffic accidents without criminal intent>,\n  "commune_name":',
).replace(
    "Rules:",
    "Rules:\n- FIRST decide is_crime_incident. If false: commune_name MUST be null and confidence MUST be 0.0.",
)


def run(prompt: str, label: str) -> None:
    print(f"\n===== {label} =====")
    for pid, head, desc in PROBES:
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.0, max_tokens=512,
            messages=[{"role": "system", "content": prompt},
                      {"role": "user", "content": f"HEADLINE: {head}\nSUMMARY: {desc[:500]}"}],
        )
        raw = resp.choices[0].message.content or ""
        m = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", raw, re.DOTALL)
        raw = m.group(1) if m else raw
        try:
            d = json.loads(raw)
            compact = {k: d.get(k) for k in ("is_crime_incident", "commune_name", "family", "confidence")}
            print(f"  {pid}: {json.dumps(compact, ensure_ascii=False)}")
        except Exception:
            print(f"  {pid}: RAW {raw[:200]}")


run(clf.SYSTEM_PROMPT, "A) production prompt")
run(VARIANT_PROMPT, "B) variant with is_crime_incident first")
