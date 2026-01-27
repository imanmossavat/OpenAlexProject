# Frontend Component (`frontend/`)

## Application Shell

- **Entry points** – `main.jsx` hydrates `<App />`, while `App.jsx` renders the router plus top-level layout. Styling lives in `App.css`, `index.css`, and shared theme files under `src/styles/`.
- **Routing** – `src/app/router.jsx` defines all routes (workflow wizard, author topic analysis, help pages). Routing is declarative; nested routes share the `Layout` component from `src/components/Layout.jsx` (header/footer wrappers).
- **Session hydration** – `shared/lib/session.js` reads/writes session IDs to `localStorage` and can hydrate from query parameters (used when links contain `?sid=...`). This mirrors how the backend expects clients to track session state.

## API & State Helpers

- **API client** – `shared/api/client.js` wraps `fetch`, auto-prefixes the base URL from `shared/config/env.js`, handles query serialization, JSON parsing, and library-session recovery (if a workflow loses session state, it restarts automatically).
- **Endpoints catalog** – `shared/api/endpoints.js` centralizes REST paths (seed sessions, crawler jobs, library uploads, etc.). Always update this file when backend routes change.
- **Workflows** – `shared/workflows/*.js` describes each wizard step (create, edit, crawler, rerun, author topics). These objects drive the Stepper UI and dictate which API endpoints to call at each stage.
- **Utilities** – `shared/lib/time.js`, `shared/lib/session.js`, `hooks/use-toast.js`, and `lib/utils.js` provide formatting, toasts, and helper methods reused across pages.

## Pages & Features

- **Workflow wizard (`src/pages/workflow/WorkflowPage.jsx`)** – Hosts the standard crawler session wizard. It renders stage-specific forms by composing components referenced in the workflow definition (seed entry, keyword builder, config forms, review screens).
- **Create Library (`src/pages/create/*.jsx`)** – Screens dedicated to uploading PDFs or selecting existing libraries before creating a session. `UnifiedStagingPage.jsx` consolidates staging filters (reusing components from `components/column-filters`).
- **Author Topic Exploration (`src/pages/author/*.jsx`)** – Three-step experience (selection → results → temporal evolution) that hits backend topic endpoints and renders markmap charts with styles from `styles/markmap.css`.
- **Help/About** – `pages/help/GrobidSetupPage.jsx` teaches users how to start the optional GROBID container, while `pages/about/AboutPage.jsx` documents the project story and links to repos.

## Reusable Components

- **Layout/Header/Footer** – Standard wrappers that add navigation, logos, and the branding imagery (`src/assets/logo.png`, `fontys.png`, `github.png`, `ixd.svg`, `linkedin.webp`).
- **Stepper (`components/Stepper.jsx`)** – Visualizes wizard progress, automatically reflecting the `shared/workflows` definitions.
- **PaperDetailModal** – Combined paper preview used by staging, author topic results, and job review screens. It fetches detail via `shared/api/client` and shows metadata, keywords, and retraction flags.
- **Column filters (`components/column-filters`)** – Table filtering UI for staging and paper catalog pages; includes constants and filter popovers.

## Data Flow

1. **Session bootstrap** – When users start or resume a workflow, `shared/workflows/createWorkflow` issues a `POST /seeds/session/start`, stores the returned `session_id`, and routes the UI to the first step.
2. **Seed & keyword collection** – Form components post to `/seeds`, `/keywords`, `/configuration` endpoints through the API client. Validation errors appear via the toast hook.
3. **Crawler launch** – Workflow pages call `/crawler_execution/{session_id}/start`. The backend returns `job_id`, which is stored in page state and polled via `/crawler_execution/jobs/{job_id}/status`.
4. **Job monitoring** – Dedicated panels show progress (iterations, papers collected) using responses from `/jobs` endpoints. Users can resume or stop jobs from the same views.
5. **Vault browsing** – Once a job finishes, the frontend fetches summary endpoints (`/crawler_execution/jobs/{job_id}/results`, `/topics`, `/library`) and displays markdown/figures. Downloads go through signed URLs or direct fetch + file-saver logic.
6. **Author topic flows** – Pages under `src/pages/author` query `/author-topic` endpoints and render markmap diagrams with the aggregated topic JSON.

## Styling & Assets

- Theme files rely on CSS modules plus utility classes. `styles/markmap.css` customizes the topic tree visualization.
- Images currently in `src/assets/` cover logos and social icons.


## Directory Highlights


- `src/app/` – Router configuration (`router.jsx`) plus any global providers you add in the future (e.g., query clients). Changes here affect navigation across the entire app.
- `src/pages/` – Feature pages grouped by domain:
  - `pages/workflow/` – The multi-step crawler wizard plus rerun experiences (Workflow page hosts both new-run and rerun modes driven by the workflow definition).
  - `pages/create/` – Library/PDF onboarding and edit screens (start page, matched seeds view, unified staging UI) reused by both new-library and edit-library workflows.
  - `pages/author/` – Author topic selection/results/evolution pages, each consuming the author-topic API endpoints.
  - `pages/help/`, `pages/about/` – Static support content (GROBID setup instructions, project overview).
- `src/components/` – Reusable presentation components such as `Layout`, `Header`, `Footer`, `Stepper`, `PaperDetailModal`, and column filter widgets. These are shared across multiple pages and represent most of the UI chrome.
- `src/shared/` – Cross-cutting logic:
  - `shared/api/` – `client.js` (fetch wrapper), `endpoints.js` (REST paths), `config/env.js` (reads `VITE_API_URL`), plus `lib/` helpers (`session`, `time`, `utils`).
  - `shared/workflows/` – Definitions for every wizard, including crawler creation, crawler rerun (`crawlerRerunWorkflow.js`), edit-library flows (`libraryCreation`, `libraryEditing` variants), author-topic workflows, and any future multi-step experiences. The Stepper and pages read these objects to determine next steps and required API calls.
- `src/hooks/` – Custom hooks like `use-toast` for toast notifications.
- `src/styles/` – CSS for specialty visualizations (`markmap.css`) and any future theme overrides.
- `src/assets/` – Static assets (logos, icons).


