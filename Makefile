# Makefile — Celeris CE0311 (Entregable 1). Requiere GNU make y Python 3.12+ (pip install -r infra/requirements.txt).
# Los objetivos sin implementación fallan con «pendiente de P#» (P2 diagramas, P3/P4 XLSX, P5 DOCX, P6 laboratorio).

PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)
VERSION ?= v1.0

.PHONY: help entorno lab-gen image test-imagen deps deps-dev gen test-gen validate lab-up lab-down test-lab matrices diagrams-check informe release-e1

help:
	@echo "make validate        fuente única + artefactos + secretos (infra/validate.py y gitleaks si está instalado)"
	@echo "make entorno          comprueba Docker, containerlab, cargo y tofu (lab/entorno.sh)"
	@echo "make gen              genera ruleset, VPN y PAC del laboratorio en lab/generated (Etapa 1; --aws-peer en AWS_PEERS)"
	@echo "make image            construye la imagen OCI celeris-node (deploy/image/Dockerfile; necesita Docker)"
	@echo "make test-imagen      ejecuta e2e/run.sh contra el binario dentro de la imagen"
	@echo "make test-gen         pruebas unitarias y snapshots de los generadores"
	@echo "make lab-gen         genera lab/celeris.clab.yml y lab/generated desde el inventario"
	@echo "make lab-up|lab-down laboratorio emulado con containerlab (Modo L; necesita Linux/WSL, Docker y containerlab)"
	@echo "make test-lab         ejecuta las pruebas T-nn del Modo L (Etapa 4)"
	@echo "make matrices        genera las dos matrices XLSX (pendiente de P3 y P4)"
	@echo "make diagrams-check  valida los .drawio contra el inventario (pendiente de P2)"
	@echo "make informe         genera DOCX y PDF (pendiente de P5)"
	@echo "make release-e1      copia la versión final a entregables/CE0311/vX.Y/ (pendiente de P5)"

entorno:
	@bash lab/entorno.sh

deps:
	$(PYTHON) -m pip install -r infra/requirements.txt

IMAGE ?= celeris-node:dev
GIT_COMMIT ?= $(shell git rev-parse HEAD 2>/dev/null || echo desconocido)$(shell git diff --quiet HEAD 2>/dev/null || echo -dirty)

image:
	docker build -f deploy/image/Dockerfile --build-arg GIT_COMMIT=$(GIT_COMMIT) --build-arg CREATED=$(shell date -u +%Y-%m-%dT%H:%M:%SZ) -t $(IMAGE) .

test-imagen:
	IMAGE=$(IMAGE) bash deploy/image/verificar-imagen.sh
	IMAGE=$(IMAGE) bash deploy/image/e2e-en-contenedor.sh

deps-dev:
	$(PYTHON) -m pip install -r infra/requirements-dev.txt

# IP públicas de los dos extremos AWS: el inventario no las fija (CI-23). Documentación RFC 5737 por defecto.
AWS_PEERS ?= 198.51.100.21 198.51.100.22

gen:
	$(PYTHON) infra/genera.py todo $(foreach p,$(AWS_PEERS),--aws-peer $(p))

test-gen:
	$(PYTHON) -m pytest tests/gen tests/network -q

validate:
	$(PYTHON) infra/validate.py
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --source . --no-banner --redact; \
	else echo "gitleaks no está instalado: lo ejecuta el CI (.github/workflows/e1.yml). V-30 ya revisó infra/ y docs/infra/."; fi

lab-gen:
	$(PYTHON) infra/genera.py lab

lab-up:
	bash lab/lab.sh up

lab-down:
	bash lab/lab.sh down

test-lab:
	$(PYTHON) tests/network/run.py

matrices:
	@echo "pendiente de P3 (XLSX de componentes) y P4 (XLSX de pruebas)" >&2; exit 1

diagrams-check:
	@echo "pendiente de P2: diagramas draw.io (gancho V-50 en infra/checks/v50_diagramas.py)" >&2; exit 1

informe:
	@echo "pendiente de P5: informe DOCX y PDF desde la plantilla de 11 secciones" >&2; exit 1

release-e1: validate
	@echo "pendiente de P5: copia a entregables/CE0311/$(VERSION)/ tras make informe y make matrices" >&2; exit 1
