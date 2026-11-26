#!/usr/bin/env bash
# Crea en GitHub las issues del backlog de la consola (CE01 E3) y las etiquetas que usa el plan.
# OPCIONAL y NO se ejecuta desde make: revisarlo y correrlo a mano, con `gh auth login` hecho, cuando el sponsor apruebe
# el plan (paso manual del README). Lee gestion/e3/datos/plan.json (python gestion/e3/plan.py lo genera).
#
#   bash gestion/e3/crear_issues.sh [--dry-run]
set -euo pipefail
cd "$(dirname "$0")/../.."
SECO="${1:-}"
PY="${PYTHON:-python}"

ejecutar() { if [ "$SECO" = "--dry-run" ]; then printf '%q ' "$@"; echo; else "$@"; fi; }

for etiqueta in cambio-alcance historia must should wont; do
  ejecutar gh label create "$etiqueta" --force --description "CE01 E3" >/dev/null
done

"$PY" - <<'EOF' > /tmp/celeris_issues.tsv
import json
m = json.load(open("gestion/e3/datos/plan.json", encoding="utf-8"))["modelo"]["agil"]
for h in m["historias"]:
    cuerpo = (f"{h['texto']}\n\n**Requisitos:** {', '.join(h['req'])} · **Casos de uso:** {', '.join(h['cu'])}\n"
              f"**MoSCoW:** {h['moscow']} · **Puntos:** {h['puntos']} · **WSJF:** {h['wsjf_valor']:.2f} · "
              f"**Sprint:** {h['sprint'] or '—'}\n\n**Criterio de aceptación (Gherkin):**\n\n{h['gherkin']}")
    etiqueta = {"Must": "must", "Should": "should", "Won't": "wont"}[h["moscow"]]
    print("\t".join([f"{h['id']} {h['quiero'][:80]}", etiqueta, cuerpo.replace("\n", "\\n")]))
EOF

while IFS=$'\t' read -r titulo etiqueta cuerpo; do
  ejecutar gh issue create --title "$titulo" --label historia --label "$etiqueta" --body "$(printf '%b' "$cuerpo")"
done < /tmp/celeris_issues.tsv
