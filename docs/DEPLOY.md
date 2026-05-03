# Deployment — Render

This document covers deploying weather_traffic to [Render](https://render.com) using the
`render.yaml` Blueprint at the project root. Two services are created from a single repo:

| Service | Type | URL pattern |
|---|---|---|
| `wt-bergen-api` | Web Service (Python, free) | `https://wt-bergen-api.onrender.com` |
| `wt-bergen` | Static Site (free) | `https://wt-bergen.onrender.com` |

> **Actual URLs may differ** if the service names are already taken on Render. Confirm in the dashboard after Step 3.

---

## Prerequisites

- GitHub account with this repo pushed (public or private)
- [Render account](https://dashboard.render.com/register) (free tier is sufficient)
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com/)

---

## First deploy

### Step 1 — Push render.yaml to GitHub
```bash
git add render.yaml backend/Procfile docs/DEPLOY.md
git commit -m "feat: add Render Blueprint deployment"
git push origin main
```

### Step 2 — Create a Blueprint on Render
Render dashboard → **New** → **Blueprint** → select your repository → confirm.

Render reads `render.yaml` and queues both services for creation.

### Step 3 — Wait for builds (~5–15 min)
Watch the build logs in the Render dashboard. The backend build installs Python deps;
the frontend build runs `npm install && npm run build`. Both must reach **Live** status.

### Step 4 — Set ANTHROPIC_API_KEY (required before the AI agent works)
Render dashboard → **wt-bergen-api** → **Environment** → add:

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` (your key) |

Click **Save Changes** — Render will redeploy the backend automatically.

### Step 5 — Confirm both services are live
- Backend health: `https://wt-bergen-api.onrender.com/api/health` → `{"status":"ok"}`
- Frontend: `https://wt-bergen.onrender.com` → dashboard loads (AI report button works once backend is warm)

---

## Step 6 — Fix the circular URL dependency (required for full functionality)

The frontend URL must be in the backend's CORS allowlist, and the backend URL must be baked
into the frontend build. Both are placeholders in `render.yaml` — update them now that the
real URLs are known.

**6a. Update CORS on the backend**

Render dashboard → **wt-bergen-api** → **Environment** → update:

```
CORS_ORIGINS = ["https://your-actual-frontend-url.onrender.com"]
```

Save → automatic redeploy.

**6b. Update the backend URL in render.yaml and redeploy the frontend**

Edit `render.yaml` — replace the `PUBLIC_BACKEND_URL` placeholder:
```yaml
      - key: PUBLIC_BACKEND_URL
        value: https://your-actual-backend-url.onrender.com
```

```bash
git add render.yaml
git commit -m "chore: set production backend URL for frontend build"
git push origin main
```

Render detects the push and rebuilds the frontend with the correct URL baked in.

---

## ⚠️ Cold start — read before demoing

Render's **free tier suspends the backend after 15 minutes of inactivity**. The container
is shut down entirely; the SQLite database (ephemeral) is wiped.

When the next request arrives:
1. Render starts a fresh container (~5–10 s)
2. `seed_demo.py` runs and recreates the 8 demo incidents (~2 s)
3. The first API response is returned (~30–60 s total from request to response)

**This is expected behaviour on the free tier.** Subsequent requests within the active
window respond in < 300 ms. Upgrading to the Starter plan ($7/month) eliminates cold starts.

The frontend (static site) is not affected — it loads instantly regardless.

---

## Updating an existing deployment

Push to `main` — Render auto-deploys both services on each push. To deploy manually:
Render dashboard → service → **Manual Deploy** → **Deploy latest commit**.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend build fails: `ModuleNotFoundError: No module named 'app'` | `pip install -e .` failed | Check build logs; ensure `rootDir: backend` in render.yaml |
| `422 Unprocessable Entity` on CORS_ORIGINS | Value is not valid JSON | Ensure it is `'["https://..."]'` — double quotes inside single quotes |
| Frontend shows "Failed to load data" | Backend is cold-starting or `PUBLIC_BACKEND_URL` is wrong | Wait 60 s and retry; confirm the URL in backend service logs |
| AI report returns `{"confidence": 0.0, ...}` | `ANTHROPIC_API_KEY` not set or invalid | Set the key in Render dashboard → wt-bergen-api → Environment |
| `CORS Missing Allow Origin` in browser | Frontend URL not in `CORS_ORIGINS` | Update env var (Step 6a) and redeploy backend |
| Service URL ends with `-abc123` suffix | Default name was already taken on Render | Use the Render-assigned URL everywhere; update Step 6 accordingly |

**Logs:**
- Render dashboard → service → **Logs** tab (real-time)
- Backend startup logs show `weather_traffic backend starting up — database ready at ...`
- `seed_demo.py` prints a summary of the 8 incidents seeded on every cold start
