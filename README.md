# mult_agent_hp — Headmaster Labubledore

Class demo: a **Harry Potter multi-agent** app. Chat with boss Labubu **Headmaster Labubledore**; he delegates to **7 book specialist Labubus** (one per novel). Specialists answer from **retrieved chunks** of a local `harrypotter.db` (full books stay out of the system prompt).

> **Corpus not in this repo.** Per-book PDFs and `harrypotter.db` are copyrighted and must stay on your machine. Place them locally (see below) before running.

## Quick start

### 1. Env

Copy `.env.example` → `.env`:

```
PORTKEY_API_KEY=your_key
MODEL_NAME=gpt-6-astra
```

### 2. Local book data

Expected layout (gitignored):

```
harrypotter.db          # SQLite with books table (full text + token_count)
books/
  01_sorcerers_stone.pdf
  02_chamber_of_secrets.pdf
  …
  07_deathly_hallows.pdf
```

Build `harrypotter.db` from your own legally obtained per-book PDFs with a local extract script (tokenizer `o200k_base`). Schema:

```sql
CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  book_number INTEGER NOT NULL UNIQUE,
  title TEXT NOT NULL,
  source_pdf TEXT NOT NULL,
  page_count INTEGER NOT NULL,
  char_count INTEGER NOT NULL,
  token_count INTEGER NOT NULL,
  tokenizer TEXT NOT NULL,
  text TEXT NOT NULL
);
```

### 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health: http://127.0.0.1:8000/api/health

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — Vite proxies `/api` to port 8000.

If the API is on **8001**, set `frontend/.env`:

```
VITE_API_BASE=http://127.0.0.1:8001
```

## Good test question

> For each Horcrux, when and how is it found or destroyed across the books?

## Layout

```
mult_agent_hp/
  .env.example
  README.md
  backend/          # FastAPI + PydanticAI
  frontend/         # Vite React + Labubu SVG cast
  books/            # local PDFs only (gitignored)
  harrypotter.db    # local SQLite only (gitignored)
```
