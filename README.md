# Universal Scraper

An AI-powered web scraper with RAG (Retrieval-Augmented Generation) capabilities for semantic search over scraped content.

## Features

- **Direct Scraping**: Scrape specific websites by URL with configurable depth and page limits
- **Smart Scraping**: AI-powered scraping based on natural language queries (requires search API integration)
- **Real-time Monitoring**: WebSocket-based job monitoring with live progress updates
- **RAG Integration**: Automatic content chunking and embedding using sentence transformers
- **Semantic Search**: Natural language search over all scraped content using Pinecone vector database
- **Modern UI**: Beautiful React frontend with Tailwind CSS and shadcn/ui components
- **Job Management**: Track all scraping jobs with detailed statistics and scraped URL lists

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Async database ORM
- **Pinecone**: Vector database for embeddings
- **Groq**: AI model for intelligent search and analysis
- **Sentence Transformers**: Text embedding models
- **BeautifulSoup4**: HTML parsing
- **Playwright**: Browser automation for JavaScript-heavy sites
- **HTTPX**: Async HTTP client

### Frontend
- **React 18**: Modern UI library
- **Vite**: Fast build tool
- **TanStack Query**: Data fetching and caching
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide Icons**: Beautiful icon library
- **Zustand**: State management

## Prerequisites

