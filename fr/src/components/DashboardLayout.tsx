import { useState } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import './DashboardLayout.css'

interface DashboardLayoutProps {
  children: React.ReactNode
  onSearch?: (val: string) => void
}

export default function DashboardLayout({ children, onSearch }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="dashboard-root">
      <div className="dashboard-body">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="dashboard-main">
          <Topbar onSearch={onSearch} onMenuToggle={() => setSidebarOpen(prev => !prev)} />
          <div className="dashboard-content">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
