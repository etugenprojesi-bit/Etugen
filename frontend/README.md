# Etügen — frontend

React + Vite + TypeScript PWA. See the repository README for how to run it
together with the backend. Main parts:

- `src/components/MapView.tsx` — MapLibre map (OpenFreeMap tiles); the
  MapLibre worker is served by a small plugin in `vite.config.ts`.
- `src/components/Controls.tsx` — GPS, demo points, irrigation choice.
- `src/components/Profile.tsx`, `MonthlyChart.tsx`, `Calendar.tsx`,
  `CropList.tsx` — result screen.
- `src/i18n.ts`, `src/learn.ts` — all user-facing text (Turkish only, plain words for farmers) and the "Bu ne demek?" explanations.
- `src/types.ts` — shape of `GET /api/analyze`.

The dev server proxies `/api` to `http://localhost:8000`.
