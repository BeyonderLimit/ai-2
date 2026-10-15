# AGENTS.md

AI-2 is a Python CLI (`ai-2`, alias `AI-2`) that turns a PC into a local-AI machine: hardware
detection, capability-tier tuning, model management, an OpenAI-compatible server, and local
Knowledge Pack (RAG) search. It also ships an Artix Linux ISO. Reference platform is Artix/runit;
a Debian/Ubuntu (apt/systemd) path exists through `ai2/backends/`.

## Setup and tests

- Python 3.11+; the only runtime dependency is PyYAML. `pip install -e .` to get the `ai-2` command.
- **Run tests from the repo root.** Tests read relative paths (`packaging/`, `iso/`, `branding/`,
  `ai2/data/`) and `import ai2` from the top-level package dir.
  ```
  pip install pyyaml pytest
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/
  ```
- Single test: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_tiers.py::test_name`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is required — it is how the README and CI run. There is no
  lint / typecheck / format step.
- Network tests are opt-in only: `AI2_NET_TESTS=1 ... pytest tests/test_catalog_urls.py` HEAD-checks
  the live model URLs. Never set it in a normal run.
- `tests/test_isa_gate.py` needs `gcc` + `objdump` (skipped otherwise).

## Test guards (do not fight them)

`tests/conftest.py` installs autouse fixtures that **raise `AssertionError`** if a test runs the real
update checker, downloads a model, or opens a real terminal window. A test that needs a model must
monkeypatch `find_model_file` / `download_model` (or carry `@pytest.mark.real_download`). Do not add
tests that touch the developer's machine or the network.

## Architecture

- Small engine, deliberately data-driven. Behavior lives mostly in `ai2/data/`: `tiers/*.yml`
  (capability tiers), `models.yml` (model catalog), `profiles/*.yml` (workflows), `packs.yml`
  (packaged copy of the community Knowledge Pack catalog), `i18n/*.json` + `languages.json`.
- `ai2/cli.py` is the argparse entry point (`ai2 = ai2.cli:main`). `detect.py` / `tiers.py` /
  `tuning.py` are the adaptation engine; `runtime.py` drives llama.cpp (downloads, `serve`,
  benchmark); `workflows.py` reads profiles; `backends/` isolates package manager (pacman/apt) and
  init (runit/systemd) so the engine never calls them directly; `knowledgecli.py` + `doc.py` +
  `pack*.py` are Knowledge Packs/RAG.
- `tools/` scripts are not part of the `ai-2` command.
- `packaging/`, `iso/`, `branding/` are distro artifacts. The packaging/ISO scripts use
  container-absolute paths (`/ai2-repo/www/ai-2`) and run **inside the build container**, not from
  this checkout.

## Invariants enforced by tests

- Version has one source: `ai2/__init__.py` `__version__`. `pyproject.toml` reads it dynamically,
  and `packaging/ai-2/PKGBUILD` `pkgver` must match (`build-packages.sh` rewrites it).
- `tests/test_consistency.py` and `tests/test_schemas.py` cross-check the tier/model/profile YAML.
  Example: every tier capability key must exist in `benchmark.STAR_LABELS`, and every named model id
  must be in the catalog. Change the YAML and this code together.
- Exactly one catalog model is flagged `benchmark` (`qwen2.5-0.5b`).
- `packaging/ai2-llama-cpp/isa-check.sh` and `packaging/ai2-whisper-cpp/isa-check.sh` must stay
  byte-identical (the ISA gate rejects instructions the oldest target CPU cannot execute).

## Generated files — regenerate, don't hand-edit

- Pack PKGBUILDs (`packaging/ai2-help`, `ai2-everyday`, `ai2-linux-essentials`) come from the
  catalog: `python3 tools/render-pack-packages.py`. Tests and the build run `--check` and fail on drift.
- `ai2/data/packs.yml` is a copy of the community catalog: `python3 tools/sync-pack-catalog.py`
  (run before a release; the build refuses a stale copy).
- `packaging/ai-2/etc-known.sha256`: after editing `branding/motd` or
  `branding/lightdm-gtk-greeter.conf`, run `python3 tools/update-etc-known.py`.
- Generated language/translator blocks in `README.md` / `TRANSLATING.md`:
  `python3 tools/translations.py readme --write`.
- ISO overlay copies of `branding/` or package files must be **byte-identical** to their source
  (`tests/test_iso_profile.py`); copy the source over the overlay after editing, unless the variant
  is listed as deliberate in that test.

## Translations

- Adding a language touches: the installer `.ts`
  (`iso/profiles/ai2/live-overlay/usr/share/calamares/branding/ai2/lang/calamares-ai2_<code>.ts`),
  `branding/desktop/*.desktop` (`Name[xx]`/`Comment[xx]`), `ai2/data/i18n/<code>.json`, the two
  guides in `branding/`, `ai2/data/languages.json`, and `translators.json`.
  `tests/test_languages.py` names what is still missing; `tools/translations.py check` / `coverage`
  report locally.
- `.qm` files are build output and never committed. `tools/translations.py build` makes them (needs
  `lrelease`); `iso/stage-profile.sh` refuses to stage an image without current ones.

## CI (`.github/workflows/tests.yml`)

Jobs: `unit` (all tests, offline), `secrets` (gitleaks over full history), `translations` (Qt6 l10n
tools + `desktop-file-utils`), and `catalog` (network check of `packs.yml` URLs/sizes/hashes; runs
only weekly or when that file changes). Reproduce the offline jobs locally before pushing.
