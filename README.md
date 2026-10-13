# 🧠 AI Interview Prep Coach

A chat app that coaches you for interviews and **remembers you across sessions**. It asks tailored questions, evaluates your answers, and uses what it has learned about you (target role, weak areas, topics already covered) to personalize the next question.

Built with:

| Piece | Role |
|---|---|
| [Streamlit](https://streamlit.io) | Web UI (chat interface) |
| [LangChain](https://python.langchain.com) | Prompt + LLM chain |
| [Groq](https://groq.com) (`openai/gpt-oss-20b`) | LLM that generates questions and feedback |
| [Mem0](https://mem0.ai) | Long-term memory layer (extracts and retrieves facts about the user) |
| [Qdrant](https://qdrant.tech) (local, on-disk) | Vector store for memories |
| Google Gemini (`gemini-embedding-001`) | Embeddings for memory search |

---

## How it works

```
You type a message
      │
      ▼
Mem0 searches memories for this User ID  (top 5 relevant)
      │
      ▼
LangChain prompt = system prompt + memories + your message
      │
      ▼
Groq LLM replies (next question OR feedback on your answer)
      │
      ▼
Mem0 stores the exchange → new facts are extracted and saved
```

Memories are stored **per User ID**, so different IDs get fully separate coaching histories.

---

## Project structure

```
coach/
├── app.py               # Streamlit UI (chat, sidebar, memory viewer)
├── memory_agent.py      # Mem0 config, LangChain chain, chat() and get_all_memories()
├── pyproject.toml       # Project metadata + dependencies (used by uv)
├── uv.lock              # Locked dependency versions (used by uv)
├── requirements.txt     # Dependency list for pip users
├── .python-version      # Python version pin (3.12)
├── .streamlit/
│   └── config.toml      # Streamlit settings (file watcher disabled)
├── .env                 # Your API keys (you create this, never commit it)
├── .mem0/               # Created at runtime: Mem0 config + history DB
└── qdrant_data/         # Created at runtime: local vector database
```

---

## Step-by-step setup guide

### Step 1: Check prerequisites

- **Python 3.12 or newer** (`python3 --version`)
- **git** (to clone the repo)
- A **Groq API key**, free at <https://console.groq.com/keys>
- A **Google Gemini API key**, free at <https://aistudio.google.com/app/apikey>
- Internet access (the app calls the Groq and Gemini APIs)

### Step 2: Get the code

```bash
git clone <your-repo-url> coach
cd coach
```

If you already have the folder, just `cd` into it.

### Step 3: Create a virtual environment and install dependencies

Pick **one** of the two options.

#### Option A: with `uv` (recommended, uses the exact locked versions)

Install uv if you don't have it: <https://docs.astral.sh/uv/getting-started/installation/>

```bash
uv sync
```

This creates `.venv/` and installs everything from `uv.lock`.

#### Option B: with plain `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Add your API keys

Create a file named `.env` in the project root (same folder as `app.py`):

```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
```

- `GROQ_API_KEY` powers the chat LLM and Mem0's memory extraction.
- `GOOGLE_API_KEY` powers the embeddings used for memory search.
- No quotes and no spaces around `=`.

> ⚠️ **Never commit `.env`.** It contains secrets. Make sure `.env` is listed in `.gitignore` before your first commit (see [Security notes](#security-notes)).

### Step 5: Run the app

```bash
# with uv
uv run streamlit run app.py

# or, with an activated venv (Option B)
streamlit run app.py
```

Streamlit prints a URL, normally <http://localhost:8501>, and opens it in your browser.

### Step 6: Use the coach

1. **Pick a User ID** in the sidebar (default: `alice`). Use your own name or any unique string.
2. **Introduce yourself** in the chat box, for example:
   > I'm preparing for a backend engineer role at a fintech company. I'm weak at system design and SQL indexing.
3. **Answer the questions** the coach asks. It will evaluate each answer and ask a follow-up.
4. Click **Show stored memories** in the sidebar to see what the coach has remembered about you.
5. Click **Clear transcript** to wipe the on-screen chat only. Stored memories are kept.
6. **Close the browser, stop the app, start it again** with the same User ID. The coach still remembers you.

### Step 7: Verify it works

Quick checklist for a healthy setup:

- [ ] App opens at `http://localhost:8501` with the title "AI Interview Prep Coach"
- [ ] Sending a message returns a reply (not an `Error:` message)
- [ ] After a few messages, **Show stored memories** lists items about you
- [ ] Restarting the app and using the same User ID still shows those memories
- [ ] A new User ID shows no memories

---

## Sidebar controls

| Control | What it does |
|---|---|
| **User ID** | Selects whose memories are read and written. Different IDs are isolated. |
| **Show stored memories** | Displays everything Mem0 has saved for the current User ID. |
| **Clear transcript** | Clears the visible chat history only. Does **not** delete memories. |

---

## Configuration

All settings live in `memory_agent.py`:

| Setting | Where | Default | Notes |
|---|---|---|---|
| LLM model | `GROQ_MODEL` | `openai/gpt-oss-20b` | Any chat model available on Groq |
| LLM temperature (chat) | `ChatGroq(..., temperature=0.3)` | `0.3` | Higher = more varied questions |
| Memory LLM temperature | `MEM0_CONFIG["llm"]` | `0.1` | Used by Mem0 for fact extraction |
| Embedding model | `MEM0_CONFIG["embedder"]` | `models/gemini-embedding-001` | |
| Embedding size | `embedding_model_dims` / `embedding_dims` | `768` | **Must match** in both places |
| Vector DB path | `MEM0_CONFIG["vector_store"]["path"]` | `./qdrant_data` | Local on-disk Qdrant |
| Memories per query | `MEMORY.search(..., limit=5)` | `5` | |
| Coach behavior | `SYSTEM_PROMPT` | Interview coach prompt | Edit to change the coach's style or target domain |

Streamlit settings are in `.streamlit/config.toml` (the file watcher is disabled to avoid reload issues with the local Qdrant lock).

---

## Resetting your data

All memory is stored locally in two places. To start completely fresh:

1. Stop the app (`Ctrl+C`).
2. Delete the data folders:
   ```bash
   rm -rf qdrant_data .mem0
   ```
3. Start the app again. Both folders are recreated automatically.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `Error: Memory initialization failed: ...` | Missing or invalid API key, or Qdrant folder locked | Check `.env`, then make sure only **one** app instance is running |
| `Storage folder ... is already accessed by another instance of Qdrant` | Two processes using `qdrant_data/` at once | Stop all other `streamlit` processes (`pkill -f streamlit`) and restart |
| `GROQ_API_KEY` / `GOOGLE_API_KEY` not found | `.env` missing, misnamed, or in the wrong folder | `.env` must be next to `app.py`, with exact key names |
| 401 / invalid API key errors | Key typo or revoked key | Regenerate the key in the Groq / Google console |
| 429 / rate limit errors | Free-tier quota reached | Wait a minute and retry, or use a different key or model |
| Vector dimension mismatch error | Changed the embedding model or dims after data was created | Make both dims values match, then [reset your data](#resetting-your-data) |
| `ModuleNotFoundError` | Dependencies not installed or venv not active | Re-run Step 3, and use `uv run ...` or activate `.venv` |
| Wrong Python version | Python older than 3.12 | Install 3.12+ (uv does this automatically with `uv sync`) |
| Port 8501 already in use | Another Streamlit app is running | `streamlit run app.py --server.port 8502` |

---

## Security notes

- `.env` holds real API keys. **Do not commit or share it.** Add this line to `.gitignore` if it isn't there already:
  ```
  .env
  ```
- If a key was ever committed or shared, revoke it and generate a new one.
- `.mem0/` and `qdrant_data/` contain the personal details you told the coach. Consider adding them to `.gitignore` too.

---

## Useful commands

```bash
uv sync                               # install / update dependencies
uv run streamlit run app.py           # start the app
uv run streamlit run app.py --server.port 8502   # use another port
rm -rf qdrant_data .mem0              # wipe all stored memories
```
