# Gita Wisdom AI - Deployment Guide

## Quick Start (Local Development)

```bash
# 1. Navigate to project
cd /path/to/Gita-project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Streamlit app
streamlit run streamlit_app.py
```

**That's it!** App works with default settings. No configuration needed.

---

## Default Credentials

| Component | Default Value | How to Change |
|-----------|---------------|----|
| Admin Password | `gita_admin_2024` | See "Optional: Custom Secrets" below |
| Port | `8501` | `.streamlit/config.toml` |
| Theme | Serene (Gold & Charcoal) | `.streamlit/config.toml` |

---

## Optional: Custom Secrets

If you want to use a **custom admin password**:

### Step 1: Create secrets file
```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

### Step 2: Edit `.streamlit/secrets.toml`
```toml
ADMIN_PASSWORD = "your_custom_password_here"
```

### Step 3: Restart app
```bash
streamlit run streamlit_app.py
```

---

## Deployment to Streamlit Cloud (Free)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Gita RAG app"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repo
4. Select `streamlit_app.py` as main file
5. Click "Deploy"

### Step 3: Add Secrets (Optional - for production)
1. In Streamlit Cloud dashboard → App settings
2. Go to "Secrets" tab
3. Paste:
```toml
ADMIN_PASSWORD = "your_secure_password"
```
4. App auto-redeploys with new password

---

## Directory Structure

```
Gita-project/
├── streamlit_app.py          ← Main app (run this)
├── requirements.txt          ← Dependencies
├── .streamlit/
│   ├── config.toml          ← App configuration
│   └── secrets.example.toml  ← Template for secrets
├── data/
│   ├── gita.db              ← Verse database
│   ├── analytics.db         ← User feedback
│   └── retriever_state.pkl  ← Cached model
└── notebooks/               ← Development notebooks
```

---

## Troubleshooting

### Error: "No secrets files found"
✅ **Fixed!** App now works without secrets.toml
- Use default password: `gita_admin_2024`
- Or optionally create `.streamlit/secrets.toml` (see above)

### Error: "retriever_state.pkl not found"
- Build retriever first:
```bash
python build_retriever.py
```

### App runs slowly
- First load caches the model (~30 seconds)
- Subsequent searches ~100-300ms
- Consider increasing Streamlit cache timeout

### Admin panel not showing
- Check password: `gita_admin_2024` (or your custom one)
- Look in sidebar under "Settings"

---

## Environment Variables (Advanced)

You can also set admin password via environment variable:

```bash
export ADMIN_PASSWORD="my_password"
streamlit run streamlit_app.py
```

Priority order:
1. Environment variable (`$ADMIN_PASSWORD`)
2. `.streamlit/secrets.toml` 
3. Default (`gita_admin_2024`)

---

## System Requirements

- **Python:** 3.8+
- **RAM:** 2GB minimum (4GB recommended)
- **Storage:** 500MB (includes embeddings)
- **GPU:** Optional (CPU works fine)

---

## Features

✅ Hybrid BM25 + Semantic Search
✅ Reciprocal Rank Fusion (RRF)
✅ Corrective RAG (2024 paper)
✅ Query Expansion (2024 paper)
✅ Real-time Analytics
✅ User Reviews & Feedback
✅ Password-Protected Admin Panel
✅ Serene UI Design
✅ Full Explainability

---

## Support

For issues or questions:
- 📧 Email: 111deblina@gmail.com
- 🔗 GitHub: [Link to repo]
- 📖 Documentation: See notebooks/

---

**Last Updated:** March 2026
**License:** MIT
