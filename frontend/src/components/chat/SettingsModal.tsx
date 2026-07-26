import { useState } from 'react'
import { X } from 'lucide-react'

interface Props {
  apiKey: string
  apiBaseUrl: string
  onSave: (key: string, url: string, model: string) => void
  onClose: () => void
}

const PRESETS = [
  { label: 'DeepSeek', url: 'https://api.deepseek.com', model: 'deepseek-chat' },
  { label: 'Anthropic', url: 'https://api.anthropic.com', model: 'claude-sonnet-4-20250514' },
  { label: 'OpenAI', url: 'https://api.openai.com/v1', model: 'gpt-4o' },
]

export function SettingsModal({ apiKey, apiBaseUrl, onSave, onClose }: Props) {
  const [key, setKey] = useState('')
  const [url, setUrl] = useState(apiBaseUrl)
  const [model, setModel] = useState('deepseek-chat')

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal" onClick={e => e.stopPropagation()}>

        <div className="form-group" style={{ marginBottom: 4 }}>
          <label>快速选择</label>
          <div style={{ display: 'flex', gap: 6 }}>
            {PRESETS.map(p => (
              <button key={p.label}
                className="btn-ghost"
                style={{ flex: 1, fontSize: 11, justifyContent: 'center' }}
                onClick={() => { setUrl(p.url); setModel(p.model) }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>API Key</label>
          <input
            type="password"
            value={key}
            onChange={e => setKey(e.target.value)}
            placeholder="sk-..."
          />
        </div>

        <div className="form-group">
          <label>API 地址</label>
          <input type="text" value={url} onChange={e => setUrl(e.target.value)} />
        </div>

        <div className="form-group">
          <label>模型名称</label>
          <input type="text" value={model} onChange={e => setModel(e.target.value)}
            placeholder="deepseek-chat" />
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
            根据你的 API 服务支持的模型填写
          </div>
        </div>

        <button className="btn-primary" onClick={() => onSave(key, url, model)} disabled={!key}>
          保存并连接
        </button>
      </div>
    </div>
  )
}
