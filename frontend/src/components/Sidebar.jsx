import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'

import { getHealth } from '../api/client'

const NAV_ITEMS = [
  { to: '/', icon: '🏠', label: '今日论文' },
  { to: '/history', icon: '📂', label: '历史日报' },
  { to: '/settings', icon: '⚙️', label: '系统配置' },
]

const FALLBACK_VERSION = '0.0.1'

export default function Sidebar() {
  const [version, setVersion] = useState(FALLBACK_VERSION)

  useEffect(() => {
    let cancelled = false

    getHealth()
      .then(data => {
        if (!cancelled && data?.version) {
          setVersion(data.version)
        }
      })
      .catch(() => {})

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>ArXiv Agent</h1>
        <p>AI 论文智能助手</p>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
        ArXiv Agent v{version} by <a href="https://github.com/New2World">New2World</a>
      </div>
    </aside>
  )
}
