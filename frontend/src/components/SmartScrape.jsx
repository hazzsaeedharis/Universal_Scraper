import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { startSmartScrape } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { Sparkles, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

export default function SmartScrape() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [maxSites, setMaxSites] = useState(3)
  const [maxPagesPerSite, setMaxPagesPerSite] = useState(50)
  const [scraperMethod, setScraperMethod] = useState('httpx')
  
  const mutation = useMutation({
    mutationFn: () => startSmartScrape(query, maxSites, maxPagesPerSite, scraperMethod),
    onSuccess: (data) => {
      setTimeout(() => {
        navigate(`/jobs/${data.job_id}`)
      }, 1500)
    },
  })
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (query) {
      mutation.mutate()
    }
  }
  
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Smart Scrape</h1>
        <p className="text-muted-foreground mt-1">
          AI-powered web scraping based on natural language queries
        </p>
      </div>
      
      {/* Alert Banner */}
      <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-900">
          <p className="font-medium mb-1">Note: Smart Scrape requires search API integration</p>
          <p className="text-blue-700">
            This feature uses AI to find and scrape relevant websites based on your query. 
            Currently requires additional setup with a search API (Google Custom Search, Bing, etc.).
          </p>
        </div>
      </div>
      
      {/* Form */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <CardTitle>Describe What You're Looking For</CardTitle>
              <CardDescription>
                AI will find and scrape relevant websites for you
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Query Input */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Search Query</label>
              <Input
                type="text"
                placeholder="e.g., beach opening hours in Germany, latest AI research papers"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={mutation.isPending}
                required
              />
              <p className="text-xs text-muted-foreground">
                Describe what information you want to find and scrape
              </p>
            </div>
            
            {/* Settings */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Sites</label>
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={maxSites}
                  onChange={(e) => setMaxSites(parseInt(e.target.value))}
                  disabled={mutation.isPending}
                />
                <p className="text-xs text-muted-foreground">
                  Number of websites to scrape (1-10)
                </p>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Pages Per Site</label>
                <Input
                  type="number"
                  min="1"
                  max="200"
                  value={maxPagesPerSite}
                  onChange={(e) => setMaxPagesPerSite(parseInt(e.target.value))}
                  disabled={mutation.isPending}
                />
                <p className="text-xs text-muted-foreground">
                  Max pages to scrape per site
                </p>
              </div>
            </div>
            
            {/* Scraper Method Selector */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Scraping Method</label>
              <select
                value={scraperMethod}
                onChange={(e) => setScraperMethod(e.target.value)}
                disabled={mutation.isPending}
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="httpx">Fast (httpx - static HTML)</option>
                <option value="playwright">Comprehensive (Playwright - JavaScript enabled)</option>
              </select>
              <p className="text-xs text-muted-foreground">
                {scraperMethod === 'httpx' 
                  ? 'Fast method for static websites. May miss JavaScript-loaded content.' 
                  : 'Slower but handles modern SPAs and JavaScript-rendered content.'}
              </p>
            </div>
            
            {/* Status Messages */}
            {mutation.isError && (
              <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
                Error: {mutation.error.message}
              </div>
            )}
            
            {mutation.isSuccess && (
              <div className="p-4 rounded-lg bg-green-50 text-green-700 text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Smart scraping job started! Redirecting to job monitor...
              </div>
            )}
            
            {/* Submit Button */}
            <Button
              type="submit"
              disabled={mutation.isPending || !query}
              className="w-full"
              size="lg"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Starting Smart Scrape...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Start Smart Scraping
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
      
      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">How it works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>1. Enter a natural language query describing what you're looking for</p>
          <p>2. AI analyzes your query and generates optimal search queries</p>
          <p>3. The system searches the web and ranks results by relevance</p>
          <p>4. Top websites are automatically scraped and processed</p>
          <p>5. Content is indexed for semantic search and question answering</p>
        </CardContent>
      </Card>
      
      {/* Examples Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Example Queries</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              'Best practices for React performance optimization',
              'Restaurant opening hours in Paris city center',
              'Latest developments in renewable energy technology',
              'Python asyncio tutorial and examples',
              'COVID-19 vaccination requirements by country',
            ].map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className="w-full text-left p-3 rounded-lg border hover:bg-accent/50 transition-colors text-sm"
                disabled={mutation.isPending}
              >
                {example}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


