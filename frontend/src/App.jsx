import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import DirectScrape from './components/DirectScrape'
import SmartScrape from './components/SmartScrape'
import Search from './components/Search'
import JobMonitor from './components/JobMonitor'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/direct-scrape" element={<DirectScrape />} />
          <Route path="/smart-scrape" element={<SmartScrape />} />
          <Route path="/search" element={<Search />} />
          <Route path="/jobs" element={<JobMonitor />} />
          <Route path="/jobs/:jobId" element={<JobMonitor />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

