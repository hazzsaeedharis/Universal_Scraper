import { Link, useLocation } from 'react-router-dom'
import { cn } from '../lib/utils'
import { 
  Home, 
  Link2, 
  Sparkles, 
  Search, 
  Activity 
} from 'lucide-react'

export default function Layout({ children }) {
  const location = useLocation()
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Direct Scrape', href: '/direct-scrape', icon: Link2 },
    { name: 'Smart Scrape', href: '/smart-scrape', icon: Sparkles },
    { name: 'Search', href: '/search', icon: Search },
    { name: 'Jobs', href: '/jobs', icon: Activity },
  ]
  
  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-card border-r">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 px-6 py-6 border-b">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">Universal Scraper</span>
          </div>
          
          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
          
          {/* Footer */}
          <div className="px-6 py-4 border-t text-xs text-muted-foreground">
            <p>v1.0.0 - AI-Powered Scraper</p>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="pl-64">
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  )
}

