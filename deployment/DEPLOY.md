# Deployment Guide

## Option 1 — Render (Recommended, Free Tier)

### Steps

1. **Fork** this repository to your GitHub account

2. Go to [render.com](https://render.com) → **New** → **Web Service**

3. Connect your forked repository

4. Configure:
   | Setting | Value |
   |---------|-------|
   | Root Directory | `backend` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | Free |

5. Add Environment Variables in Render Dashboard:
   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=<your_groq_api_key>
   DEBUG=false
   LOG_LEVEL=INFO
   ```
   Get a free Groq key: https://console.groq.com

6. Add a **Persistent Disk**:
   - Mount path: `/opt/render/project/src/chroma_db`
   - Size: 1 GB

7. Click **Deploy** — first deploy takes ~5 minutes (model download)

8. Your app will be live at: `https://your-service-name.onrender.com`

---

## Option 2 — Railway

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Deploy:
   ```bash
   cd backend
   railway init
   railway up
   railway variables set GROQ_API_KEY=your_key LLM_PROVIDER=groq
   ```

---

## Option 3 — Docker (Self-hosted / VPS)

```bash
# Clone
git clone https://github.com/zairakhaan786/GenAI-Banking-Support-Chatbot.git
cd GenAI-Banking-Support-Chatbot

# Configure
cp backend/.env.example backend/.env
# Edit .env and add GROQ_API_KEY

# Build & Run
docker-compose up --build -d

# View logs
docker-compose logs -f bankbot

# App running at http://localhost:8000
```

---

## Option 4 — Local Development

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your API key
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `groq` | `groq` / `openai` / `google` / `fallback` |
| `GROQ_API_KEY` | Recommended | — | Free at console.groq.com |
| `OPENAI_API_KEY` | Optional | — | OpenAI GPT access |
| `GOOGLE_API_KEY` | Optional | — | Google Gemini access |
| `DEBUG` | No | `false` | Enable debug mode |
| `TOP_K_RESULTS` | No | `5` | RAG retrieval chunks |
| `CHUNK_SIZE` | No | `600` | Document chunk size |

> **Note:** The chatbot works in **fallback mode** even without any API key, using retrieved context to construct responses.

---

## Health Check

After deployment, verify:
```bash
curl https://your-app-url.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "collection_documents": 49
}
```
