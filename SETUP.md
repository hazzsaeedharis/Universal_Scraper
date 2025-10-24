# Quick Setup Guide

Get Universal Scraper running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- Groq API Key: [Get it here](https://console.groq.com)
- Pinecone API Key: [Get it here](https://www.pinecone.io)

## Step 1: Clone and Navigate

```bash
cd Universal_Scraper
```

## Step 2: Configure Environment

Create a `.env` file in the root directory:

```bash
# Copy and edit the following:

# API Keys (REQUIRED)
GROQ_API_KEY=gsk_your_actual_groq_key_here
PINECONE_API_KEY=your_pinecone_key_here

# Pinecone Configuration  
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=universal-scraper

# Optional - defaults are fine
DATABASE_URL=sqlite+aiosqlite:///./scraper.db
DATA_STORAGE_PATH=./data
MAX_DEPTH=3
REQUEST_TIMEOUT=30
HOST=0.0.0.0
PORT=8000
```

## Step 3: Create Pinecone Index

1. Go to [Pinecone Console](https://app.pinecone.io)
2. Click **Create Index**
3. Configure:
   - **Name**: `universal-scraper`
   - **Dimensions**: `384`
   - **Metric**: `cosine`
   - **Region**: Any (e.g., us-west1-gcp)
4. Click **Create Index**

## Step 4: Install Dependencies

### Backend

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
cd ..
```

## Step 5: Run the Application

### Option A: Using Startup Script (Recommended)

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Step 6: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Quick Test

1. Open http://localhost:5173
2. Click **Direct Scrape**
3. Enter a URL: `https://example.com`
4. Click **Start Scraping**
5. Monitor progress in **Job Monitor**
6. Search content in **Search** tab

## Common Issues

### "Pinecone index not found"
- Make sure you created the index with dimension **384** (not 1536!)
- Verify index name matches your `.env` file

### "Groq API key invalid"
- Double-check your API key at [console.groq.com](https://console.groq.com)
- Make sure there are no extra spaces in `.env`

### "Module not found" errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### Frontend won't start
- Check Node version: `node --version` (should be 18+)
- Delete `node_modules` and run `npm install` again

### Port already in use
- Change port in `.env` (backend) or `vite.config.js` (frontend)
- Or stop the process using the port

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the [API documentation](http://localhost:8000/docs) when backend is running
- Try the semantic search after scraping some content
- Explore the RAG pipeline in the code

## Need Help?

- Check backend logs: `backend.log`
- Check frontend logs: `frontend.log`
- Review browser console for frontend errors
- Open an issue on GitHub

---

**Happy Scraping! 🚀**

