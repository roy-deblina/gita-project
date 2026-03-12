# 🚀 Production-Ready: Supabase Cloud Database Setup

Your Gita RAG app now uses **Supabase** (free PostgreSQL) for persistent analytics and reviews. This ensures:

✅ **Data persists forever** (no loss on app restart)  
✅ **Production-grade** (automatic backups, scalable)  
✅ **Completely free** tier (100GB storage, 500K API calls/month)  
✅ **Easy setup** (10 minutes to production)

---

## Step 1: Create Free Supabase Account

1. Go to **https://supabase.com**
2. Click **Sign Up** with email or GitHub
3. Create a new project:
   - **Project name:** `gita-project`
   - **Password:** Strong password (save this!)
   - **Region:** Choose closest to users (e.g., `us-east-1`)
4. Wait for project to initialize (~2 minutes)

---

## Step 2: Create Database Tables

Once your project is created, go to **SQL Editor** and run this script:

```sql
-- Create reviews table
CREATE TABLE reviews (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  query TEXT NOT NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  email TEXT,
  sentiment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create page_visits table
CREATE TABLE page_visits (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  session_id TEXT,
  user_agent TEXT,
  visit_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create query_clicks table
CREATE TABLE query_clicks (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  query TEXT NOT NULL,
  session_id TEXT,
  verses_returned INTEGER,
  confidence FLOAT,
  latency_ms FLOAT,
  click_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable realtime for all tables (optional but cool!)
ALTER PUBLICATION supabase_realtime ADD TABLE reviews;
ALTER PUBLICATION supabase_realtime ADD TABLE page_visits;
ALTER PUBLICATION supabase_realtime ADD TABLE query_clicks;
```

✅ Click **Run** - tables are now created!

---

## Step 3: Get Your API Credentials

1. Go to **Settings** → **API** in sidebar
2. Copy these two values:
   - **Project URL** (e.g., `https://abcdefgh.supabase.co`)
   - **API Key** → `anon` public key (⚠️ NOT secret!)

```
SUPABASE_URL = "https://abcdefgh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Step 4: Add to Local Secrets

Create/update `.streamlit/secrets.toml`:

```toml
ADMIN_PASSWORD = "Deblina1176"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
```

---

## Step 5: Test Locally

```bash
cd /Users/Guddus/Documents/NW-MSDS/Gita-project
streamlit run streamlit_app.py
```

Try these actions:
1. ✅ Search for a verse → **query_clicks table gets entry**
2. ✅ Leave a review → **reviews table gets entry**
3. ✅ Visit any page → **page_visits table gets entry**

Go to **Supabase Dashboard** → **Table Editor** → See your data appear in real-time!

---

## Step 6: Deploy to Streamlit Cloud

### 6.1 Push to GitHub (without secrets!)

```bash
git add .
git commit -m "Add Supabase for production analytics"
git push origin main
```

**Note:** `.streamlit/secrets.toml` won't push (protected by `.gitignore`)

### 6.2 Add Secrets in Streamlit Cloud

In Streamlit Cloud dashboard:
1. Select your app
2. Click **Settings** (⋮ menu)
3. Go to **Secrets** tab
4. Paste:
```toml
ADMIN_PASSWORD = "Deblina1176"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
```
5. Click **Save** - app restarts automatically

✅ **Done!** Your app is now production-ready with persistent data!

---

## How It Works

### Local Development
1. **If Supabase configured?** → Uses cloud database (Supabase)
2. **If not?** → Falls back to local SQLite automatically
3. **Result:** No breaking changes, seamless experience

### Production (Streamlit Cloud)
1. Secrets pulled from Streamlit Cloud dashboard
2. Analytics written to Supabase
3. **Data persists forever** (not ephemeral)
4. ✅ Users can be created and destroyed anytime
5. ✅ All reviews and analytics preserved

---

## Monitoring Your Analytics

### Supabase Dashboard → Table Editor
- Real-time view of all analytics
- Export as CSV
- Filter and search

### Streamlit App → Analytics Tab
- Users see aggregated stats (popular queries, sentiment)
- Real-time updates from Supabase

---

## Scaling (Optional Future)

Supabase free tier includes:
- **100 GB storage**
- **500K API calls/month**
- Enough for 50K+ users

If you outgrow:
1. Upgrade Supabase tier ($5-25/month)
2. Or use Supabase's generous free tier longer
3. No code changes needed!

---

## Troubleshooting

### "Supabase not configured. Using local SQLite"
**Cause:** Missing `SUPABASE_URL` or `SUPABASE_KEY`  
**Fix:** Check `.streamlit/secrets.toml` has correct credentials

### App works locally but not on Streamlit Cloud
**Cause:** Secrets not added to Streamlit Cloud  
**Fix:** Go to App Settings → Secrets → add SUPABASE_URL and SUPABASE_KEY

### Data not persisting on Streamlit Cloud
**Cause:** Using SQLite (Streamlit ephemeral filesystem)  
**Fix:** Ensure Supabase credentials are correct in Streamlit Cloud secrets

### "Table already exists"
**Cause:** Running SQL script twice  
**Fix:** Just ignore - tables are created, move on

---

## Summary

| Component | Before | After |
|-----------|--------|-------|
| **Analytics Storage** | Local SQLite (lost on reboot) | Supabase Cloud (persistent) |
| **Data Persistence** | ❌ Lost | ✅ Forever |
| **Scalability** | Single user | 1000s of concurrent users |
| **Cost** | Free | Free forever tier |
| **Setup Time** | Done | 10 minutes |

---

## 🎉 You're Production-Ready!

Your app now has:
- ✅ Free cloud database (Supabase)
- ✅ Persistent analytics (never lost)
- ✅ Production-grade backups
- ✅ Real-time dashboard
- ✅ Just a link to share

**Next:** Deploy to Streamlit Cloud following [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)

**Questions?** Check Supabase docs: https://supabase.com/docs
