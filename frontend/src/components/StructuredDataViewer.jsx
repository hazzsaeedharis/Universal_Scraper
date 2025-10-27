import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import { Download, Copy, Table, Code, Brain, CheckCircle2 } from 'lucide-react'
import { exportData } from '../lib/api'
import { toast } from 'sonner'

export default function StructuredDataViewer({ data, dataType, confidence }) {
  const [viewMode, setViewMode] = useState('table') // 'table' or 'json'

  const handleExport = async (format) => {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const filename = `${dataType}_${timestamp}`
      
      const blob = await exportData(data, format, filename)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${filename}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.success(`Exported as ${format.toUpperCase()}!`)
    } catch (error) {
      console.error('Export error:', error)
      toast.error(`Failed to export as ${format.toUpperCase()}`)
    }
  }

  const handleCopy = () => {
    const jsonText = JSON.stringify(data, null, 2)
    navigator.clipboard.writeText(jsonText)
      .then(() => toast.success('Copied to clipboard!'))
      .catch(() => toast.error('Failed to copy'))
  }

  const renderTable = () => {
    if (!data || Object.keys(data).length === 0) {
      return <p className="text-muted-foreground">No structured data available.</p>
    }

    switch (dataType) {
      case 'business_hours':
        return (
          <div className="space-y-6">
            {data.entity && <h3 className="text-lg font-semibold">{data.entity}</h3>}
            
            {data.hours?.regular && data.hours.regular.length > 0 && (
              <div>
                <h4 className="text-md font-semibold mb-3">Regular Hours</h4>
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 px-4 text-left">Day</th>
                      <th className="py-2 px-4 text-left">Status</th>
                      <th className="py-2 px-4 text-left">Open</th>
                      <th className="py-2 px-4 text-left">Close</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.hours.regular.map((h, i) => (
                      <tr key={i} className="border-b last:border-b-0">
                        <td className="py-2 px-4">{h.day}</td>
                        <td className="py-2 px-4">
                          <Badge variant={h.status === 'open' ? 'default' : 'secondary'}>
                            {h.status}
                          </Badge>
                        </td>
                        <td className="py-2 px-4">{h.open || '—'}</td>
                        <td className="py-2 px-4">{h.close || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            {data.hours?.kitchen && data.hours.kitchen.length > 0 && (
              <div>
                <h4 className="text-md font-semibold mb-3">Kitchen Hours</h4>
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 px-4 text-left">Day</th>
                      <th className="py-2 px-4 text-left">Status</th>
                      <th className="py-2 px-4 text-left">Open</th>
                      <th className="py-2 px-4 text-left">Close</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.hours.kitchen.map((h, i) => (
                      <tr key={i} className="border-b last:border-b-0">
                        <td className="py-2 px-4">{h.day}</td>
                        <td className="py-2 px-4">
                          <Badge variant={h.status === 'open' ? 'default' : 'secondary'}>
                            {h.status}
                          </Badge>
                        </td>
                        <td className="py-2 px-4">{h.open || '—'}</td>
                        <td className="py-2 px-4">{h.close || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            {data.timezone && <p className="text-sm text-muted-foreground mt-4">Timezone: {data.timezone}</p>}
          </div>
        )

      case 'menu':
        return (
          <div className="space-y-6">
            {data.restaurant && <h3 className="text-lg font-semibold">{data.restaurant}</h3>}
            {data.menu_name && <p className="text-sm text-muted-foreground">{data.menu_name}</p>}
            
            {data.categories && data.categories.map((category, catIdx) => (
              <div key={catIdx}>
                <h4 className="text-md font-semibold mb-3">{category.category_name}</h4>
                {category.description && <p className="text-sm text-muted-foreground mb-3">{category.description}</p>}
                
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 px-4 text-left">Item</th>
                      <th className="py-2 px-4 text-left">Description</th>
                      <th className="py-2 px-4 text-left">Price</th>
                      <th className="py-2 px-4 text-left">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {category.items && category.items.map((item, itemIdx) => (
                      <tr key={itemIdx} className="border-b last:border-b-0">
                        <td className="py-2 px-4 font-medium">{item.name}</td>
                        <td className="py-2 px-4 text-muted-foreground max-w-md truncate">{item.description}</td>
                        <td className="py-2 px-4 whitespace-nowrap">
                          {item.price ? `${item.price} ${item.currency || data.currency || ''}` : '—'}
                        </td>
                        <td className="py-2 px-4">
                          {item.annotations && item.annotations.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {item.annotations.map((ann, i) => (
                                <Badge key={i} variant="outline" className="text-xs">{ann}</Badge>
                              ))}
                            </div>
                          )}
                          {item.calories && <span className="text-xs text-muted-foreground ml-2">{item.calories} cal</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
            
            {data.notes && <p className="text-sm text-muted-foreground mt-4 italic">{data.notes}</p>}
          </div>
        )

      case 'contact_info':
        return (
          <div className="space-y-3">
            {data.entity && <h3 className="text-lg font-semibold mb-4">{data.entity}</h3>}
            
            {data.phone_numbers && data.phone_numbers.length > 0 && (
              <div>
                <p className="text-sm font-medium">Phone:</p>
                <p className="text-sm text-muted-foreground">{data.phone_numbers.join(', ')}</p>
              </div>
            )}
            
            {data.email_addresses && data.email_addresses.length > 0 && (
              <div>
                <p className="text-sm font-medium">Email:</p>
                <p className="text-sm text-muted-foreground">{data.email_addresses.join(', ')}</p>
              </div>
            )}
            
            {data.website_urls && data.website_urls.length > 0 && (
              <div>
                <p className="text-sm font-medium">Website:</p>
                {data.website_urls.map((url, i) => (
                  <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline block">
                    {url}
                  </a>
                ))}
              </div>
            )}
            
            {data.address && (
              <div>
                <p className="text-sm font-medium">Address:</p>
                <p className="text-sm text-muted-foreground">
                  {data.address.street}, {data.address.city}, {data.address.state} {data.address.zip_code}, {data.address.country}
                </p>
              </div>
            )}
            
            {data.social_media && data.social_media.length > 0 && (
              <div>
                <p className="text-sm font-medium">Social Media:</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {data.social_media.map((sm, i) => (
                    <a key={i} href={sm.url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                      {sm.platform}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      case 'pricing':
        return (
          <div className="space-y-4">
            {data.entity && <h3 className="text-lg font-semibold">{data.entity}</h3>}
            {data.average_price && (
              <p className="text-sm">
                <strong>Average Price:</strong> {data.average_price} {data.currency}
              </p>
            )}
            
            {data.price_ranges && data.price_ranges.length > 0 && (
              <div>
                <h4 className="text-md font-semibold mb-3">Price Ranges</h4>
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 px-4 text-left">Category</th>
                      <th className="py-2 px-4 text-left">Min</th>
                      <th className="py-2 px-4 text-left">Max</th>
                      <th className="py-2 px-4 text-left">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.price_ranges.map((pr, i) => (
                      <tr key={i} className="border-b last:border-b-0">
                        <td className="py-2 px-4">{pr.category}</td>
                        <td className="py-2 px-4">{pr.min_price} {data.currency}</td>
                        <td className="py-2 px-4">{pr.max_price} {data.currency}</td>
                        <td className="py-2 px-4 text-muted-foreground">{pr.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            {data.notes && <p className="text-sm text-muted-foreground italic">{data.notes}</p>}
          </div>
        )

      default:
        return (
          <pre className="bg-muted p-4 rounded-md text-sm overflow-auto max-h-96">
            {JSON.stringify(data, null, 2)}
          </pre>
        )
    }
  }

  return (
    <Card className="border-primary shadow-lg mt-6">
      <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <CardTitle className="flex items-center gap-2">
                Structured Data
                <Badge variant="secondary" className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Extracted
                </Badge>
              </CardTitle>
              <CardDescription>
                Type: <Badge variant="outline">{dataType}</Badge> | Confidence: {(confidence * 100).toFixed(0)}%
              </CardDescription>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button 
              variant={viewMode === 'table' ? 'default' : 'outline'} 
              size="sm" 
              onClick={() => setViewMode('table')}
            >
              <Table className="w-4 h-4 mr-2" /> Table
            </Button>
            <Button 
              variant={viewMode === 'json' ? 'default' : 'outline'} 
              size="sm" 
              onClick={() => setViewMode('json')}
            >
              <Code className="w-4 h-4 mr-2" /> JSON
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-6">
        {/* View Content */}
        {viewMode === 'table' ? renderTable() : (
          <div className="relative">
            <Button
              variant="secondary"
              size="sm"
              className="absolute top-2 right-2 z-10"
              onClick={handleCopy}
            >
              <Copy className="w-4 h-4 mr-2" /> Copy
            </Button>
            <pre className="bg-muted p-4 rounded-md text-sm overflow-auto max-h-[500px]">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
        
        {/* Export Buttons */}
        <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
          <Button variant="secondary" size="sm" onClick={() => handleExport('json')}>
            <Download className="w-4 h-4 mr-2" /> Export JSON
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('csv')}>
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('md')}>
            <Download className="w-4 h-4 mr-2" /> Export Markdown
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

