import { useQuery } from '@tanstack/react-query'
import { getStats, getJobs } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { formatDate, getStatusColor, formatBytes } from '../lib/utils'
import { 
  Database, 
  FileText, 
  Globe, 
  Activity,
  Loader2 
} from 'lucide-react'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })
  
  const { data: recentJobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', 10],
    queryFn: () => getJobs(10),
  })
  
  if (statsLoading || jobsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }
  
  const statCards = [
    {
      title: 'Total Jobs',
      value: stats?.total_jobs || 0,
      icon: Activity,
      description: 'Scraping jobs executed',
    },
    {
      title: 'URLs Scraped',
      value: stats?.total_urls_scraped || 0,
      icon: FileText,
      description: 'Pages successfully scraped',
    },
    {
      title: 'Domains',
      value: stats?.total_domains || 0,
      icon: Globe,
      description: 'Unique domains crawled',
    },
    {
      title: 'Vectors',
      value: stats?.vector_store_stats?.total_vector_count || 0,
      icon: Database,
      description: 'Embeddings in Pinecone',
    },
  ]
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your scraping activities
        </p>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <Icon className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>
      
      {/* Recent Jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {recentJobs && recentJobs.length > 0 ? (
            <div className="space-y-4">
              {recentJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <Badge className={getStatusColor(job.status)}>
                        {job.status}
                      </Badge>
                      <span className="font-medium">
                        {job.job_type === 'direct' ? 'Direct Scrape' : 'Smart Scrape'}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {job.start_url || job.query}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span>Scraped: {job.urls_scraped}</span>
                      <span>Failed: {job.urls_failed}</span>
                      <span>{formatDate(job.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No jobs yet. Start scraping!
            </p>
          )}
        </CardContent>
      </Card>
      
      {/* Storage Info */}
      {stats?.storage_stats && (
        <Card>
          <CardHeader>
            <CardTitle>Storage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Size</p>
                <p className="text-2xl font-bold">
                  {formatBytes(stats.storage_stats.total_size_bytes)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Domains Stored</p>
                <p className="text-2xl font-bold">
                  {stats.storage_stats.domains}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

