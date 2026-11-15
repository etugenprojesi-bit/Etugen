# Etügen

Decision-support PWA for exploring crop-rotation strategies anywhere on Earth,
built for the NASA Space Apps Challenge 2026 challenge *"Field Shift: Adapting
Farms with NASA Data"*.

**Try it:** <https://etugen-etugen.hf.space/?lang=en>

> **This tool supports, it does not replace, the farmer's judgement and local
> agronomic expertise.** Every recommendation lists the evidence behind it, its
> data gaps, and the questions to check locally.

## What it does

- **Pick a field** on a satellite map, or mark its corners to get its area in decares.
- **Easy mode:** answer one question (can you irrigate?) and get a 2–3 year rotation plan:
  crop per year, sowing and harvest dates, rain shortfall, irrigation interval, idle months.
- **Row direction:** NASADEM slope shows which way the land falls; the app draws rows across it.
  On flat land erosion is left out.
- **Expert mode:** priorities, constraints, the farmer's current rotation, nine sub-scores,
  risk layers and the evidence behind every card.
- **NASA data:** POWER (25 years daily), GPM IMERG, SMAP, MODIS NDVI and phenology, NASADEM;
  plus SoilGrids, GGCMI crop calendar and peer-reviewed crop temperatures. 50 crops, every
  value sourced; unknown stays "missing data".
- **Turkish by default, English** with the EN button (or `?lang=en`). Works on a phone;
  the three demo fields (Konya, Punjab, Nakuru) answer in seconds from saved real data.

## Repository layout

```
backend/        FastAPI app (sources, harmonize, features, patterns,
                suitability, rotation, explain, cache) + pytest tests
frontend/       React + Vite + TypeScript PWA
data/           crops.yaml (hand-curated, every value sourced), ecocrop/
demo_cache/     real API responses for 3 demo points (offline fallback)
scripts/probe/  one script per data source, verifying it really works
docs/           DATA_SOURCES, CREDITS, PRIVACY, METHOD, DEMO, KULLANIM_KILAVUZU, SUBMISSION_CHECKLIST, STAGES
```

## Setup

Copy `.env.example` to `.env` (optional for stage 1); never commit `.env`.

### Backend (stage 1)

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt   # bin/ on macOS/Linux
backend/.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --port 8000
```

Then open `http://localhost:8000/api/analyze?lat=37.60&lon=32.75` (Konya) or
`http://localhost:8000/docs` for the interactive API page. Optional
parameter `irrigation=none|limited|full`.

Risk layers (stage 5): `http://localhost:8000/api/risk?lat=37.60&lon=32.75`
(optional `crop=winter_wheat`). `/api/analyze`, `/api/risk` and
`/api/rotations` accept `precip_source=power|imerg`, `delta_t` (°C, −2…4)
and `delta_p` (%, −30…30): a sensitivity test, see `docs/METHOD.md`.

Satellite layers (stage 3): `http://localhost:8000/api/satellite?lat=37.60&lon=32.75`.
Needs `EE_PROJECT` in `.env` and `earthengine authenticate` once; without
Earth Engine the 3 demo points still work from `demo_cache/`, other points
return an explicit error. To refresh the demo cache:
`backend/.venv/Scripts/python scripts/build_demo_cache.py gee`.

### Frontend (stage 2)

In a second terminal, with the backend running:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. If port 8000 is taken, run the backend on
another port and point the dev proxy there (PowerShell:
`$env:API_URL="http://localhost:8001"; npm run dev`). On a phone on the same Wi-Fi, open the
`Network:` address Vite prints (e.g. `http://192.168.1.20:5173`). GPS and
"install as app" need HTTPS, so on a phone over plain Wi-Fi use map taps or
the demo buttons; installing works on the computer at `localhost`.

Production build: `npm run build`, then `npm run preview` (port 4173).

Tests (offline; the 3 demo points use `demo_cache/`):

```bash
cd backend && .venv/Scripts/python -m pytest
```

### Data-source probes (stage 0)

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements-probe.txt   # bin/ on macOS/Linux
cd scripts/probe
../../backend/.venv/Scripts/python probe_power.py
../../backend/.venv/Scripts/python probe_soilgrids_wcs.py
../../backend/.venv/Scripts/python probe_ornl_modis.py
../../backend/.venv/Scripts/python probe_gee_catalog.py
../../backend/.venv/Scripts/python probe_gee.py      # needs EE_PROJECT in .env
```

Results and verified dataset IDs: `docs/DATA_SOURCES.md`.

## Method

See [`docs/METHOD.md`](docs/METHOD.md): which parts are physics (FAO-56),
rules, classical statistics and machine learning, plus the known
limitations. Machine learning (k-means, Isolation Forest) appears only in the
stage 3 pattern comparison, side by side with classical methods.

## Data sources and credits

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md),
[`docs/CREDITS.md`](docs/CREDITS.md) and the generated list of all dependencies
[`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) (`backend/.venv/Scripts/python scripts/list_dependencies.py`).

## User guide (Turkish)

For farmers: [`docs/KULLANIM_KILAVUZU.md`](docs/KULLANIM_KILAVUZU.md) — step by step,
how to read scores and risk colours, limits of the tool, when to ask a local expert.

## Demo

Two-minute script: [`docs/DEMO.md`](docs/DEMO.md). The app is written for farmers in Turkish (default); an **EN** button in the header switches to English, and `?lang=en` in the address opens it in English directly.

## Use of AI

The project idea, the decisions and the review are the team's. Much of the code,
the probe scripts and the documentation were written with an AI coding assistant
(Claude, via Claude Code, Anthropic) and reviewed by the team; commits made with it
carry a `Co-Authored-By: Claude …` line. The app itself uses no AI to compute
scores or plans (rules and physics, see `docs/METHOD.md`); an optional, off-by-default
feature rewords rotation cards in plain language with the Anthropic API. Details:
[`docs/CREDITS.md`](docs/CREDITS.md) "AI tools".

## Live demo

- App: <https://etugen-etugen.hf.space> (Turkish) · <https://etugen-etugen.hf.space/?lang=en> (English)
- Code: <https://github.com/etugenprojesi-bit/Etugen>

## Privacy

See [`docs/PRIVACY.md`](docs/PRIVACY.md).

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).
