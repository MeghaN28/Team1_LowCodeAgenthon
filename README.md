# Supply Chain – Warehousing (Medical Inventory Management)

## Project Overview

**Project Name:** Supply Chain - Warehousing  
**Agent Name:** Inventory Management Agent / Medical Inventory Management Agent  
**Team:** Team 1 – *Supply Soul*  
**Contributors:** **Megha Narendra Simha**, **Poorrnima Vetrivelan**, **Nada Feteiha**

This system helps healthcare facilities efficiently manage medication and supply inventory, forecast demand using machine learning embeddings and semantic search, and automate restocking. It leverages AI agents, a Flask backend, a PostgreSQL database, and a React frontend with real-time dashboards and visualizations.

---

## Key Goals

- Maintain real-time inventory levels and generate alerts for low stock.  
- Analyze historical consumption data and forecast future demand.  
- Provide semantic-search-based intelligent item lookup.  
- Automate purchase orders with human-in-the-loop approval.  

---

## Repository Overview

This repository contains the complete implementation of the **Medical Inventory Management System** with:

- 🧠 AI agents for stock monitoring, forecasting, and restocking  
- 🔄 MCP-based agent orchestration  
- 🗄️ Flask backend with PostgreSQL  
- 🖥️ React dashboard with chatbot interface  
- 📊 Visualizations for consumption, forecasting, and stock levels  

---

## Repository Layout


---

## Quick Start (Developer Guide)

### ✅ Prerequisites

- macOS / Linux / Windows  
- Python **3.9–3.11**  
- Node.js + npm  
- PostgreSQL  
- (Optional) Homebrew for macOS  

---

## ⚙️ Backend Setup

### 1. Create a virtual environment

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

Install dependencies
pip install -r requirements.txt
pip install flask flask-cors psycopg2-binary pandas numpy piper-tts

Database setup
psql -U <db_user> -d <db_name> -f schema_only.sql
# Optional: full dump
# psql -U <db_user> -d <db_name> -f full_dump.sql
Prepare embeddings
python3 Backend/semantic_search/vectorembedding.py


Start Backend
cd Backend
source venv/bin/activate
python app.py

pip install piper-tts
cd Backend
python3 -c "from piper.download import ensure_model_cached; ensure_model_cached('en_US-lessac-medium')"
POST /api/tts
Body: { "text": "Hello" }
Returns: WAV audio file

cd Frontend
npm install
npm run dev
http://localhost:5173
```
Developer Notes

Recommended Python versions: 3.9–3.11

Install torch before sentence-transformers for compatibility.

Add cache folders (e.g., __pycache__/) to .gitignore.

Team Task Split & Contributions
🧠 Multi-Agent System & Backend

MCP Coding (Core Framework) — Megha N

Agent Orchestration Layer — Megha N

Conversational Agent — Megha N

Background Agent (Real-time DB updates) — Megha N

Semantic Search Agent — Megha N

Inventory Update Agent — Megha N

Mail Agent (Automated PO Emails) — Megha N

📦 Supply Chain AI Agents

Agent 1 — Stock Level Monitor — Megha N

Agent 2 — Demand Forecaster — Megha N

Agent 3 — Reorder Automator — Poorrnima Vetrivelan

📊 Frontend & UI

Conversational Agent UI (Home Page) — Nada Feteiha

Inventory Stock Monitor & Forecast UI — Nada Feteiha

Purchase Order Review Page — Nada Feteiha

Dashboard & Visualizations — Poorrnima Vetrivelan

🔧 Supporting Work

POC on iGentIC — Megha N

GitHub Repository Setup — Megha N

Input Files (CSV, Sample Data) — Poorrnima Vetrivelan

💬 Feedback on the iGentIC Platform

We found the iGentIC platform extremely useful for building multi-agent systems with minimal effort. The low-code environment allowed us to focus mainly on:

Designing and building AI agents

Implementing core logic

MCP-based multi-agent orchestration

Real-time integration with backend and database

✅ What Worked Well

Low-code environment sped up agent development

Smooth UI for testing and triggering agents

Easy integration for both conversational and background agents

🔧 Suggestions for Improvement

Make knowledge base upload more streamlined

Add support for multiple cloud providers

Provide detailed demo videos covering full platform functionality

Add rename/edit options in more UI sections

Overall, the platform provided a strong foundation for building our multi-agent inventory management system. With a few enhancements, it can become even more powerful for future teams.
Application Screenshots
Layer
	Technology
	Purpose

Frontend
	React
	Dashboard, voice interface, human approval UI

Backend
	Python (Flask / FastAPI) MCP
	API endpoints, orchestration logic

AI Agents
	Open AI
	Forecasting, summarization, query handling

Voice/Video
	TTS
	

Data + DB
	PostGres + Knowledge base
	Inventory, consumption, and supplier data

Visualization
	matplotlib / Plotly / React Charts
	Graphs, stock vs threshold, forecasts

Workflow Orchestration
	iGentic Platform
	Multi-agent pipeline control

Version Control
	GitHub
	Code management

