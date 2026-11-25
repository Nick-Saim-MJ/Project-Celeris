# Makefile — Celeris CE0311 (Entregable 1). Requiere GNU make y Python 3.12+ (pip install -r infra/requirements.txt).
# Los objetivos sin implementación fallan con «pendiente de P#» (P2 diagramas, P3/P4 XLSX, P5 DOCX, P6 laboratorio).

PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)
VERSION ?= v1.0

.PHONY: diagrams-dc diagrams-dc-check matrices-dc informe-dc informe-ce02 help entorno lab-gen tofu-gen tofu-check tofu-emulador image test-imagen deps deps-dev gen test-gen validate lab-up lab-down test-lab matrices diagrams-check informe release-e1

help:
	@echo "make validate        fuente única + artefactos + secretos (infra/validate.py y gitleaks si está instalado)"
	@echo "make entorno          comprueba Docker, containerlab, cargo y tofu (lab/entorno.sh)"
	@echo "make gen              genera ruleset, VPN y PAC del laboratorio en lab/generated (Etapa 1; --aws-peer en AWS_PEERS)"
	@echo "make image            construye la imagen OCI celeris-node (deploy/image/Dockerfile; necesita Docker)"
	@echo "make test-imagen      ejecuta e2e/run.sh contra el binario dentro de la imagen"
	@echo "make test-gen         pruebas unitarias y snapshots de los generadores"
	@echo "make lab-gen         genera lab/celeris.clab.yml y lab/generated desde el inventario"
	@echo "make lab-up|lab-down laboratorio emulado con containerlab (Modo L; necesita Linux/WSL, Docker y containerlab)"
	@echo "make tofu-gen         genera deploy/opentofu/envs/demo/diseno.auto.tfvars.json desde el inventario (Modo A)"
	@echo "make tofu-check       tofu fmt -check y tofu validate de deploy/opentofu (no planifica ni aplica nada)"
	@echo "make tofu-emulador    levanta el AWS Emulator local, aplica la demo y genera evidencias/<fecha>-E (AWS emulado, sin cuenta real)"
	@echo "make test-lab         ejecuta las pruebas T-nn del Modo L (Etapa 4)"
	@echo "make matrices        genera las dos matrices XLSX (componentes y pruebas)"
	@echo "make diagrams-check  genera, exporta y valida los diagramas draw.io (V-50…V-56)"
	@echo "make informe         genera el informe DOCX y PDF desde la plantilla y valida V-80+ (Word o LibreOffice)"
	@echo "make informe-ce02    genera el Entregable 1 de CE02 (SRS, prototipo, C4 + ADR, UML) en DOCX y PDF (Word)"
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

tofu-gen:
	$(PYTHON) infra/genera.py tofu

# Solo formato y validación; el despliegue (tofu plan/apply) es decisión del equipo y no se ejecuta aquí.
tofu-check: tofu-gen
	tofu fmt -check -recursive deploy/opentofu
	cd deploy/opentofu/envs/demo && tofu init -backend=false -input=false && tofu validate

# AWS emulado: plano de control, sin tráfico. Solo contra el AWS Emulator en Docker, con credenciales ficticias (CI-53).
tofu-emulador:
	deploy/opentofu/emulador/demo.sh todo

lab-up:
	bash lab/lab.sh up

lab-down:
	bash lab/lab.sh down

test-lab:
	$(PYTHON) tests/network/run.py

# Matrices XLSX: componentes (P3, gancho V-60; recalcula una copia en LibreOffice o Excel, V-65) y pruebas (P4, gancho V-70).
matrices:
	$(PYTHON) infra/gen/xlsx_componentes.py --verificar
	$(PYTHON) infra/genera.py xlsx-pruebas

# Genera los 7 .drawio desde infra/*.yaml, los exporta a PNG/PDF con el XML embebido (necesita draw.io Desktop;
# ruta en DRAWIO si no está en el PATH) y los valida (V-50…V-56). Informe: docs/infra/e1/cobertura-figuras.md.
diagrams-check:
	$(PYTHON) infra/gen/drawio.py
	$(PYTHON) infra/gen/exportar_drawio.py
	$(PYTHON) infra/gen/drawio_check.py

informe:
	$(PYTHON) docs/infra/e1/build_informe.py --pdf
	$(PYTHON) infra/validate.py

# Entregable 2 (CE0331, centro de datos híbrido): solo diseño. Orden: diagrams-dc → matrices-dc → informe-dc.
diagrams-dc:
	$(PYTHON) infra/gen/drawio_dc.py
	$(PYTHON) infra/gen/exportar_dc.py

diagrams-dc-check:
	$(PYTHON) infra/gen/drawio_dc_check.py

matrices-dc:
	$(PYTHON) infra/gen/xlsx_centro_datos.py --verificar

informe-dc:
	$(PYTHON) docs/infra/e2/build_informe.py --pdf
	$(PYTHON) infra/validate.py

# CE02 Entregable 1 (Requerimientos y Diseño del Sistema): regenera los UML/C4 y arma el informe.
informe-ce02:
	$(PYTHON) docs/software/e1/diagramas/render.py
	$(PYTHON) docs/software/e1/build_informe_ce02.py --pdf

release-e1: validate
	@echo "pendiente de P5: copia a entregables/CE0311/$(VERSION)/ tras make informe y make matrices" >&2; exit 1
