# Headmaster Labubledore — backend

Harry Potter multi-agent class demo. A boss Labubu (**Headmaster Labubledore**) chats with the user and delegates to **7 book specialist Labubus** via PydanticAI tools. Each specialist answers from **retrieved chunks** of its book in `harrypotter.db` (never the full text).

## Setup

```powershell
cd "Lecture 10\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Put `PORTKEY_API_KEY` in `test_student/zlisto/.env` or `Lecture 10/.env` (see `../.env.example`). Model default: `gpt-6-astra`.

## Run

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If 8000 is busy, use `--port 8001` and point the frontend at that port.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health + DB/key status |
| GET | `/api/roster` | Boss + 7 specialists metadata |
| POST | `/api/chat` | Non-streaming chat (`{ "message": "..." }`) |
| POST | `/api/chat/stream` | SSE progress + final answer |

### SSE event types

- `boss_thinking` — boss started
- `specialist_started` — book agent called
- `specialist_done` — book agent finished
- `final` — full `{ answer, delegations, boss_name }`
- `error` — failure payload

### Final response shape

```json
{
  "answer": "narrative from Labubledore",
  "delegations": [
    {
      "agent": "Book 6 Labubu",
      "book_number": 6,
      "book_title": "Harry Potter and the Half-Blood Prince",
      "question": "How are Horcruxes explained?",
      "reply": "...",
      "status": "done"
    }
  ],
  "trace": [],
  "boss_name": "Headmaster Labubledore"
}
```

## Notes

- Full books are 111k–371k tokens each — specialists use keyword chunk retrieval (~40k chars evidence cap).
- Do not commit `.env` or dump book text into logs/README.
