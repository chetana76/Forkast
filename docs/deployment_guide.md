# Forkast — Deployment Guide
## Live demo on Streamlit Community Cloud (free, 5 minutes)

### Why deploy?

A live public URL satisfies the competition's "Public Project Link" requirement
and lets judges click through the full Forkast UI without any local setup.
Streamlit Community Cloud is free for public repos.

---

### Step 1 — Push your repo to GitHub

```bash
git add .
git commit -m "Add Streamlit Cloud config and secrets template"
git push
```

### Step 2 — Create a Streamlit Cloud account

Go to **share.streamlit.io** → sign in with GitHub → authorise access to your repos.

### Step 3 — Deploy Forkast

1. Click **"New app"**
2. Repository: `chetana76/forkast`
3. Branch: `main`
4. Main file path: `app/main_app.py`
5. Click **"Advanced settings"** → **"Secrets"**
6. Paste this into the secrets box:
   ```toml
   GOOGLE_API_KEY = "your-actual-key-here"
   ```
7. Click **"Deploy"**

Streamlit builds the environment, installs `requirements.txt`, and starts the app.
First deploy takes 2–3 minutes. After that you get a URL like:
`https://forkast.streamlit.app`

### Step 4 — Add the URL to your Kaggle submission

On the Kaggle writeup form, paste the Streamlit URL into the "Public Project Link" field.

---

### Troubleshooting

**ImportError on google-adk or chromadb** — Streamlit Cloud uses Python 3.11
by default. Add a `runtime.txt` to pin it:
```
python-3.11
```

**API key not found error** — check the Secrets panel in your app dashboard
(gear icon → Secrets). The key must be exactly `GOOGLE_API_KEY` with no spaces.

**ChromaDB persistence** — Streamlit Cloud does not persist disk state between
sessions. The app uses `EphemeralClient()` in notebook mode; for the Streamlit
app, `data/chroma/` is written to a temp directory that resets on redeploy.
Run `rag/ingest.py` as part of app startup by adding this to `app/main_app.py`:

```python
@st.cache_resource
def init_rag():
    from rag.ingest import ingest
    ingest()
init_rag()
```

This embeds the 30 recipes on first load (~10s) and caches the result for
the lifetime of the Streamlit session.
