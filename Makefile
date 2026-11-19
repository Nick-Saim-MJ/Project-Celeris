# Makefile — Celeris CE0311 (Entregable 1). Requiere GNU make y Python 3.12+ (pip install -r infra/requirements.txt).
# Los objetivos sin implementación fallan con «pendiente de P#» (P2 diagramas, P3/P4 XLSX, P5 DOCX, P6 laboratorio).

PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)
VERSION ?= v1.0

.PHONY: help deps deps-dev gen test-gen validate lab-up lab-down test-lab matrices diagrams-check informe release-e1

help:
	@echo "make validate        fuente única + artefactos + secretos (infra/validate.py y gitleaks si está instalado)"
	@echo "make gen              genera ruleset, VPN y PAC del laboratorio en lab/generated (Etapa 1; --aws-peer en AWS_PEERS)"
	@echo "make test-gen         pruebas unitarias y snapshots de los generadores"
	@echo "make lab-up|lab-down|test-lab   laboratorio containerlab (pendiente de P6)"
	@echo "make matrices        genera las dos matrices XLSX (pendiente de P3 y P4)"
	@echo "make diagrams-check  valida los .drawio contra el inventario (pendiente de P2)"
	@echo "make informe         genera DOCX y PDF (pendiente de P5)"
	@echo "make release-e1      copia la versión final a entregables/CE0311/vX.Y/ (pendiente de P5)"

deps:
	$(PYTHON) -m pip install -r infra/requirements.txt

deps-dev:
	$(PYTHON) -m pip install -r infra/requirements-dev.txt

# IP públicas de los dos extremos AWS: el inventario no las fija (CI-23). Documentación RFC 5737 por defecto.
AWS_PEERS ?= 198.51.100.21 198.51.100.22

gen:
	$(PYTHON) infra/genera.py todo $(foreach p,$(AWS_PEERS),--aws-peer $(p))

test-gen:
	$(PYTHON) -m pytest tests/gen -q

validate:
	$(PYTHON) infra/validate.py
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --source . --no-banner --redact; \
	else echo "gitleaks no está instalado: lo ejecuta el CI (.github/workflows/e1.yml). V-30 ya revisó infra/ y docs/infra/."; fi

lab-up:
	@echo "pendiente de P6: laboratorio containerlab (lab/celeris.clab.yml, Parte F4)" >&2; exit 1

lab-down:
	@echo "pendiente de P6: laboratorio containerlab (lab/celeris.clab.yml, Parte F4)" >&2; exit 1

test-lab:
	@echo "pendiente de P6: ejecuta tests/network/*.yaml generados de infra/pruebas.yaml (Parte F4.3)" >&2; exit 1

matrices:
	@echo "pendiente de P3 (XLSX de componentes) y P4 (XLSX de pruebas)" >&2; exit 1

diagrams-check:
	@echo "pendiente de P2: diagramas draw.io (gancho V-50 en infra/checks/v50_diagramas.py)" >&2; exit 1

informe:
	@echo "pendiente de P5: informe DOCX y PDF desde la plantilla de 11 secciones" >&2; exit 1

release-e1: validate
	@echo "pendiente de P5: copia a entregables/CE0311/$(VERSION)/ tras make informe y make matrices" >&2; exit 1
