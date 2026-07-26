import { useState } from 'react'
import { X } from 'lucide-react'
import * as api from '../../api/client'
import type { SquadInfo } from '../../types'

interface Props {
  squads: SquadInfo[]
  onImport: (file: File) => void
  onSelect: (id: number) => void
  onClose: () => void
}

export function ImportModal({ squads, onImport, onSelect, onClose }: Props) {
  const [pasteText, setPasteText] = useState('')
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState('')

  const doPasteImport = async () => {
    if (!pasteText.trim()) { setError('请先粘贴数据'); return }
    setImporting(true); setError('')
    try {
      const res = await fetch('/api/import/fm24-clipboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pasteText }),
      })
      const data = await res.json()
      if (res.ok && data.success) { onSelect(data.squad_id); onClose() }
      else { setError(data.detail || '解析失败') }
    } catch (e: any) { setError(e.message) }
    finally { setImporting(false) }
  }

  const doHTMLUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return
    setImporting(true); setError('')
    try {
      const form = new FormData(); form.append('file', file)
      const res = await fetch('/api/import/fm24-html', { method: 'POST', body: form })
      const data = await res.json()
      if (res.ok && data.success) { onSelect(data.squad_id); onClose() }
      else { setError(data.detail || '解析失败') }
    } catch (e: any) { setError(e.message) }
    finally { setImporting(false) }
  }

  const doCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return
    setImporting(true); setError('')
    try { await onImport(file) }
    catch (e: any) { setError(e.message) }
    finally { setImporting(false) }
  }

  const doSample = async () => {
    setImporting(true); setError('')
    try {
      const res = await fetch('/api/import/sample', { method: 'GET' })
      const data = await res.json()
      if (res.ok && data.success) { onSelect(data.squad_id); onClose() }
      else { setError(data.detail || '加载失败') }
    } catch (e: any) { setError(e.message) }
    finally { setImporting(false) }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>

        <h2 style={{ margin: '0 0 12px 0' }}>📤 导入阵容数据</h2>

        {/* Paste */}
        <div style={{ marginBottom: 14, padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 10 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
            📋 方式二：粘贴数据
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6 }}>
            FMRTE 或 FM24 里 Ctrl+A → Ctrl+C → 到这里 Ctrl+V
          </div>
          <textarea
            value={pasteText}
            onChange={e => setPasteText(e.target.value)}
            placeholder="Ctrl+V 粘贴..."
            style={{
              width: '100%', height: 70, background: 'var(--bg-primary)',
              border: '1px solid var(--border)', borderRadius: 6, padding: 8,
              color: 'var(--text-primary)', fontSize: 11, fontFamily: 'monospace',
              resize: 'vertical',
            }}
          />
          <button className="btn-primary" onClick={doPasteImport}
            disabled={importing || !pasteText.trim()} style={{ marginTop: 6, fontSize: 12 }}>
            {importing ? '解析中...' : '解析并导入'}
          </button>
        </div>

        {/* FM24 HTML */}
        <div style={{ marginBottom: 14, padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 10 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
            🎮 FM24 导出 HTML / 📊 FMRTE 导出 JSON
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8, lineHeight: 1.6 }}>
            FM24: Squad → Ctrl+A → Ctrl+P → Web Page → 上传 .html<br />
            FMRTE: 导出 → JSON → 上传 .json<br />
            CSV: 拖拽上传 .csv
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <label className="btn-ghost" style={{ cursor: 'pointer', fontSize: 12 }}>
              📁 .html
              <input type="file" accept=".html,.htm" onChange={doHTMLUpload} hidden />
            </label>
            <label className="btn-ghost" style={{ cursor: 'pointer', fontSize: 12 }}>
              📊 .json
              <input type="file" accept=".json" onChange={async (e) => {
                const f = e.target.files?.[0]; if (!f) return
                setImporting(true); setError('')
                try {
                  const form = new FormData(); form.append('file', f)
                  const res = await fetch('/api/import/json', { method: 'POST', body: form })
                  const data = await res.json()
                  if (res.ok && data.success) { onSelect(data.squad_id); onClose() }
                  else { setError(data.detail || '解析失败') }
                } catch (e: any) { setError(e.message) }
                finally { setImporting(false) }
              }} hidden />
            </label>
            <label className="btn-ghost" style={{ cursor: 'pointer', fontSize: 12 }}>
              📄 .csv
              <input type="file" accept=".csv" onChange={doCSVUpload} hidden />
            </label>
          </div>
        </div>

        {/* Sample */}
        <button onClick={doSample} disabled={importing}
          className="btn-ghost" style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}>
          🧪 使用示例数据（立刻体验）
        </button>

        {error && (
          <div style={{
            marginTop: 12, padding: '10px', borderRadius: 8,
            background: 'var(--danger)15', border: '1px solid var(--danger)30',
            fontSize: 12, color: 'var(--danger)', whiteSpace: 'pre-wrap',
          }}>{error}</div>
        )}

        {squads.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div className="section-title">已导入的阵容</div>
            {squads.map(s => (
              <button key={s.id}
                onClick={() => { onSelect(s.id); onClose() }}
                className="btn-ghost" style={{ justifyContent: 'flex-start', width: '100%', marginBottom: 2, fontSize: 12 }}
              >
                📋 {s.name}
                <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>{s.player_count} 人</span>
              </button>
            ))}
          </div>
        )}

        <button onClick={onClose} className="btn-ghost"
          style={{ width: '100%', justifyContent: 'center', marginTop: 12, fontSize: 12 }}>
          关闭
        </button>
      </div>
    </div>
  )
}
