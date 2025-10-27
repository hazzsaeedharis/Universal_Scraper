import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { startDirectScrape } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { Link2, Loader2, CheckCircle2 } from 'lucide-react'

export default function DirectScrape() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [maxDepth, setMaxDepth] = useState(3)
  const [maxPages, setMaxPages] = useState(100)
  const [scraperMethod, setScraperMethod] = useState('httpx')
  
  const mutation = useMutation({
    mutationFn: () => startDirectScrape(url, maxDepth, maxPages, scraperMethod),
    onSuccess: (data) => {
      setTimeout(() => {
        navigate(`/jobs/${data.job_id}`)
      }, 1500)
    },
  })
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (url) {
      mutation.mutate()
    }
  }
  
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Direct Scrape</h1>
        <p className="text-muted-foreground mt-1">
          Scrape a specific website and follow internal links
        </p>
      </div>
      
      {/* Form */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Link2 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Enter Website URL</CardTitle>
              <CardDescription>
                Provide the starting URL to crawl the entire domain
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* URL Input */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Website URL</label>
              <Input
                type="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={mutation.isPending}
                required
              />
            </div>
            
            {/* Settings */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Depth</label>
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                  disabled={mutation.isPending}
                />
                <p className="text-xs text-muted-foreground">
                  How deep to follow links (1-10)
                </p>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Pages</label>
                <Input
                  type="number"
                  min="1"
                  max="1000"
                  value={maxPages}
                  onChange={(e) => setMaxPages(parseInt(e.target.value))}
                  disabled={mutation.isPending}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum pages to scrape
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
                  : 'Slower but handles modern SPAs and JavaScript-rendered content (e.g., React, KFC, BrewDog).'}
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
                Scraping job started! Redirecting to job monitor...
              </div>
            )}
            
            {/* Submit Button */}
            <Button
              type="submit"
              disabled={mutation.isPending || !url}
              className="w-full"
              size="lg"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Starting Scrape...
                </>
              ) : (
                <>
                  <Link2 className="w-4 h-4 mr-2" />
                  Start Scraping
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
          <p>1. Enter the starting URL of the website you want to scrape</p>
          <p>2. The crawler will visit the page and extract all internal links</p>
          <p>3. It will follow those links up to the specified depth</p>
          <p>4. Content is saved locally and processed into RAG embeddings</p>
          <p>5. You can then search the scraped content semantically</p>
        </CardContent>
      </Card>
    </div>
  )
}

