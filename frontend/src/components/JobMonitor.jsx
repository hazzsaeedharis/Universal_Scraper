import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { getJob, getJobs, getJobUrls } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { formatDate, getStatusColor, truncate } from '../lib/utils'
import { 
  Activity, 
  Loader2, 
  CheckCircle2, 
  XCircle,
  Clock,
  ExternalLink,
  RefreshCw,
  ChevronRight,
  Globe,
  FileText
} from 'lucide-react'

export default function JobMonitor() {
  const { jobId } = useParams()
  const [selectedJobId, setSelectedJobId] = useState(jobId ? parseInt(jobId) : null)
  const [wsData, setWsData] = useState(null)
  const [ws, setWs] = useState(null)
  
  // Query for job list
  const { 
    data: jobs, 
    isLoading: jobsLoading,
    refetch: refetchJobs 
  } = useQuery({
    queryKey: ['jobs', 50],
    queryFn: () => getJobs(50),
    refetchInterval: 5000, // Refetch every 5 seconds
  })
  
  // Query for selected job details
  const { 
    data: jobDetails, 
    isLoading: detailsLoading,
    refetch: refetchDetails
  } = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => getJob(selectedJobId),
    enabled: !!selectedJobId,
    refetchInterval: (data) => {
      // Stop refetching if job is completed, failed, or cancelled
      if (!data) return false
      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        return false
      }
      return 3000 // Refetch every 3 seconds for active jobs
    }
  })
  
  // Query for job URLs
  const { 
    data: jobUrls,
    refetch: refetchUrls
  } = useQuery({
    queryKey: ['job-urls', selectedJobId],
    queryFn: () => getJobUrls(selectedJobId),
    enabled: !!selectedJobId && jobDetails?.status === 'completed',
  })
  
  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!selectedJobId) return
    
    // Close existing connection
    if (ws) {
      ws.close()
    }
    
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/jobs/ws/${selectedJobId}`
    
    const websocket = new WebSocket(wsUrl)
    
    websocket.onopen = () => {
      console.log('WebSocket connected for job', selectedJobId)
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)
      setWsData(data)
      
      // Refetch data on updates
      if (data.type === 'progress') {
        refetchDetails()
      } else if (data.type === 'completion') {
        refetchDetails()
        refetchJobs()
        refetchUrls()
      }
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }
    
    setWs(websocket)
    
    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
    }
  }, [selectedJobId])
  
  // Auto-select first job if none selected
  useEffect(() => {
    if (!selectedJobId && jobs && jobs.length > 0) {
      setSelectedJobId(jobs[0].job_id)
    }
  }, [jobs, selectedJobId])
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4" />
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />
      case 'failed':
        return <XCircle className="w-4 h-4" />
      default:
        return <Activity className="w-4 h-4" />
    }
  }
  
  if (jobsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Job Monitor</h1>
          <p className="text-muted-foreground mt-1">
            Track your scraping jobs in real-time
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            refetchJobs()
            refetchDetails()
            refetchUrls()
          }}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">All Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {jobs && jobs.length > 0 ? (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {jobs.map((job) => (
                  <button
                    key={job.job_id}
                    onClick={() => setSelectedJobId(job.job_id)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedJobId === job.job_id
                        ? 'bg-primary/10 border-primary'
                        : 'hover:bg-accent/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(job.status)}
                        <Badge className={getStatusColor(job.status)} variant="outline">
                          {job.status}
                        </Badge>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                    <p className="text-sm font-medium truncate">
                      {job.start_url || job.query || `Job ${job.job_id}`}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDate(job.created_at)}
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No jobs yet</p>
                <Link to="/direct-scrape">
                  <Button variant="link" size="sm" className="mt-2">
                    Start scraping
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Job Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedJobId && jobDetails ? (
            <>
              {/* Status Card */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(jobDetails.status)}
                      <div>
                        <CardTitle>Job #{jobDetails.job_id}</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                          {jobDetails.job_type === 'direct' ? 'Direct Scrape' : 'Smart Scrape'}
                        </p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(jobDetails.status)} size="lg">
                      {jobDetails.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Target */}
                  <div>
                    <p className="text-sm font-medium mb-1">Target</p>
                    {jobDetails.start_url ? (
                      <a
                        href={jobDetails.start_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline flex items-center gap-1"
                      >
                        {jobDetails.start_url}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <p className="text-sm text-muted-foreground">{jobDetails.query}</p>
                    )}
                  </div>
                  
                  {/* Progress */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Discovered</p>
                      <p className="text-2xl font-bold">{jobDetails.urls_discovered || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Scraped</p>
                      <p className="text-2xl font-bold text-green-600">{jobDetails.urls_scraped || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Failed</p>
                      <p className="text-2xl font-bold text-red-600">{jobDetails.urls_failed || 0}</p>
                    </div>
                  </div>
                  
                  {/* WebSocket Real-time Data */}
                  {wsData && wsData.current_url && (
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-xs font-medium text-blue-900 mb-1">Currently processing:</p>
                      <p className="text-sm text-blue-700 truncate">{wsData.current_url}</p>
                    </div>
                  )}
                  
                  {/* Timestamps */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Created</p>
                      <p className="font-medium">{formatDate(jobDetails.created_at)}</p>
                    </div>
                    {jobDetails.started_at && (
                      <div>
                        <p className="text-muted-foreground">Started</p>
                        <p className="font-medium">{formatDate(jobDetails.started_at)}</p>
                      </div>
                    )}
                    {jobDetails.completed_at && (
                      <div>
                        <p className="text-muted-foreground">Completed</p>
                        <p className="font-medium">{formatDate(jobDetails.completed_at)}</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Error Message */}
                  {jobDetails.error_message && (
                    <div className="p-3 bg-destructive/10 rounded-lg border border-destructive/20">
                      <p className="text-sm text-destructive">{jobDetails.error_message}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* Scraped URLs */}
              {jobUrls && jobUrls.urls && jobUrls.urls.length > 0 && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5" />
                      <CardTitle>Scraped URLs ({jobUrls.total})</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-[400px] overflow-y-auto">
                      {jobUrls.urls.map((url, index) => (
                        <div
                          key={index}
                          className="p-3 rounded-lg border hover:bg-accent/50 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <a
                                href={url.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-medium hover:text-primary flex items-center gap-1 group"
                              >
                                <Globe className="w-3 h-3 flex-shrink-0" />
                                <span className="truncate">{url.title || url.url}</span>
                                <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                              </a>
                              <p className="text-xs text-muted-foreground mt-1 truncate">
                                {url.url}
                              </p>
                              <div className="flex items-center gap-3 mt-1">
                                <span className="text-xs text-muted-foreground">
                                  {url.content_length?.toLocaleString()} chars
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(url.scraped_at)}
                                </span>
                              </div>
                            </div>
                            <Badge 
                              variant="outline"
                              className={url.status === 'success' ? 'border-green-500 text-green-700' : 'border-red-500 text-red-700'}
                            >
                              {url.status}
                            </Badge>
                          </div>
                          {url.error_message && (
                            <p className="text-xs text-destructive mt-2">{url.error_message}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Select a job to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}


