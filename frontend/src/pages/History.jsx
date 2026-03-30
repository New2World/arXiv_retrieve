import { useState, useEffect } from 'react'
import { getHistoryDates, getPapers } from '../api/client'
import { toast } from '../components/Toast'
import PaperCard from '../components/PaperCard'

export default function History() {
  const [dates, setDates] = useState([])
  const [selected, setSelected] = useState(null)
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getHistoryDates()
      .then(d => { 
        setDates(d)
        if (d.length > 0) {
          selectDate(d[0])
        }
      })
      .catch(() => toast.error('加载历史记录失败'))
  }, [])

  const selectDate = async (d) => {
    setSelected(d)
    setLoading(true)
    try {
      const data = await getPapers({ fetch_date: d, selected_only: true })
      setPapers(data)
    } catch { 
      toast.error('加载当期论文失败') 
    } finally { 
      setLoading(false) 
    }
  }

  const handleRatingChanged = () => {
    // If a player rates a paper in the history view, we silently reload exactly like the Home view
    if (selected) {
      getPapers({ fetch_date: selected, selected_only: true })
        .then(setPapers)
        .catch(err => console.error(err))
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>历史回顾</h2>
        <p>按需加载往期入选论文，支持交互阅读和打分修正</p>
      </div>
      <div className="page-body">
        {dates.length === 0 ? (
          <div className="empty-state">
            <span className="emoji">📂</span>
            <h3>暂无历史记录</h3>
            <p>完成首次每日抓取后，历史日报将出现在这里</p>
          </div>
        ) : (
          <div className="history-layout">
            <div className="date-list">
              {dates.map(d => (
                <div
                  key={d}
                  className={`date-item ${selected === d ? 'active' : ''}`}
                  onClick={() => selectDate(d)}
                >
                  📅 {d}
                </div>
              ))}
            </div>
            {/* We override the classic markdown-view styling slightly here to fit the PaperCard padding securely */}
            <div className="markdown-view" style={{ background: 'transparent', padding: 0, border: 'none' }}>
              {loading ? (
                <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)' }}>
                  <div className="spinner" style={{ margin: '0 auto 12px' }} />加载中...
                </div>
              ) : papers.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)' }}>
                  当日暂无论文数据。
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {papers.map((paper) => (
                    <PaperCard key={paper.id} paper={paper} onRated={handleRatingChanged} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
