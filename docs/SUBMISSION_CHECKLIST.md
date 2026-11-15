# Submission checklist — NASA Space Apps 2026

Checked against the official [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/)
(2026 hackathon, dated 13 November 2026) on 14 November 2026.

**Deadline:** submission opens Saturday 14 November 2026, 09:00 and **closes Sunday
15 November 2026, 23:59** (time zone of the Local Event). Edits are allowed until then;
only the last saved version is judged.

## Submission form (all fields required, all in English)
- [ ] Project name
- [ ] High-level project summary
- [ ] Link to project demo (public, no password / permission / registration; test in a private browser window)
- [ ] Link to final project (e.g. the public GitHub repository and/or the deployed app)
- [ ] Detailed project description
- [ ] Use of Super Intelligence (SI): how tools were used (data collection only, not seen by judges)
- [ ] NASA data used (at least one NASA data set is required for a Global Award) — list below
- [ ] Space agency partner data and other references (all data, resources and tools) — from `docs/CREDITS.md`
- [ ] All team members confirmed at the same Local Event; "Terms and Conditions" and "Confirm All Work is Original" ticked; "Submit for Judging"

## Demo (guide: video ≤ 30 s **or** slide deck ≤ 7 slides)
- [ ] Choose format. `docs/DEMO.md` is a **2-minute** script: it must be cut to **≤ 30 s** for a video, or turned into ≤ 7 slides. Longer demos are **not eligible** for Global Judging
- [ ] Video: English speech or English subtitles. Slides: English, with team name, member names and the challenge ("Field Shift: Adapting Farms with NASA Data")
- [ ] Hosted externally (YouTube, Google Drive, GitHub, …), link public
- [ ] No images, video, audio or likeness of anyone under 18
- [ ] SI-generated images/videos (if any) carry a visible watermark; no NASA logos or design elements in generated content (the app uses none)

## Licence and code
- [x] `LICENSE` (Apache-2.0, full text) at repo root
- [x] `NOTICE` file
- [x] No secrets in git history (`.env` ignored, `.env.example` only; checked 2026-11-11)
- [x] SI use acknowledged: README "Use of AI", `docs/CREDITS.md` "AI tools", `Co-Authored-By` lines in the commit metadata (guide: code must acknowledge SI in text and metadata)
- [ ] Repository public on GitHub; README explains setup in ≤ 2 commands
- [ ] Deployed app (optional for the guide, but makes the "final project" link usable for judges)

## Sources and credits
- [x] `docs/CREDITS.md` complete: every data set, API, library (transitive: `docs/DEPENDENCIES.md`), base map, AI tool
- [ ] Every non-NASA source openly accessible or OSI-licensed — **open:** FAO ECOCROP (temperature ranges of 28 crops) states no licence; used by user decision 2026-11-12, labelled in data, UI and docs under the single source key `ecocrop`; FAO asked, no reply yet. Without it 15 of 50 crops stay evaluable. Mention this in the description
- [x] No promotion of commercial products or services (checked 2026-11-14): brand names appear only functionally — Google Maps links are parsed, Google Earth Engine is the access platform for NASA data, the optional plain-language explanation uses the Anthropic API (off by default; the app works without it), packages in `docs/DEPENDENCIES.md`

## NASA data used
- [x] NASA POWER daily (climate, ET0, suitability, irrigation interval)
- [x] MODIS MOD13Q1 NDVI (patterns, NDVI risk layer) and MCD12Q2 phenology (season validation)
- [x] SMAP SPL3SMP_E 005 + 006 (soil moisture, risk layer)
- [x] GPM IMERG V07 monthly (rainfall check, optional rainfall source)
- [x] NASADEM (slope, erosion score, contour row direction)
- [ ] Verified but not used: HLS / Landsat, GRACE/GRACE-FO, ECOSTRESS, GEDI (do not list them as used)

## Responsible use
- [x] "Supports, does not replace, farmer and local expert judgement" message visible where decisions are made (also in the easy-mode plan)
- [x] Privacy summary in the app ("Gizlilik"), matching `docs/PRIVACY.md` (mode choice in local storage, field corners never leave the device)
- [x] `docs/METHOD.md` states which parts are ML, rules, physics; assumptions are labelled