- Python 3.9+
- Node.js 18+
- Groq API key (get from [console.groq.com](https://console.groq.com))
- Pinecone API key (get from [pinecone.io](https://www.pinecone.io))

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Universal_Scraper
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (optional, for JavaScript-heavy sites)
playwright install
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# API Keys (REQUIRED)
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Pinecone Configuration
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=universal-scraper

# Database
DATABASE_URL=sqlite+aiosqlite:///./scraper.db

# Storage
DATA_STORAGE_PATH=./data

# Scraper Configuration
MAX_CONCURRENT_SCRAPES=5
MAX_DEPTH=3
REQUEST_TIMEOUT=30
RATE_LIMIT_DELAY=1.0
USER_AGENT=UniversalScraper/1.0

# RAG Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=10

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

### 5. Create Pinecone Index

Before running the application, create a Pinecone index:

1. Log in to [Pinecone Console](https://app.pinecone.io)
2. Create a new index with the following settings:
   - **Name**: `universal-scraper` (or match your `PINECONE_INDEX_NAME`)
   - **Dimensions**: `384` (for all-MiniLM-L6-v2 model)
   - **Metric**: `cosine`
   - **Region**: Choose your preferred region

## Running the Application

### Option 1: Using Startup Scripts (Recommended)

#### On macOS/Linux:

```bash
chmod +x start.sh
./start.sh
```

#### On Windows:

```cmd
start.bat
```

### Option 2: Manual Start

#### Terminal 1 - Backend:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run backend server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend:

```bash
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

### 1. Direct Scraping

1. Navigate to **Direct Scrape** in the sidebar
2. Enter a website URL (e.g., `https://example.com`)
3. Configure settings:
   - **Max Depth**: How many levels of links to follow (1-10)
   - **Max Pages**: Maximum number of pages to scrape
4. Click **Start Scraping**
5. You'll be redirected to the Job Monitor to track progress

### 2. Semantic Search

1. First, scrape some websites using Direct Scrape
2. Navigate to **Search** in the sidebar
3. Enter a natural language query
4. View semantically relevant results from your scraped content
5. Click on sources to visit the original pages

### 3. Job Monitoring

1. Navigate to **Job Monitor** in the sidebar
2. View all scraping jobs and their status
3. Click on a job to see detailed information
4. Monitor real-time progress with WebSocket updates
5. View all scraped URLs and their status

### 4. Smart Scraping (Advanced)

⚠️ **Note**: Smart Scraping requires additional setup with a search API (Google Custom Search, Bing, etc.)

1. Navigate to **Smart Scrape** in the sidebar
2. Enter a natural language query describing what you want to find
3. The AI will generate optimal search queries
4. Relevant websites will be automatically discovered and scraped

## API Endpoints

### Scraping

- `POST /scrape/direct` - Start direct scraping job
- `POST /scrape/smart` - Start smart scraping job

### Jobs

- `GET /jobs/` - List all jobs
- `GET /jobs/{job_id}` - Get job details
- `GET /jobs/{job_id}/urls` - Get scraped URLs for a job
- `GET /jobs/stats/overview` - Get system statistics
- `WS /jobs/ws/{job_id}` - WebSocket for real-time job updates

### Search

- `POST /search/` - Perform semantic search
- `GET /search/history` - Get recent search queries

## Project Structure

```
Universal_Scraper/
├── backend/
│   ├── ai/                  # AI agents (Groq, search, site selection)
│   ├── api/                 # FastAPI routes and schemas
│   ├── rag/                 # RAG pipeline (chunking, embedding, retrieval)
│   ├── scraper/             # Web scraping logic
│   ├── storage/             # Database and file storage
│   ├── utils/               # Utilities (logging, validation)
│   ├── config.py            # Configuration management
│   └── main.py              # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── lib/             # API client and utilities
│   │   ├── App.jsx          # Main app component
│   │   └── main.jsx         # Entry point
│   ├── index.html
│   └── package.json
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md               # This file
```

## Architecture

### Backend Flow

1. **API Layer**: FastAPI receives scraping requests
2. **Background Tasks**: Jobs run asynchronously
3. **Crawler**: Fetches and parses web pages
4. **Storage**: Saves raw content locally and metadata to SQLite
5. **RAG Pipeline**:
   - Chunks text content
   - Generates embeddings using sentence transformers
   - Stores vectors in Pinecone
6. **WebSocket**: Broadcasts real-time progress updates

### Frontend Flow

1. **User Interface**: React components with Tailwind CSS
2. **API Client**: Axios for HTTP requests
3. **State Management**: TanStack Query for server state, Zustand for local state
4. **Real-time Updates**: WebSocket connection for job monitoring
5. **Routing**: React Router for navigation

## Configuration

### Scraper Settings

- `MAX_CONCURRENT_SCRAPES`: Number of parallel scraping jobs
- `MAX_DEPTH`: Default maximum crawl depth
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds
- `RATE_LIMIT_DELAY`: Delay between requests in seconds

### RAG Settings

- `EMBEDDING_MODEL`: Sentence transformer model name
- `CHUNK_SIZE`: Text chunk size for embedding
- `CHUNK_OVERLAP`: Overlap between chunks
- `TOP_K_RESULTS`: Default number of search results

## Troubleshooting

### Backend Issues

**Error: "Pinecone index not found"**
- Make sure you created the Pinecone index with the correct name and dimensions (384)

**Error: "Database connection failed"**
- Ensure the `DATA_STORAGE_PATH` directory exists or the app has write permissions

**Error: "Groq API key invalid"**
- Verify your API key in the `.env` file
- Check your API key at [console.groq.com](https://console.groq.com)

### Frontend Issues

**Error: "Network Error" or "Failed to fetch"**
- Ensure the backend server is running on port 8000
- Check CORS settings in `backend/main.py`

**WebSocket not connecting**
- Verify the WebSocket URL in `JobMonitor.jsx`
- Check browser console for connection errors

### Scraping Issues

**Pages not being scraped**
- Check if the website blocks scrapers (User-Agent, robots.txt)
- Try increasing `REQUEST_TIMEOUT`
- For JavaScript-heavy sites, Playwright integration may be needed

## Development

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests (if configured)
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
black backend/

# Frontend
cd frontend
npm run lint
```

## Performance Tips

1. **Adjust Concurrency**: Increase `MAX_CONCURRENT_SCRAPES` for faster scraping
2. **Rate Limiting**: Adjust `RATE_LIMIT_DELAY` to be respectful to target servers
3. **Chunk Size**: Smaller chunks = more granular search but more vectors
4. **Top K Results**: Balance between relevance and response time

## Security Considerations

- Never commit `.env` files to version control
- Use strong API keys and rotate them regularly
- Be respectful of robots.txt and rate limits
- Consider legal implications of web scraping in your jurisdiction

## Future Enhancements

- [ ] Search API integration for Smart Scraping
- [ ] PDF and document scraping support
- [ ] Export functionality (JSON, CSV, Markdown)
- [ ] Scheduled scraping jobs
- [ ] User authentication and multi-tenancy
- [ ] Advanced filtering and search options
- [ ] Mobile-responsive improvements
- [ ] Docker containerization
- [ ] Cloud deployment guides (AWS, GCP, Azure)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, React, and AI**


