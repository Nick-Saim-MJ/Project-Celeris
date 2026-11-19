#!/usr/bin/env bash
# Comprueba las herramientas del laboratorio (Modo L) y del Modo A. No instala nada.
set -u
FALTAN=0
v() { # nombre, comando de versión
  if out=$(eval "$2" 2>&1 | head -1) && [ -n "$out" ]; then printf '  ok    %-12s %s\n' "$1" "$out"; else printf '  FALTA %-12s\n' "$1"; FALTAN=$((FALTAN + 1)); fi
}
v docker        "docker --version"
v "docker (demonio)" "docker info --format '{{.ServerVersion}}'"
v containerlab  "containerlab version 2>/dev/null | grep -m1 version"
v nftables      "nft --version"
v cargo         "cargo --version"
v clippy        "cargo clippy --version"
v tofu          "tofu version"
v python3       "python3 --version"
echo
[ "$FALTAN" -eq 0 ] && echo "entorno completo" || { echo "$FALTAN herramienta(s) sin instalar: ver docs/infra/e1/ensayo-laboratorio.md (requisitos)"; exit 1; }
