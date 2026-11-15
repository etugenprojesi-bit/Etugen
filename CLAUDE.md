# Etügen — working rules

NASA Space Apps 2026 project ("Field Shift: Adapting Farms with NASA Data"):
a mobile-first PWA for exploring crop-rotation strategies anywhere on Earth.
Full brief and stage plan: README.md, docs/.

## Conversation
- Talk to the user in Turkish. Code, identifiers and comments in English.
- The user works alone, is not deeply familiar with git/CLI: give step-by-step
  instructions with commands and say what each step is for.

## Process
- Work in stages (docs/STAGES.md). Stop at the end of each stage:
  summarise what was done, how to test it, open questions; wait for approval.
- Ask before adding a heavy dependency or changing the architecture.
- Small, meaningful commits. Commits stay local (no remote / GitHub for now).
- Unit-test calculation code (ET0, trapezoid, harmonisation, rotation rules, scoring).

## Data integrity
- Never invent data, coefficients, dataset IDs or results. Verify every source
  with a probe script (scripts/probe/) and record it in docs/DATA_SOURCES.md.
- If an API fails, show the error / missing data explicitly. Mock data must be
  marked in the file name (MOCK_) and in the UI.
- No made-up prices: market data is "user input / unknown".
- Every value in data/crops.yaml has a source; null = unknown, never 0.
- Crop temperature limits come from literature with DOI + table/page. FAO ECOCROP
  (no licence stated; FAO asked) is used, by user decision 2026-11-12, only for
  crops without literature values, labelled in data, UI and docs, all under the
  single source key `ecocrop` so it can be removed if FAO objects.
- POWER GWETTOP/GWETROOT are model output, not SMAP observations — label them so.

## Space Apps rules
- Apache-2.0. Update docs/CREDITS.md in the same commit as any new dependency,
  data set, base map or AI tool (name, provider, link, licence, used for).
- Non-NASA sources must be freely accessible or OSI-licensed; ask the user before
  adding anything with an unclear/restrictive licence.
- No promotion of commercial products in the app or docs.
- Privacy: location and inputs are used only for the analysis; the server
  stores only 0.05°-rounded coordinates + public-data results (docs/PRIVACY.md).
- Secrets only in .env (never committed). Earth Engine needs EE_PROJECT in .env.

## Environment
- Windows, Python 3.14 venv at backend/.venv, Node 24, no Docker installed.
- Demo points (MODIS-verified cropland): konya 37.60,32.75 · punjab 30.80,75.60 · nakuru -0.25,36.15.
