## Project Overview
**Project Name:** Supply Chain - Warehousing  
**Agent Name:** Inventory Management Agent / Medical Inventory Management Agent  
**Team:** Team 1 - Supply Soul  
**Contributors:** Megha Narendra Simha, Poorrnima Vetrivelan, Nada Feteiha

This system helps healthcare facilities efficiently manage medication and supply inventory, forecast demand using machine learning embeddings and semantic search, and automate restocking. It leverages AI agents, a Flask backend, PostgreSQL database, and a React frontend with visualizations.

---

## Key Goals
- Maintain real-time inventory levels and generate alerts for low stock.
- Analyze historical consumption data and forecast future demand.
# Supply Chain - Warehousing (Medical Inventory Management)

Project repository for an inventory management system aimed at healthcare facilities. It provides stock monitoring, demand forecasting, semantic search for inventory resolution, and automated purchase-order assistance with a responsive React dashboard.

## Overview

- Real-time stock tracking and low-stock alerts
- Demand forecasting using historical trend analysis and semantic-search-assisted resolution
- Automated purchase-order generation with human-in-the-loop approval
- React dashboard with charts and conversational chatbot interface

## Repository layout

- `Backend/` — Flask backend, MCP orchestrator, semantic-search utilities, TTS/STT endpoints, helper scripts
- `Frontend/` — React + Vite frontend application (dashboard, chatbot, inventory views)
- `schema_only.sql`, `full_dump.sql` — (database schema and optional data dumps)

## Quick Start (developer)

### Prerequisites
- macOS / Linux / Windows
- Python 3.9–3.11 recommended
- Node.js + npm (for frontend)
- PostgreSQL (local or remote)
- Homebrew (macOS) recommended for installing system audio tools

### Backend setup
1. Create and activate a Python virtual environment:
```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```
If you prefer a minimal install for development, install only the essentials:
```bash
pip install flask flask-cors psycopg2-binary pandas numpy piper-tts
```

3. Database setup (example):
```bash
# from repo root
psql -U <db_user> -d <db_name> -f schema_only.sql
# optionally load full dump
# psql -U <db_user> -d <db_name> -f full_dump.sql
```

4. Prepare semantic embeddings (optional but recommended):
```bash
python3 Backend/semantic_search/vectorembedding.py
```

5. Start the backend:
```bash
cd Backend
source venv/bin/activate
python app.py
```
The Flask app listens on port 8080 by default.

### TTS (Piper) notes
This repo includes a lightweight Piper-based TTS endpoint in `Backend/tts_api.py`.
- Ensure you have the Piper package installed: `pip install piper-tts`
- Download the model file (example):
```bash
cd Backend
python3 -c "from piper.download import ensure_model_cached; ensure_model_cached('en_US-lessac-medium')"
```
- The endpoint is available at `POST /api/tts` and accepts JSON `{ "text": "..." }`. It returns a WAV file.

### Frontend setup
1. Install and run the frontend:
```bash
cd Frontend
npm install
npm run dev
```
2. Open `http://localhost:5173` (default Vite port).

## Developer notes

- Use Python 3.9–3.11 for best compatibility with ML libraries.
- For heavy ML use (Coqui TTS, torch), install correct `torch` wheel before `sentence-transformers`.
- Remove `__pycache__` and other generated artifacts from commits. Add `__pycache__/` and other binaries to `.gitignore`.

## Recent changes (version2 branch)

This branch contains the following notable changes (summary):
- **Backend**
  - `tts_api.py`: Added Piper-based TTS endpoint that synthesizes text to WAV and stores/returns audio files.
  - `app.py`: Registers `tts_api` blueprint so TTS endpoint is available at `/api/tts`.
  - Semantic search updates: `Backend/semantic_search/combine_mcp_demand_stock_withss.py` updated with improved docstrings and semantic resolution.
  - Added helper CSV fixtures and generation scripts for demo/testing: `consumption.csv`, `finance.csv`, `inventory_master.csv`, and `generatedata.py`.
  - Some large DB dumps and archives were removed from the branch to keep the repository lighter.
- **Frontend**
  - Updated pages: `Chatbot.jsx`, `Dashboard.jsx`, `Home.jsx` — UI and behavior improvements for the chatbot and dashboard.

## Changelog & merge guidance

- Before merging to `main`:
  - Remove `__pycache__` and other binary files from commits and push a `.gitignore` update.
  - Re-run tests and smoke-test the TTS endpoint (ensure Piper model is present).
  - Consider moving demo CSVs out of the main repo into a `data/` release artifact if they are large.

## Help & next steps

If you want, I can:
- Add a `CHANGELOG.md` entry for these changes.
- Add `.gitignore` entries and remove tracked binary artifacts.
- Create a small Dockerfile to simplify environment setup (include Piper model download when building).

## Contact

For questions or to request additional documentation or automation, open an issue or ask here.


- **Backend**

  - `Backend/tts_api.py`: Added a TTS endpoint (Piper-based voice service) that synthesizes text to WAV and returns audio files.
