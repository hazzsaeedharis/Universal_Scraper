import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { search as performSearch, getSearchHistory, getAIAnswer, getNamespaces } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import StructuredDataViewer from './StructuredDataViewer'
import { 
  Search as SearchIcon, 
  Loader2, 
  ExternalLink, 
  Clock,
  History,
  Sparkles,
  Brain,
  CheckCircle2
} from 'lucide-react'

export default function Search() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(10)
  const [namespace, setNamespace] = useState('job_1')
  const [searchResults, setSearchResults] = useState(null)
  
  // Search history query
  const { data: historyData } = useQuery({
    queryKey: ['search-history'],
    queryFn: () => getSearchHistory(10),
  })
  
  // Namespaces query
  const { data: namespacesData } = useQuery({
    queryKey: ['namespaces'],
    queryFn: () => getNamespaces(),
  })
  
  // Auto-select first namespace if available
  useEffect(() => {
    if (namespacesData?.namespaces?.length > 0 && !namespace) {
      setNamespace(namespacesData.namespaces[0].namespace)
    }
  }, [namespacesData, namespace])
  
  // Search mutation (traditional semantic search)
  const searchMutation = useMutation({
    mutationFn: ({ q, k, ns }) => performSearch(q, k, ns),
    onSuccess: (data) => {
      setSearchResults(data)
    },
  })
  
  // AI answer mutation (RAG with Groq)
  const aiAnswerMutation = useMutation({
    mutationFn: ({ q, k, ns }) => getAIAnswer(q, k, ns),
    onSuccess: (data) => {
      setSearchResults({ 
        results: data.search_results || [], 
        count: data.search_results?.length || 0,
        response_time_ms: data.response_time_ms
      })
    }
  })
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (query) {
      // Clear previous results
      setSearchResults(null)
      // Use AI answer by default
      aiAnswerMutation.mutate({ q: query, k: 5, ns: namespace })
    }
  }
  
  const handleHistoryClick = (historyQuery) => {
    setQuery(historyQuery)
    aiAnswerMutation.mutate({ q: historyQuery, k: 5, ns: namespace })
  }
  
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Brain className="w-8 h-8" />
          AI-Powered Search
        </h1>
        <p className="text-muted-foreground mt-1">
          Ask questions and get intelligent answers from your scraped content
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
                placeholder="Ask a question about your scraped content..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={aiAnswerMutation.isPending}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={aiAnswerMutation.isPending || !query}
              >
                {aiAnswerMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4" />
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
                    disabled={aiAnswerMutation.isPending}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Namespace (Job ID)</label>
                  <select
                    value={namespace}
                    onChange={(e) => setNamespace(e.target.value)}
                    disabled={aiAnswerMutation.isPending}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {namespacesData?.namespaces?.map((ns) => (
                      <option key={ns.namespace} value={ns.namespace}>
                        {ns.namespace} ({ns.vector_count.toLocaleString()} vectors)
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-muted-foreground">
                    Select which scraping job to search within
                  </p>
                </div>
              </div>
            </details>
          </form>
        </CardContent>
      </Card>
      
      {/* AI Answer Section */}
      {aiAnswerMutation.isPending && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <div>
                <p className="font-medium">Generating AI answer...</p>
                <p className="text-sm text-muted-foreground">Searching content and synthesizing response</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {aiAnswerMutation.isError && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="text-destructive text-sm">
              Error: {aiAnswerMutation.error.message}
            </div>
          </CardContent>
        </Card>
      )}
      
      {aiAnswerMutation.data && (
        <Card className="border-primary shadow-lg">
          <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                <Brain className="w-5 h-5 text-primary-foreground" />
              </div>
              <div className="flex-1">
                <CardTitle className="flex items-center gap-2">
                  AI Answer
                  <Badge variant="secondary" className="flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Powered by Groq
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Generated from {aiAnswerMutation.data?.sources?.length || 0} sources in {aiAnswerMutation.data?.response_time_ms?.toFixed(0) || 0}ms
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {/* AI Generated Answer */}
            <div className="prose prose-sm max-w-none mb-6">
              <p className="text-base leading-relaxed whitespace-pre-wrap">{aiAnswerMutation.data?.answer}</p>
            </div>
            
            {/* Sources */}
            {aiAnswerMutation.data?.sources && aiAnswerMutation.data.sources.length > 0 && (
              <div className="border-t pt-4">
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <ExternalLink className="w-4 h-4" />
                  Sources
                </h4>
                <div className="space-y-2">
                  {aiAnswerMutation.data.sources.map((source, index) => (
                    <a
                      key={index}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors group"
                    >
                      <Badge variant="outline" className="mt-0.5">
                        {index + 1}
                      </Badge>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                          {source.title}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">{source.domain}</p>
                      </div>
                      <Badge variant="outline" className="shrink-0">
                        {(source.score * 100).toFixed(0)}%
                      </Badge>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Structured Data Viewer */}
      {aiAnswerMutation.data?.has_structured_data && (
        <StructuredDataViewer
          data={aiAnswerMutation.data.structured_data}
          dataType={aiAnswerMutation.data.data_type}
          confidence={aiAnswerMutation.data.confidence || 0}
        />
      )}
      
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
                Found {searchResults.count} results in {searchResults.response_time_ms?.toFixed(0) || 0}ms
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
      {!aiAnswerMutation.isPending && !aiAnswerMutation.data && (
        <Card>
          <CardContent className="pt-6 text-center">
            <Brain className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ask Me Anything</h3>
            <p className="text-sm text-muted-foreground">
              Ask questions about your scraped content and get AI-powered answers with source citations.
              <br />
              Make sure you've scraped some websites first!
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}


