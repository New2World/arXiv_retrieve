import { useState, useEffect } from 'react'
import { getSettings, updateSettings } from '../api/client'
import { toast } from '../components/Toast'

function TagsInput({ value, onChange, placeholder }) {
  const [input, setInput] = useState('')
  const add = () => {
    const v = input.trim()
    if (v && !value.includes(v)) onChange([...value, v])
    setInput('')
  }
  const remove = (tag) => onChange(value.filter(t => t !== tag))
  return (
    <div className="tags-container">
      {value.map(tag => (
        <span key={tag} className="tag">
          {tag}
          <button onClick={() => remove(tag)} type="button">×</button>
        </span>
      ))}
      <input
        className="tags-input"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={e => (e.key === 'Enter' || e.key === ',') && (e.preventDefault(), add())}
        placeholder={placeholder || 'Enter 添加...'}
      />
    </div>
  )
}

export default function Settings() {
  const [cfg, setCfg] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getSettings().then(setCfg)
  }, [])

  const set = (key, val) => setCfg(c => ({ ...c, [key]: val }))

  const setProviderConfig = (key, val) => {
    setCfg(c => ({
      ...c,
      providers: {
        ...c.providers,
        [c.llm_provider]: {
          ...c.providers[c.llm_provider],
          [key]: val
        }
      }
    }))
  }

  const clearProviderApiKey = () => {
    setCfg(c => ({
      ...c,
      providers: {
        ...c.providers,
        [c.llm_provider]: {
          ...c.providers[c.llm_provider],
          api_key: '',
          clear_api_key: true,
          has_api_key: false
        }
      }
    }))
  }

  const parseCronToLocal = (cronStr) => {
    if (!cronStr || cronStr === 'none') return { type: 'daily', time: '08:00', day: '1' }
    const parts = cronStr.split(' ')
    if (parts.length < 5) return { type: 'daily', time: '08:00', day: '1' }

    let min = parseInt(parts[0], 10)
    let hour = parseInt(parts[1], 10)
    const isWeekly = parts[4] !== '*'
    let dow = isWeekly ? parseInt(parts[4], 10) : 1

    const offsetMins = new Date().getTimezoneOffset()

    let localMin = min - offsetMins
    let overflowHours = Math.floor(localMin / 60)
    localMin = localMin % 60
    if (localMin < 0) localMin += 60

    let localHour = hour + overflowHours
    let overflowDays = Math.floor(localHour / 24)
    localHour = localHour % 24
    if (localHour < 0) localHour += 24

    let localDow = (dow + overflowDays) % 7
    if (localDow < 0) localDow += 7

    const localTimeStr = `${localHour.toString().padStart(2, '0')}:${localMin.toString().padStart(2, '0')}`
    return { type: isWeekly ? 'weekly' : 'daily', time: localTimeStr, day: localDow.toString() }
  }

  const updateCronFromLocal = (newType, newTime, newDay) => {
    if (!newTime) newTime = '08:00'
    const [h, m] = newTime.split(':')
    let localHour = parseInt(h, 10)
    let localMin = parseInt(m, 10)
    let localDow = parseInt(newDay, 10)

    const offsetMins = new Date().getTimezoneOffset()

    let utcMin = localMin + offsetMins
    let overflowHours = Math.floor(utcMin / 60)
    utcMin = utcMin % 60
    if (utcMin < 0) utcMin += 60

    let utcHour = localHour + overflowHours
    let overflowDays = Math.floor(utcHour / 24)
    utcHour = utcHour % 24
    if (utcHour < 0) utcHour += 24

    let utcDow = (localDow + overflowDays) % 7
    if (utcDow < 0) utcDow += 7

    const cronStr = newType === 'daily'
      ? `${utcMin} ${utcHour} * * *`
      : `${utcMin} ${utcHour} * * ${utcDow}`

    setCfg(c => ({
      ...c,
      auto_fetch_cron: cronStr,
      arxiv_days: newType === 'daily' ? 1 : 7
    }))
  }

  const save = async () => {
    setSaving(true)
    try {
      const updated = await updateSettings(cfg)
      setCfg(updated)
      toast.success('配置已保存')
    } catch {
      toast.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (!cfg) return (
    <div style={{ textAlign: 'center', padding: 64, color: 'var(--text-secondary)' }}>
      <div className="spinner" style={{ margin: '0 auto 12px' }} />加载配置...
    </div>
  )

  const currentProvider = cfg.providers[cfg.llm_provider] || {}
  const providerNames = Object.keys(cfg.providers || {})

  return (
    <div>
      <div className="page-header">
        <h2>系统配置</h2>
        <p>配置 LLM 模型、ArXiv 抓取参数、关键词筛选等</p>
      </div>

      <div className="page-body">
        <div className="settings-grid">
          {/* LLM 配置 */}
          <div className="card settings-section">
            <h3>🤖 LLM 配置</h3>

            <div className="form-group">
              <label className="form-label">当前大语言模型驱动 (Provider)</label>
              <select value={cfg.llm_provider} onChange={e => set('llm_provider', e.target.value)}>
                {providerNames.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">总结字数流限制 (全局最大 Token)</label>
              <input type="number" value={cfg.llm_max_tokens}
                onChange={e => set('llm_max_tokens', +e.target.value)} />
              <p className="form-hint">所有大模型统一的生成阈控制区。</p>
            </div>

            <div className="form-group">
              <label className="form-label">并发请求数 (最大同时处理论文)</label>
              <input type="number" value={cfg.llm_concurrency}
                onChange={e => set('llm_concurrency', +e.target.value)} />
              <p className="form-hint">设为 1 即完全排队串行处理（有效防止大模型拥堵）。</p>
            </div>

            <div className="form-group">
              <label className="form-label">请求间隔休眠 (秒)</label>
              <input type="number" value={cfg.llm_wait_seconds}
                onChange={e => set('llm_wait_seconds', +e.target.value)} />
              <p className="form-hint">每消耗完一个请求后强行挂起的冷却时间，防止触发防刷限流 (429)。</p>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '16px 0' }} />
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
              <h4 style={{ margin: '0 12px', fontSize: '0.9rem', color: 'var(--text-primary)', textTransform: 'uppercase' }}>
                {cfg.llm_provider} 专线配置方案
              </h4>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
            </div>

            <div className="form-group">
              <label className="form-label">该驱动支持的模型簇 (Enter 自由追加全新模型)</label>
              <TagsInput
                value={currentProvider.available_models || []}
                onChange={v => setProviderConfig('available_models', v)}
                placeholder="例如: gpt-5"
              />
              <p className="form-hint">随时追加厂商新出的模型ID，这些变更会持久化到 config.json。</p>
            </div>

            <div className="form-group">
              <label className="form-label">选定默认运行模型</label>
              {(currentProvider.available_models || []).length > 0 ? (
                <select value={currentProvider.model} onChange={e => setProviderConfig('model', e.target.value)}>
                  {currentProvider.available_models.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              ) : (
                <input value={currentProvider.model} onChange={e => setProviderConfig('model', e.target.value)} placeholder="如 gpt-4o" />
              )}
            </div>

            <div className="form-group">
              <label className="form-label">API 凭证密钥 (api_key)</label>
              <input
                type="password"
                value={currentProvider.api_key || ''}
                placeholder={currentProvider.has_api_key ? '已配置，留空则保持不变' : 'sk-... 或留空'}
                onChange={e => {
                  const value = e.target.value
                  setCfg(c => ({
                    ...c,
                    providers: {
                      ...c.providers,
                      [c.llm_provider]: {
                        ...c.providers[c.llm_provider],
                        api_key: value,
                        clear_api_key: false
                      }
                    }
                  }))
                }}
              />
              <p className="form-hint">
                {currentProvider.has_api_key ? '当前已保存密钥，重新输入才会覆盖。' : '当前尚未配置密钥。'}
              </p>
              {currentProvider.has_api_key && cfg.llm_provider !== 'ollama' && (
                <button type="button" className="btn btn-ghost" onClick={clearProviderApiKey}>
                  清除已保存密钥
                </button>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">自定义中转网关 (base_url)</label>
              <input value={currentProvider.base_url !== 'none' ? currentProvider.base_url : ''} placeholder="https://api..."
                onChange={e => setProviderConfig('base_url', e.target.value || 'none')} />
              <p className="form-hint">官方原厂无需填写。使用中转等代理时修改此地址。</p>
            </div>

          </div>

          {/* ArXiv 配置 */}
          <div className="card settings-section">
            <h3>📡 ArXiv 配置</h3>

            <div className="form-group">
              <label className="form-label">抓取分类</label>
              <TagsInput
                value={cfg.arxiv_categories}
                onChange={v => set('arxiv_categories', v)}
                placeholder="例如: cs.AI"
              />
              <p className="form-hint">ArXiv 学科分类，如 cs.AI、cs.LG、cs.CV</p>
            </div>

            <div className="form-group">
              <label className="form-label">时间范围（天）</label>
              <input type="number" value={cfg.arxiv_days} max={7}
                disabled={cfg.auto_fetch_enabled}
                title={cfg.auto_fetch_enabled ? "受自动化调度锁定" : ""}
                onChange={e => set('arxiv_days', +e.target.value)} />
              {cfg.auto_fetch_enabled && (
                <p className="form-hint" style={{ color: 'var(--brand-primary)' }}>自动设成 {cfg.arxiv_days} 天以贴合调度频次，避免重复抓取或遗漏文章。</p>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">候选池大小</label>
              <input type="number" value={cfg.arxiv_max_results} max={3000}
                onChange={e => set('arxiv_max_results', +e.target.value)} />
              <p className="form-hint">抓取后进行筛选前的论文数量上限</p>
            </div>

            <div className="form-group">
              <label className="form-label">保留篇数</label>
              <input type="number" value={cfg.papers_per_day} max={200}
                onChange={e => set('papers_per_day', +e.target.value)} />
            </div>

            <h3 style={{ marginTop: 24 }}>🔍 关键词筛选</h3>
            <div className="form-group">
              <label className="form-label">关键词（留空则不过滤）</label>
              <TagsInput
                value={cfg.keywords}
                onChange={v => set('keywords', v)}
                placeholder="例如: diffusion"
              />
              <p className="form-hint">关键词匹配论文标题或摘要（OR 逻辑）</p>
            </div>

            <h3 style={{ marginTop: 24 }}>⏳ 自动化任务调度</h3>
            <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input type="checkbox"
                checked={cfg.auto_fetch_enabled || false}
                onChange={e => {
                  const isEnabled = e.target.checked
                  if (isEnabled) {
                    const cType = parseCronToLocal(cfg.auto_fetch_cron).type
                    setCfg(c => ({ ...c, auto_fetch_enabled: true, arxiv_days: cType === 'daily' ? 1 : 7 }))
                  } else {
                    set('auto_fetch_enabled', false)
                  }
                }}
                id="enable_auto"
                style={{ width: '16px', height: '16px', cursor: 'pointer' }}
              />
              <label htmlFor="enable_auto" style={{ fontWeight: 600, cursor: 'pointer' }}>开启定时自动抓取</label>
            </div>

            {cfg.auto_fetch_enabled && (
              <div className="form-group" style={{ padding: '16px', background: 'var(--bg-elevated)', borderRadius: 8, marginTop: -4, border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <div style={{ flex: 1 }}>
                    <label className="form-label" style={{ marginBottom: 6 }}>触发频率</label>
                    <select className="input-field" value={parseCronToLocal(cfg.auto_fetch_cron).type}
                      onChange={e => updateCronFromLocal(e.target.value, parseCronToLocal(cfg.auto_fetch_cron).time, parseCronToLocal(cfg.auto_fetch_cron).day)}>
                      <option value="daily">每天</option>
                      <option value="weekly">每周</option>
                    </select>
                  </div>

                  {parseCronToLocal(cfg.auto_fetch_cron).type === 'weekly' && (
                    <div style={{ flex: 1 }}>
                      <label className="form-label" style={{ marginBottom: 6 }}>指定日</label>
                      <select className="input-field" value={parseCronToLocal(cfg.auto_fetch_cron).day}
                        onChange={e => updateCronFromLocal(parseCronToLocal(cfg.auto_fetch_cron).type, parseCronToLocal(cfg.auto_fetch_cron).time, e.target.value)}>
                        <option value="1">星期一</option>
                        <option value="2">星期二</option>
                        <option value="3">星期三</option>
                        <option value="4">星期四</option>
                        <option value="5">星期五</option>
                        <option value="6">星期六</option>
                        <option value="0">星期日</option>
                      </select>
                    </div>
                  )}

                  <div style={{ flex: 1 }}>
                    <label className="form-label" style={{ marginBottom: 6 }}>时间点</label>
                    <input type="time" className="input-field" value={parseCronToLocal(cfg.auto_fetch_cron).time}
                      onChange={e => updateCronFromLocal(parseCronToLocal(cfg.auto_fetch_cron).type, e.target.value, parseCronToLocal(cfg.auto_fetch_cron).day)} />
                  </div>
                </div>
                <p className="form-hint" style={{ marginTop: 14 }}>
                  系统将会在设定时刻于后台自动执行全文摘要。请务必保证服务端守护进程常驻运行。<br />底层 UTC 映射表达式: <code style={{ color: 'var(--brand-primary)', marginLeft: 4 }}>{cfg.auto_fetch_cron}</code>
                </p>
              </div>
            )}

          </div>
        </div>

        <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <button className="btn btn-ghost" onClick={() => getSettings().then(setCfg)}>
            ↩ 重置
          </button>
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? '保存中...' : '💾 保存配置'}
          </button>
        </div>
      </div>
    </div>
  )
}
