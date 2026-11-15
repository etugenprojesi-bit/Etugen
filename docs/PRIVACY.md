# Privacy

Etügen has no user accounts, no cookies and no tracking.
(Checked against the code on 2026-11-11, stage 7. A short Turkish version is
shown in the app under "Gizlilik".)

| Data | Where it goes | Stored? |
|---|---|---|
| Selected location (lat/lon) | Backend, which rounds it to 0.05° (~5 km) before asking public data services (NASA POWER, Earth Engine for NASA satellite data) | The backend cache stores **only the rounded coordinates and public-data results**, with no identifier, IP address or time of request |
| Irrigation, rainfall source, scenario sliders, priorities, constraints, current rotation | Backend, in memory for the single request | **Not stored** on the server |
| Explanation request (optional LLM) | Only if the user ticks it and the server has an API key: the card facts and priorities, **without coordinates**, to the Anthropic API | Not stored by us; the UI shows a notice when this is on |
| Inputs in your browser | Kept only while the page is open (React state). The only values written to local storage are the chosen mode ("easy" / "expert") and the language ("tr" / "en") | Mode and language choice only, on your device |
| Field corners (optional) | Never leave the browser: the area and the field sketch are computed on the device; only the centre is used as the selected location (rounded by the backend as above) | No |
| Map view | Map tiles for the area on screen are loaded from OpenFreeMap and, for the satellite view, from EOX (tiles.maps.eox.at); no cookies, no account, no key | Not by us; see openfreemap.org and eox.at |
| Place search (optional) | Only if the user types a place name and presses "Ara": the typed text (not the location) goes from the browser to OpenStreetMap Nominatim. Typed coordinates and pasted map links are parsed in the browser and sent nowhere | Not by us; see the OSMF privacy policy |
| TKGM parcel query (optional link) | The app only opens TKGM's own web site in a new tab. Nothing is sent from the app to TKGM and nothing entered there comes back to the app; a pasted map link is parsed in the browser | No |
| Recent results | The app's service worker keeps the last 20 analysis results and the last 20 risk/satellite results on your device for offline use (public data only) | 7 days, on your device |

**Server logs.** The web server's access log normally writes the client
address next to the request URL, which contains the coordinates. The backend
removes the query string from access-log lines (`app/logging_privacy.py`,
tested), so coordinates and IP addresses are never logged together. Requests
to public data services may be logged with the rounded coordinates, without
any user information.

**Hosted demo.** The public demo runs on Hugging Face Spaces (docs/YAYINLAMA.md). The app
stores nothing beyond what is listed above; the hosting provider’s own request logs fall under
its privacy policy.
