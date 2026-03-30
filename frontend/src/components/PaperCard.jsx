import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import StarRating from './StarRating'
import { ratePaper, toggleDislike } from '../api/client'
import { toast } from './Toast'

export default function PaperCard({ paper, onRated }) {
  const [expanded, setExpanded] = useState(false)
  const [rating, setRating] = useState(paper.user_rating || 0)
  const [disliked, setDisliked] = useState(paper.is_disliked || false)
  const [loading, setLoading] = useState(false)

  const handleRate = async (val) => {
    if (loading) return
    setLoading(true)
    try {
      await ratePaper(paper.id, val)
      setRating(val)
      onRated?.()
      toast.success(`已评分 ${val} ⭐`)
    } catch {
      toast.error('评分失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleDislike = async () => {
    try {
      const nextState = !disliked
      await toggleDislike(paper.id, nextState)
      setDisliked(nextState)
      toast.success(nextState ? '已打回，将在下次抓取时彻底移除！' : '已撤销不喜欢标记')
    } catch {
      toast.error('操作失败')
    }
  }

  const pubDate = paper.published
    ? new Date(paper.published).toLocaleDateString('zh-CN')
    : 'N/A'

  const authors = paper.authors?.slice(0, 3).join(', ') +
    (paper.authors?.length > 3 ? ` 等 ${paper.authors.length} 人` : '')

  const scoreColor = paper.ai_score > 0.3 ? 'badge-green'
    : paper.ai_score > 0.1 ? 'badge-yellow' : 'badge-blue'

  return (
    <div className="card paper-card" style={disliked ? { opacity: 0.55, filter: 'grayscale(1)' } : {}}>
      <div className="paper-card-header">
        <h3 className="paper-title">
          <a href={paper.url} target="_blank" rel="noreferrer">{paper.title}</a>
        </h3>
        {paper.ai_score != null && (
          <span className={`badge ${scoreColor}`} title="偏好相关度">
            ≈{(paper.ai_score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      <div className="paper-meta">
        <span className="paper-meta-item">👤 {authors}</span>
        <span className="paper-meta-item">📅 {pubDate}</span>
        {paper.categories?.slice(0, 3).map(cat => (
          <span key={cat} className="badge badge-blue">{cat}</span>
        ))}
        {paper.comment && (
          <span className="paper-meta-item" style={{ color: 'var(--text-muted)', fontSize: '0.77rem' }}>
            {paper.comment}
          </span>
        )}
      </div>

      {!expanded && (
        <p className="paper-abstract">{paper.abstract}</p>
      )}

      {expanded && paper.summary && (
        <div className="paper-summary">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{paper.summary}</ReactMarkdown>
        </div>
      )}

      {expanded && !paper.summary && (
        <p className="paper-abstract" style={{ fontStyle: 'italic' }}>暂无 AI 总结</p>
      )}

      <div className="paper-footer">
        <div className="paper-actions">
          <button className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '5px 10px' }}
            onClick={() => setExpanded(e => !e)}>
            {expanded ? '▲ 收起' : '▼ 展开总结'}
          </button>
          <a href={paper.pdf_url || paper.url} target="_blank" rel="noreferrer"
            className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '5px 10px' }}>
            📄 PDF
          </a>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>评分:</span>
          <StarRating value={rating} onChange={handleRate} />
          
          <button 
            className={`btn ${disliked ? 'btn-primary' : 'btn-ghost'}`} 
            style={{ fontSize: '0.75rem', padding: '4px 8px', marginLeft: 8 }}
            onClick={handleDislike}
            title="不感兴趣，在下一轮新抓取前彻底抹除此文章并不计入历史。"
          >
            {disliked ? '已打回 👎' : '👎'}
          </button>
        </div>
      </div>
    </div>
  )
}
