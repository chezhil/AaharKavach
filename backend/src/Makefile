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

# Lambda runs python3.11 on x86_64 Linux (see template.yaml), which is not
# necessarily what `pip install` on the build machine would produce: a
# packages with a compiled extension (e.g. cedarpy, a Rust/maturin binding)
# installs as a macOS/arm64 wheel on a Mac, silently fails to import in
# Lambda, and Cedar fails closed — every profile request 403s with no error
# in the deploy itself. Forcing pip to fetch the Lambda-matching manylinux
# wheel from PyPI fixes this without needing `sam build --use-container`.
PIP_TARGET_FLAGS := --platform manylinux2014_x86_64 --implementation cp \
	--python-version 3.11 --abi cp311 --only-binary=:all:

define assemble
	@test -d "$(ROOT)/data" || { echo "ERROR: could not locate repo root from ARTIFACTS_DIR"; exit 1; }
	cp -r "$(ROOT)/backend/src/." "$(ARTIFACTS_DIR)/"
	rm -f "$(ARTIFACTS_DIR)/Makefile"
	cp -r "$(ROOT)/data" "$(ARTIFACTS_DIR)/data"
	cp -r "$(ROOT)/agent" "$(ARTIFACTS_DIR)/agent"
	cp -r "$(ROOT)/backend/policies" "$(ARTIFACTS_DIR)/policies"
	$(PY) -m pip install -q $(PIP_TARGET_FLAGS) -r "$(ROOT)/backend/src/requirements.txt" -t "$(ARTIFACTS_DIR)"
	$(PY) -m pip install -q $(PIP_TARGET_FLAGS) -r "$(ROOT)/data/requirements.txt" -t "$(ARTIFACTS_DIR)"
	# agent/ is copied in above but its own deps (strands-agents, pydantic) were
	# never installed, so the agent import failed at runtime and every
	# evaluation silently fell back to the deterministic rulebook.
	$(PY) -m pip install -q $(PIP_TARGET_FLAGS) -r "$(ROOT)/agent/requirements.txt" -t "$(ARTIFACTS_DIR)"
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
