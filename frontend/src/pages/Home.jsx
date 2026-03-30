import { useState, useEffect, useCallback, useRef } from 'react'
import useSWR from 'swr'
import { getPapers, triggerFetch, getFetchStatus } from '../api/client'
import PaperCard from '../components/PaperCard'
import { toast } from '../components/Toast'

export default function Home() {
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(true)
  const [dateFilter, setDateFilter] = useState('')
  const [search, setSearch] = useState('')

  // SWR dynamically fetches and manages status state
  // Auto-polls every 3 seconds ONLY if the current status says it revolves "running"
  const { data: fetchStatus, mutate: mutateStatus } = useSWR('/fetch/status', getFetchStatus, {
    refreshInterval: (data) => (data?.running ? 3000 : 0),
    revalidateOnFocus: false
  })

  const loadPapers = useCallback(async () => {
    setLoading(true)
    try {
      const params = { selected_only: true }
      if (dateFilter) {
        params.fetch_date = dateFilter
      } else {
        params.latest_fetch = true
      }
      const data = await getPapers(params)
      setPapers(data)
    } catch {
      toast.error('加载论文失败')
    } finally {
      setLoading(false)
    }
  }, [dateFilter])

  const prevRunning = useRef(false)
  useEffect(() => {
    // When transition from running (true) => idle (false), force a papers reload
    if (prevRunning.current === true && fetchStatus && !fetchStatus.running) {
      loadPapers()
    }
    prevRunning.current = fetchStatus?.running || false
  }, [fetchStatus?.running, loadPapers])

  // Initial render load
  useEffect(() => { loadPapers() }, [loadPapers])

  const handleFetch = async () => {
    try {
      await triggerFetch()
      toast.success('开始抓取论文...')
      mutateStatus() // Tell SWR to instantly re-check, enabling the polling loop naturally
    } catch (e) {
      toast.error(e.response?.data?.detail || '触发失败')
    }
  }

  const filtered = papers.filter(p =>
    !search || p.title.toLowerCase().includes(search.toLowerCase()) ||
    p.abstract?.toLowerCase().includes(search.toLowerCase())
  )

  const today = new Date().toISOString().slice(0, 10)

  return (
    <div>
      <div className="page-header">
        <h2>今日论文</h2>
        <p>AI 筛选的最新 ArXiv 论文，按偏好评分排序</p>
      </div>

      <div className="page-body">
        {/* Fetch Banner */}
        {fetchStatus?.running && (
          <div className="fetch-banner">
            <div className="spinner" />
            <div>
              <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>正在抓取论文...</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                这需要几分钟，完成后自动刷新
              </div>
            </div>
          </div>
        )}

        {/* Status bar */}
        {fetchStatus?.last_log && !fetchStatus.running && (
          <div className="fetch-banner" style={{ background: 'transparent', border: '1px solid var(--border-subtle)', marginBottom: 16 }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              上次抓取：{new Date(fetchStatus.last_log.started_at).toLocaleString('zh-CN')}
              &nbsp;·&nbsp;
              共抓取 {fetchStatus.last_log.fetched_count} 篇，筛选 {fetchStatus.last_log.selected_count} 篇
              &nbsp;·&nbsp;
              [{fetchStatus.last_log.status === 'done' ? '✅ 完成' : '❌ 失败'}]
            </span>
            <button className="btn btn-primary" onClick={handleFetch} style={{ marginLeft: 'auto' }}
              disabled={fetchStatus.running}>
              🔄 立即抓取
            </button>
          </div>
        )}

        {/* No last log: first time */}
        {!fetchStatus?.last_log && !fetchStatus?.running && (
          <div className="fetch-banner">
            <span style={{ flex: 1, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              尚无论文数据，点击"立即抓取"开始
            </span>
            <button className="btn btn-primary" onClick={handleFetch}>
              🚀 立即抓取
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="filters-bar">
          <input
            placeholder="🔍 搜索标题或摘要..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <input
            type="date"
            value={dateFilter}
            max={today}
            onChange={e => setDateFilter(e.target.value)}
            style={{ width: 'auto' }}
            title="按日期筛选"
          />
          {dateFilter && (
            <button className="btn btn-ghost" onClick={() => setDateFilter('')}>✕ 清除日期</button>
          )}
          <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {filtered.length} 篇
          </span>
        </div>

        {/* Paper list */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
            <div className="spinner" style={{ margin: '0 auto 12px' }} />
            加载中...
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <span className="emoji">📭</span>
            <h3>暂无论文</h3>
            <p>试试点击"立即抓取"获取最新 ArXiv 论文</p>
          </div>
        ) : (
          filtered.map(paper => (
            <PaperCard key={paper.id} paper={paper} onRated={loadPapers} />
          ))
        )}
      </div>
    </div>
  )
}
