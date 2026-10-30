PY ?= python3
SKILL_DIR ?= $(HOME)/.dsh/skills/novel-writing
SKILL_AB_DIR ?= $(HOME)/.dsh/skills/novel-ab

.PHONY: test sync install clean

test:
	$(PY) tests/test_all.py

sync:
	@mkdir -p skill/scripts skill-ab/scripts
	@cp scripts/*.py skill/scripts/
	@cp scripts/*.py skill-ab/scripts/
	@cp WORKFLOW.md skill/WORKFLOW.md
	@echo "synced scripts -> skill/scripts ($(shell ls scripts/*.py | wc -l | tr -d ' ') files)"

install: sync
	@mkdir -p $(dir $(SKILL_DIR)) $(dir $(SKILL_AB_DIR))
	@rm -rf $(SKILL_DIR) $(SKILL_AB_DIR)
	@cp -R skill $(SKILL_DIR)
	@cp -R skill-ab $(SKILL_AB_DIR)
	@echo "installed -> $(SKILL_DIR)"
	@echo "installed -> $(SKILL_AB_DIR)"

clean:
	@rm -rf scripts/__pycache__ tests/__pycache__ skill/scripts/__pycache__ skill-ab/scripts/__pycache__
