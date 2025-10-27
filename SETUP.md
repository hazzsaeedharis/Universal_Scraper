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

### Playwright (Optional - for JavaScript-heavy sites)

If you plan to scrape modern websites with JavaScript (React, Vue, etc.):

```bash
# macOS/Linux
playwright install chromium

# Or with system dependencies
playwright install --with-deps chromium
```

**Note**: Playwright is optional. The scraper works fine without it using the default httpx method.

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

---

## 📖 How Scraping Works: httpx vs Playwright

Universal Scraper offers **two scraping methods** that you can choose from for each job:

### 🚀 Method 1: httpx (Fast & Simple)

**Best for**: Static HTML websites, blogs, documentation

**How it works**:
1. Sends HTTP GET request to the URL
2. Receives HTML response immediately
3. Parses HTML with BeautifulSoup
4. Extracts text, links, and metadata
5. Follows internal links recursively

**Performance**:
- ⚡ **Speed**: 1-2 seconds per page
- 💾 **Memory**: Low (~10MB)
- 🎯 **Success Rate**: 100% for static sites

**Limitations**:
- ❌ Cannot execute JavaScript
- ❌ Misses dynamically-loaded content
- ❌ Won't find JS-loaded PDF links
- ❌ Fails on modern SPAs (Single Page Apps)

**When to use**:
- News websites
- Government/institutional sites
- Documentation sites
- Simple blogs
- Wikipedia

### 🌐 Method 2: Playwright (Comprehensive)

**Best for**: Modern JavaScript-heavy websites (React, Vue, Angular)

**How it works**:
1. Launches a real Chromium browser (headless)
2. Navigates to the URL like a real user
3. **Executes all JavaScript** on the page
4. Waits for network to be idle
5. Extracts rendered HTML and all links
6. **Finds JavaScript-loaded content** (menus, PDFs, etc.)
7. Follows links recursively

**Performance**:
- 🐌 **Speed**: 5-10 seconds per page
- 💾 **Memory**: Higher (~100MB per browser)
- 🎯 **Success Rate**: 95%+ for JS-heavy sites

**Advantages**:
- ✅ Executes JavaScript
- ✅ Finds dynamically-loaded links
- ✅ Detects JS-loaded PDF menus
- ✅ Works on modern SPAs
- ✅ Bypasses basic bot detection
- ✅ Handles lazy loading

**When to use**:
- Restaurant websites (KFC, BrewDog, etc.)
- E-commerce sites
- React/Vue/Angular applications
- Sites with JavaScript menus
- Sites with dynamic content
- PDF menus loaded via JavaScript

---

## 🎯 Step-by-Step Usage Guide

### Direct Scrape (Recommended for Beginners)

1. **Navigate to Direct Scrape**
   - Open http://localhost:5173
   - Click **Direct Scrape** in the sidebar

2. **Enter Target URL**
   - Example: `https://www.kfc.de`
   - Must include `https://` or `http://`

3. **Configure Settings**
   - **Max Depth**: How many link levels to follow (1-10)
     - 1 = Only the starting page
     - 2 = Starting page + direct links
     - 3 = Starting page + links + links from those links
   - **Max Pages**: Maximum pages to scrape (1-1000)
     - Prevents infinite loops
     - Recommended: 50-100 for testing

4. **Choose Scraping Method** ⭐ NEW!
   - **httpx (Fast)**: For simple, static websites
     - Example: Wikipedia, documentation sites
   - **Playwright (Comprehensive)**: For JavaScript sites
     - Example: KFC, BrewDog, React apps
     - **Use this if the website looks modern or has menus**

5. **Start Scraping**
   - Click **Start Scraping**
   - Redirects to Job Monitor automatically

6. **Monitor Progress**
   - Watch real-time updates
   - See URLs discovered/scraped/failed
   - View current URL being processed
   - Check completion status

7. **Search Your Data**
   - Go to **Search** tab
   - Enter a question or keyword
   - Get AI-powered answers with sources

### Smart Scrape (AI-Powered)

1. **Navigate to Smart Scrape**
   - Click **Smart Scrape** in the sidebar

2. **Describe What You're Looking For**
   - Example: "Restaurant menus in Berlin"
   - Example: "COVID-19 vaccination requirements"

