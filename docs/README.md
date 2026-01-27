# Documentation Hub

Use this folder as the single starting point for documentation. The structure mirrors how the application is built (crawler core, FastAPI backend, React frontend) plus operational guides and prompts.

## Layout

- `system-overview.md` – combined description of how all parts of the stack interact and how to deploy them end-to-end.
- `components/` – deep dives for each codebase:
  - `crawler.md`
  - `backend.md`
  - `frontend.md`
- `handover/` – operations-facing assets:
  - `structure-map.md` – ownership sheet showing where each capability lives.
  - `mega-prompts.md` – reusable debugging prompts (one global, plus one per component).
- `assets/` – Folder for presentation images, video guide notes, the fertilizer prediction interview decks, the researcher survey, and the “ideas for next” vault (see `docs/assets/README.md` for descriptions).
