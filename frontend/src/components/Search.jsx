import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { search as performSearch, getSearchHistory } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import { 
  Search as SearchIcon, 
  Loader2, 
  ExternalLink, 
  Clock,
  History,
  Sparkles
} from 'lucide-react'

export default function Search() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(10)
  const [namespace, setNamespace] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  
  // Search history query
  const { data: historyData } = useQuery({
    queryKey: ['search-history'],
    queryFn: () => getSearchHistory(10),
  })
  
  // Search mutation
  const searchMutation = useMutation({
    mutationFn: () => performSearch(query, topK, namespace),
    onSuccess: (data) => {
      setSearchResults(data)
    },
  })
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (query) {
      searchMutation.mutate()
    }
  }
  
  const handleHistoryClick = (historyQuery) => {
    setQuery(historyQuery)
    searchMutation.mutate({ query: historyQuery, topK, namespace })
  }
  
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Semantic Search</h1>
        <p className="text-muted-foreground mt-1">
          Search your scraped content using natural language
        </p>
      </div>
      
      {/* Search Form */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <SearchIcon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Search Query</CardTitle>
              <CardDescription>
                Ask questions about your scraped content
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="What are you looking for?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={searchMutation.isPending}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={searchMutation.isPending || !query}
              >
                {searchMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <SearchIcon className="w-4 h-4" />
                )}
              </Button>
            </div>
            
            {/* Advanced Options */}
            <details className="text-sm">
              <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                Advanced Options
              </summary>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Results Count</label>
                  <Input
                    type="number"
                    min="1"
                    max="50"
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value))}
                    disabled={searchMutation.isPending}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Namespace (Job ID)</label>
                  <Input
                    type="text"
                    placeholder="job_123 or leave empty"
                    value={namespace}
                    onChange={(e) => setNamespace(e.target.value)}
                    disabled={searchMutation.isPending}
                  />
                </div>
              </div>
            </details>
          </form>
        </CardContent>
      </Card>
      
      {/* Search Results */}
      {searchMutation.isError && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="text-destructive text-sm">
              Error: {searchMutation.error.message}
            </div>
          </CardContent>
        </Card>
      )}
      
      {searchResults && (
        <div className="space-y-4">
          {/* Results Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">
                Search Results
              </h2>
              <p className="text-sm text-muted-foreground">
                Found {searchResults.count} results in {searchResults.response_time_ms.toFixed(0)}ms
              </p>
            </div>
            <Badge variant="outline" className="flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Semantic Search
            </Badge>
          </div>
          
          {/* Results List */}
          {searchResults.results.length > 0 ? (
            <div className="space-y-4">
              {searchResults.results.map((result, index) => (
                <Card key={result.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      {/* Header */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <a
                            href={result.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-semibold hover:text-primary flex items-center gap-2 group"
                          >
                            {result.source.title || result.source.url}
                            <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </a>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-muted-foreground">
                              {result.source.domain}
                            </span>
                            <span className="text-xs text-muted-foreground">•</span>
                            <span className="text-xs text-muted-foreground">
                              Chunk {result.source.chunk_index + 1}
                            </span>
                          </div>
                        </div>
                        <Badge 
                          variant="outline" 
                          className={
                            result.score > 0.8 
                              ? 'border-green-500 text-green-700' 
                              : result.score > 0.6 
                              ? 'border-yellow-500 text-yellow-700'
                              : 'border-gray-500 text-gray-700'
                          }
                        >
                          {(result.score * 100).toFixed(0)}% match
                        </Badge>
                      </div>
                      
                      {/* Content */}
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {result.text}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                No results found. Try a different query or scrape more content first.
              </CardContent>
            </Card>
          )}
        </div>
      )}
      
      {/* Search History */}
      {historyData && historyData.searches && historyData.searches.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-muted-foreground" />
              <CardTitle className="text-lg">Recent Searches</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {historyData.searches.map((item, index) => (
                <button
                  key={index}
                  onClick={() => handleHistoryClick(item.query)}
                  className="w-full flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors text-sm"
                  disabled={searchMutation.isPending}
                >
                  <div className="flex items-center gap-3 flex-1 text-left">
                    <Clock className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                    <span className="truncate">{item.query}</span>
                  </div>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <span className="text-xs">{item.results_count} results</span>
                    <span className="text-xs">{item.response_time_ms.toFixed(0)}ms</span>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* No Data Message */}
      {!searchMutation.isPending && !searchResults && (
        <Card>
          <CardContent className="pt-6 text-center">
            <SearchIcon className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ready to Search</h3>
            <p className="text-sm text-muted-foreground">
              Enter a query above to search through your scraped content.
              Make sure you've scraped some websites first!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}


