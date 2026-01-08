# ArticleCrawler Full Stack Installation and Runbook

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Repository Setup](#repository-setup)
4. [Environment Configuration](#environment-configuration)
6. [Backend API Setup](#backend-api-setup)
7. [Frontend Setup](#frontend-setup)
8. [Running the Stack Together](#running-the-stack-together)


---

## Overview

ArticleCrawler ships as a three-part stack:

* **core engine** (`fakenewscitationnetwork/`): the Python package that crawls OpenAlex, manages experiments, and exports libraries.
* **Backend API** (`article-crawler-backend/`): a FastAPI service that exposes crawler functionality to the UI and orchestrates long-running jobs.
* **Frontend** (`frontend/`): a Vite + React application that talks to the API and visualizes crawler outputs.

The backend and frontend let you operate the crawler through a browser.

---

## Requirements

* **Software**

  * Git
  * Python 3.11
  * Docker Desktop (required for optional GROBID PDF parsing) or for the docker setup
* **Accounts / API keys**

  * OpenAlex email (`OPENALEX_EMAIL`)
  * Optional Zotero credentials (`ZOTERO_LIBRARY_ID`, `ZOTERO_LIBRARY_TYPE`, `ZOTERO_API_KEY`)

Ensure ports **8000** (API), **5173** (frontend), and **8070** (GROBID) are free.

---

## Repository Setup

Clone the repo and switch to the working branch:

```bash
git clone https://github.com/imanmossavat/OpenAlexProject.git
cd OpenAlexProject
```

Project layout:

* `install.py` – full-stack installer (root)
* `fakenewscitationnetwork/` – Python package, CLI, data directories
* `article-crawler-backend/` – FastAPI project
* `frontend/` – React + Vite application


---

## Environment Configuration

There are 2 ways to configure 1. the automated setup where you run install.py, 2. is the Docker-based setup (recommended for MacOS)

You can either let the installer generate all environment files automatically by just inputting the right data in the console when prompted.

The installer:

* creates **`.venv/` at the repository root**
* installs **all Python dependencies (CLI + backend)** into that environment
* writes `.env` files for all components

### Automated setup (recommended)

From the repository root:

```bash
# From the root
python install.py
```

The script:

* prompts for OpenAlex/Zotero configuration
* writes `.env` files for CLI, backend, and frontend
* creates `.venv/` and installs all Python dependencies
* downloads required NLTK data
* checks Docker
* optionally runs `npm install` for the frontend

You can re-run it safely; it will prompt before overwriting files.

---


#### Getting API Keys


**Zotero API Key** (Optional):

1. Create account at https://www.zotero.org/
2. Go to https://www.zotero.org/settings/keys
3. Click "Create new private key"
4. Select read permissions
5. Copy the API key to your `.env` file
6. Find your library ID


---

### Docker-based setup (optional, no local dependencies)

If you prefer running the stack inside containers (helpful on macOS where some dependencies require extra work outside of the installer), use the provided Docker workflow.

1. Install Docker Desktop.
2. Copy `.env.docker.example` to `.env` at the repository root and fill in the required values.
3. Run:

   ```bash
   # From the root
   docker compose up --build
   ```

   The backend container runs `python install.py --non-interactive --env-only` on startup, so the same `.env` files are generated automatically inside the mounted directories.

   The compose file also starts GROBID for you; the backend uses `GROBID_URL` (defaults to `http://grobid:8070`) to reach it inside the Docker network.

4. Data & uploads persist on the host through mounted folders

5. Visit [http://localhost:5173](http://localhost:5173) for the frontend and [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) for the API once the containers are up.

You can still run `python install.py` interactively on Windows/Linux when you do not want Docker.

---


### full-stack installer

```bash
# From the root
python install.py
```

> Tip: pass `--non-interactive --env-only` if you just need the `.env` files generated from environment variables (used by the Docker workflow).

Activate the environment afterward:

* **Windows**

  ```bash
  .venv\Scripts\activate
  ```
* **Linux/macOS**

  ```bash
  source .venv/bin/activate
  ```

---

The following is only for if you used the full-stack installer instead of the Docker-based setup

---

### PDF processing (Docker + GROBID)

GROBID is required because of the PDF processing

**IMPORTANT:** Run GROBID commands in a **separate terminal/command prompt** window and keep it running while processing PDFs.

#### Step 1: Pull the GROBID Docker Image
```bash
docker pull lfoppiano/grobid:0.8.2
```

This will download the GROBID image (~2GB). It may take several minutes depending on your internet connection.

#### Step 2: Start GROBID (in a separate terminal)

**Open a new terminal/command prompt window** and run:
```bash
docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2
```

**Notes:**
- Keep this terminal window open while processing PDFs
- Wait about 30-60 seconds for GROBID to fully start


---


## Backend API Setup

If you used the installer, backend dependencies are already installed.

```bash
# ensure .venv is active
# From the root
cd article-crawler-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

* [http://localhost:8000/](http://localhost:8000/)
* [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

## Frontend Setup

```bash
# From the root
cd frontend
npm install
npm run dev
```

Vite defaults to [http://localhost:5173](http://localhost:5173).

---

## Running the Stack Together

1. Activate `.venv/`
2. Start Docker + GROBID (optional)
3. Run backend API (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)
4. Run frontend (`npm run dev`)
5. Use separate terminals for each service

---
