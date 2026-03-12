# 🚀 Streamlit Cloud Deployment Guide

Deploy your Gita RAG app to Streamlit Cloud in 5 minutes with **persistent cloud analytics**!

---

## Prerequisites: Set Up Cloud Database (10 minutes)

⚠️ **BEFORE DEPLOYING:** Follow [SUPABASE_SETUP.md](SUPABASE_SETUP.md) to:
1. Create free Supabase account
2. Create database tables
3. Get API credentials (SUPABASE_URL & SUPABASE_KEY)

This ensures your analytics and reviews **persist forever** (never lost).

---

## Step 1: Push Your Code to GitHub

### Prerequisites
- GitHub account (free at https://github.com)
- Git installed on your machine

### Commands
```bash
cd /Users/Guddus/Documents/NW-MSDS/Gita-project

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Deploy Gita RAG to Streamlit Cloud"

# Create a new repository on GitHub at https://github.com/new
# Name it: gita-project
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/gita-project.git
git branch -M main
git push -u origin main
```

**Note:** Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Step 2: Create `.streamlit/secrets.toml` for Production

On Streamlit Cloud, secrets are managed through the web UI (NOT by uploading the file).

### What NOT to do:
❌ Don't push `.streamlit/secrets.toml` to GitHub (contains sensitive password)

### What TO do:
✅ Create `.gitignore` to exclude secrets:

```bash
# In project root, create/update .gitignore
echo ".streamlit/secrets.toml" >> .gitignore
git add .gitignore
git commit -m "Exclude secrets from version control"
git push
```

---

## Step 3: Deploy to Streamlit Cloud

### 3.1 Go to Streamlit Cloud
- Visit https://share.streamlit.io
- Sign in with GitHub (or create free account)

### 3.2 Click "New app"
- **Repository:** Select `YOUR_USERNAME/gita-project`
- **Branch:** `main`
- **Main file path:** `streamlit_app.py`

### 3.3 Click "Deploy" 
Streamlit will:
1. Clone your GitHub repo
2. Install dependencies from `requirements.txt`
3. Launch your app

**Wait ~2-3 minutes for deployment to complete**

---

## Step 4: Add Secrets to Streamlit Cloud

⚠️ **IMPORTANT:** Your app needs both admin password AND cloud database credentials!

### How to add secrets:

1. **In Streamlit Cloud dashboard**, find your app
2. Click the **three dots (⋮)** → **Settings**
3. Navigate to **Secrets** tab
4. Add ALL of these:
```toml
ADMIN_PASSWORD = "Deblina1176"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
```

5. Click **Save**

Streamlit will automatically restart your app with the secrets.

---

## Step 5: Test Your Deployment

1. **Open your app URL** (shown in Streamlit Cloud dashboard)
   - Format: `https://gita-project-RANDOMSTRING.streamlit.app`

2. **Test as public user:**
   - Access Wisdom, Research, Analytics tabs (should work freely)
   - Try a search query (logs to Supabase)
   - Leave a review (persists to Supabase)

3. **Verify analytics in Supabase:**
   - Go to Supabase dashboard → Table Editor
   - See your queries and reviews appear in real-time
   - ✅ Confirms data is persisting to cloud

4. **Test as admin:**
   - Click "Architecture" tab
   - Enter password: `Deblina1176`
   - Should see admin dashboard

5. **Share the link:**
   - Your public URL can be shared with anyone
   - They can use the app without logging in
   - All reviews/analytics automatically saved
   - Only you can access admin panel (password protected)

---

## Troubleshooting

### "ModuleNotFoundError: No module named..."
**Solution:** Your `requirements.txt` is missing a package
```bash
pip install MISSING_PACKAGE
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```
Then redeploy from Streamlit Cloud settings.

### "retriever_state.pkl not found"
**Solution:** File might be too large for GitHub
```bash
# Add to .gitignore if > 100MB
echo "data/retriever_state.pkl" >> .gitignore

# Instead, Streamlit Cloud will build it on first run
# Or upload via git-lfs if needed
```

### App loads but password doesn't work
**Solution:** Check Streamlit Cloud secrets:
1. Go to Settings → Secrets
2. Verify `ADMIN_PASSWORD = "Deblina1176"` exactly
3. Wait 1 minute for restart
4. Try again

### Port 8501 errors (local testing)
**Solution:** Kill existing process
```bash
lsof -ti:8501 | xargs kill -9
streamlit run streamlit_app.py
```

---

## Advanced: Custom Domain (Optional)

Streamlit Cloud supports custom domains:
1. Purchase a domain (e.g., gita-app.com)
2. In Streamlit Cloud settings → Domain
3. Follow DNS setup instructions

---

## Environment Variables (Production Tips)

For production, you can also use environment variables instead of secrets file:

```bash
# On your local machine or Streamlit Cloud secrets:
export ADMIN_PASSWORD="Deblina1176"
```

Your app's fallback logic handles this:
1. First checks `.streamlit/secrets.toml`
2. Then checks `ADMIN_PASSWORD` env var
3. Falls back to default (hardcoded as backup)

---

## Monitoring & Updates

### View app logs:
- Streamlit Cloud dashboard → Your app → **View logs**

### Update your app:
```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push origin main
```
Streamlit Cloud auto-deploys on push! (usually within 1 minute)

### Stop/Pause the app:
- Dashboard → App settings → "Manage app" → Reboot/Delete

---

## Performance Tips

1. **Clear cache between updates:**
   ```bash
   rm -rf ~/.streamlit/cache
   ```

2. **For large embeddings (retriever_state.pkl):**
   - Consider uploading as separate data directory
   - Or use git-lfs for large files

3. **Monitor analytics:**
   - Check the Analytics tab to see user engagement
   - Review popular queries

---

## Pricing

**Streamlit Cloud is FREE for:**
- ✅ Public apps (unlimited)
- ✅ Up to 3 private apps
- ✅ Community tier support

**Pro tier** (paid) for:
- Private apps
- Custom domain
- Priority support

---

## Share Your App! 🎉

Once deployed, share your URL with:
- **Recruiters** - Shows full-stack ML/Data Science skills
- **Friends & family** - Try searching for verses
- **Social media** - Share the Gita wisdom!

**Your URL format:**
```
https://gita-project-RANDOMSTRING.streamlit.app
```

---

## Questions?

- Streamlit Docs: https://docs.streamlit.io
- GitHub Help: https://docs.github.com
- This project: Refer to README.md

---

**Status:** ✅ Your app is production-ready!
**Admin Password:** `Deblina1176`
**Time to deploy:** ~5 minutes
