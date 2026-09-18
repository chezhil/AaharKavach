# SAM custom build. SAM looks for this inside CodeUri.
#
# The handlers import the knowledge base (data/) and the agent (agent/), which
# live at the repo root — outside CodeUri. A plain `sam build` packages only
# CodeUri, so those imports resolve during local development and then
# ImportError in Lambda: the deploy succeeds and every request 500s.
#
# SAM runs make in a temp copy of CodeUri, so relative paths to the repo are
# meaningless here. ARTIFACTS_DIR is absolute and inside the repo
# (<root>/backend/.aws-sam/build/<Function>), so the root is four levels up.

ROOT := $(shell cd "$(ARTIFACTS_DIR)/../../../.." && pwd)
# `python` is not on PATH on a stock macOS; CI images vary too.
PY := $(shell command -v python3 || command -v python)

define assemble
	@test -d "$(ROOT)/data" || { echo "ERROR: could not locate repo root from ARTIFACTS_DIR"; exit 1; }
	cp -r "$(ROOT)/backend/src/." "$(ARTIFACTS_DIR)/"
	rm -f "$(ARTIFACTS_DIR)/Makefile"
	cp -r "$(ROOT)/data" "$(ARTIFACTS_DIR)/data"
	cp -r "$(ROOT)/agent" "$(ARTIFACTS_DIR)/agent"
	cp -r "$(ROOT)/backend/policies" "$(ARTIFACTS_DIR)/policies"
	$(PY) -m pip install -q -r "$(ROOT)/backend/src/requirements.txt" -t "$(ARTIFACTS_DIR)"
	$(PY) -m pip install -q -r "$(ROOT)/data/requirements.txt" -t "$(ARTIFACTS_DIR)"
	find "$(ARTIFACTS_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type d -name tests -prune -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -name "*.pyc" -delete 2>/dev/null || true
endef

build-ProfilesFunction:
	$(assemble)

build-ScansFunction:
	$(assemble)

build-CompareFunction:
	$(assemble)

build-HistoryFunction:
	$(assemble)