3. **Configure Settings**
   - **Max Sites**: How many websites to scrape (1-10)
   - **Pages Per Site**: How many pages per website (1-200)
   - **Scraping Method**: Choose httpx or Playwright

4. **Let AI Find & Scrape**
   - AI generates optimal search queries
   - Finds relevant websites
   - Scrapes them automatically
   - Indexes content for search

---

## 🏗️ Architecture: How It All Works

### The Scraping Pipeline

```
User Input (URL + Method)
    ↓
┌─────────────────────────────┐
│  Frontend (React)           │
│  - DirectScrape.jsx         │
│  - Method Selector Dropdown │
└─────────────────────────────┘
    ↓ API Call (POST /scrape/direct)
┌─────────────────────────────┐
│  Backend API (FastAPI)      │
│  - Validates method         │
│  - Creates job in database  │
│  - Starts background task   │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  Crawler                    │
│  - Manages queue & visited  │
│  - Calls fetcher for URLs   │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  Fetcher (Router)           │
│  - Routes to httpx OR       │
│  - Routes to Playwright     │
└─────────────────────────────┘
    ↓                    ↓
┌────────────┐    ┌────────────────┐
│httpx       │    │Playwright      │
│Fetcher     │    │Fetcher         │
│            │    │                │
│HTTP GET → │    │Browser Launch →│
│HTML ← ✅   │    │JS Execute →    │
│            │    │Rendered HTML ← │
└────────────┘    └────────────────┘
         ↓              ↓
    ┌─────────────────────────────┐
    │  Parser                     │
    │  - BeautifulSoup            │
    │  - Extract text & links     │
    │  - Detect PDF links         │
    └─────────────────────────────┘
              ↓
    ┌─────────────────────────────┐
    │  Storage                    │
    │  - Save to local JSON       │
    │  - Update database          │
    └─────────────────────────────┘
              ↓
    ┌─────────────────────────────┐
    │  RAG Pipeline               │
    │  1. Chunk text              │
    │  2. Generate embeddings     │
    │  3. Store in Pinecone       │
    └─────────────────────────────┘
              ↓
         ✅ Searchable!
```

### Method Selection Flow

1. **User selects method** in dropdown (httpx or playwright)
2. **Frontend sends** `scraper_method: "httpx"` or `"playwright"`
3. **Backend validates** method is valid
4. **Crawler initializes** `Fetcher(method=ScraperMethod.PLAYWRIGHT)`
5. **Fetcher routes** each URL to appropriate implementation
6. **Playwright launches browser** (if selected) and reuses it for all pages
7. **Results** are identical format regardless of method
8. **Logs show** which method was used for debugging

### PDF Detection with Playwright

**The Problem**: Many restaurant websites load PDF menus via JavaScript:

```html
<!-- JavaScript-loaded PDF link (invisible to httpx) -->
<button onclick="loadMenu('https://cdn.example.com/menu.pdf')">
  View Menu
</button>
```

**The Solution**: Playwright executes the JavaScript:

1. **Page loads** in real browser
2. **JavaScript executes** and creates PDF links
3. **Playwright extracts** all `<a href="*.pdf">` links
4. **Crawler detects** `.pdf` URLs
5. **PDF Processor** downloads and extracts text (OCR if needed)
6. **Text indexed** for RAG search

---

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

### Playwright Issues

**"Playwright not installed" error**
```bash
# Install Playwright browsers
playwright install chromium

# Or with system dependencies (recommended)
playwright install --with-deps chromium
```

**"Browser failed to launch"**
- On Linux: `playwright install-deps` (installs system dependencies)
- On macOS: `brew install playwright` (alternative installation)
- Check if Chromium path is correct in logs

**Playwright is slow**
- This is normal! Playwright is 5-10x slower than httpx
- It launches a real browser and executes JavaScript
- Use httpx for simple sites to save time

**"Timeout waiting for selector"**
- Increase timeout in `backend/config.py`: `playwright_timeout: 60000` (60 seconds)
- Some sites load slowly - this is expected
- Check if site has bot detection

**No PDF links detected with Playwright**
- Check backend logs for "Found X PDF links"
- Verify PDF link exists by manually inspecting the website
- PDF might be behind authentication or region-lock

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

