import { useState, useEffect, useRef, useCallback } from 'react'
import { MessageBubble } from './components/chat/MessageBubble'
import { ChatInput } from './components/chat/ChatInput'
import { SquadPanel } from './components/panels/SquadPanel'
import { SettingsModal } from './components/chat/SettingsModal'
import { ImportModal } from './components/chat/ImportModal'
import * as api from './api/client'
import { MessageSquare, Users, Swords, Settings, Upload, Trophy } from 'lucide-react'
import type { ChatMessage, Player, SquadInfo, TacticResult } from './types'

type Tab = 'chat' | 'squad' | 'tactics'

const SUGGESTIONS = [
  '📊 帮我分析一下阵容的优缺点',
  '🎯 设计一套高压逼抢的战术',
  '🔄 我的阵容适合什么打法？',
  '📋 生成完整的 433 战术方案',
  '🛡️ 防线速度慢该怎么办',
  '💰 3000万预算该补哪个位置',
]

export default function App() {
  // State
  const [apiKey, setApiKey] = useState('')
  const [apiBaseUrl, setApiBaseUrl] = useState('https://api.deepseek.com')
  const [showSettings, setShowSettings] = useState(false)
  const [showImport, setShowImport] = useState(false)

  const [squads, setSquads] = useState<SquadInfo[]>([])
  const [activeSquadId, setActiveSquadId] = useState<number | null>(null)
  const [players, setPlayers] = useState<Player[]>([])

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')

  const [activeTab, setActiveTab] = useState<Tab>('chat')

  const chatEndRef = useRef<HTMLDivElement>(null)
  const messagesRef = useRef<ChatMessage[]>([])

  useEffect(() => { messagesRef.current = messages }, [messages])

  // Init
  useEffect(() => {
    api.getConfigStatus().then(s => {
      if (s.has_api_key) {
        setApiBaseUrl(s.api_base_url)
        setApiKey('***')
      } else {
        setShowSettings(true)
      }
    })
    api.getSquads().then(s => {
      setSquads(s)
      if (s.length > 0) {
        setActiveSquadId(s[0].id)
        api.getPlayers(s[0].id).then(setPlayers)
      }
    })
  }, [])

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const selectSquad = useCallback(async (id: number) => {
    setActiveSquadId(id)
    const p = await api.getPlayers(id)
    setPlayers(p)
  }, [])

  const handleSend = useCallback(async (text: string) => {
    if (!activeSquadId) {
      setMessages(prev => [...prev, {
        role: 'system', content: '请先导入阵容数据！点击右上角 📤 按钮导入 FMRTE CSV 文件。'
      }])
      return
    }

    const userMsg: ChatMessage = { role: 'user', content: text, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)
    setStreamingText('')

    let fullText = ''

    try {
      const history = messagesRef.current.map(m => ({ role: m.role, content: m.content }))
      for await (const chunk of api.streamChat(text, activeSquadId, history)) {
        if (chunk.type === 'text') {
          fullText += chunk.content
          setStreamingText(fullText)
        } else if (chunk.type === 'error') {
          fullText += `\n\n❌ ${chunk.message}`
          setStreamingText(fullText)
        }
      }
    } catch (e: any) {
      fullText += `\n\n❌ 错误: ${e.message}`
      setStreamingText(fullText)
    }

    if (fullText.trim()) {
      setMessages(prev => [...prev, {
        role: 'assistant', content: fullText, timestamp: new Date().toISOString()
      }])
    }
    setStreamingText('')
    setIsStreaming(false)
  }, [activeSquadId])

  const handleImport = useCallback(async (file: File) => {
    try {
      const result = await api.uploadCSV(file)
      if (result.success) {
        setShowImport(false)
        const updated = await api.getSquads()
        setSquads(updated)
        if (result.squad_id) await selectSquad(result.squad_id)
        setMessages(prev => [...prev, {
          role: 'system',
          content: `✅ 成功导入 **${result.player_count}** 名球员！\n\n可以开始对话了，试着问我：\n• "帮我分析一下阵容"\n• "设计一套高压逼抢的战术"`,
          timestamp: new Date().toISOString(),
        }])
      }
    } catch (e: any) {
      setMessages(prev => [...prev, {
        role: 'system', content: `❌ 导入失败: ${e.message}`, timestamp: new Date().toISOString()
      }])
    }
  }, [selectSquad])

  const handleSaveConfig = useCallback(async (key: string, url: string, model: string) => {
    await api.setConfig(key, url, model)
    setApiKey('***')
    setApiBaseUrl(url)
    setShowSettings(false)
  }, [])

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="app-sidebar">
        <nav className="sidebar-nav">
          <button className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}>
            <MessageSquare size={16} /> 对话
          </button>
          <button className={`nav-item ${activeTab === 'squad' ? 'active' : ''}`}
            onClick={() => setActiveTab('squad')}>
            <Users size={16} /> 阵容
            {players.length > 0 && <span className="badge">{players.length}</span>}
          </button>
          <button className={`nav-item ${activeTab === 'tactics' ? 'active' : ''}`}
            onClick={() => setActiveTab('tactics')}>
            <Swords size={16} /> 战术历史
          </button>

          <hr className="sidebar-divider" />

          <button className="nav-item" onClick={() => setShowImport(true)}>
            <Upload size={16} /> 导入数据
          </button>
          <button className="nav-item" onClick={() => setShowSettings(true)}>
            <Settings size={16} /> API 设置
          </button>
        </nav>

        {/* Sidebar panels */}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 8px 12px' }}>
          {activeTab === 'squad' && <SquadPanel players={players} />}
          {activeTab === 'tactics' && (
            <div className="empty-state">
              <div className="icon">📋</div>
              <div className="title">战术历史</div>
              <div className="subtitle">生成战术后自动保存在这里</div>
            </div>
          )}
        </div>

        {/* Status */}
        <div className="status-bar" style={{ borderTop: '1px solid var(--border)', background: 'transparent' }}>
          <span className={`status-dot ${activeSquadId ? '' : 'offline'}`} />
          {activeSquadId ? `${players.length} 名球员` : '未导入数据'}
        </div>
      </aside>

      {/* Main */}
      <div className="main-content">
        {/* Header */}
        <header className="app-header">
          <div className="logo">⚽</div>
          <h1>FM2024 战术顾问</h1>
          <span className="subtitle">AI 助理教练</span>
          <div className="header-actions">
            {activeSquadId && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginRight: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                <Trophy size={12} />
                {squads.find(s => s.id === activeSquadId)?.club_name || ''}
              </span>
            )}
          </div>
        </header>

        {/* Chat */}
        <div className="chat-container" id="chat-scroll">
          {messages.length === 0 && !isStreaming && (
            <div className="welcome-card">
              <div className="icon">🧠</div>
              <h2>{activeSquadId ? '阵容已就绪，开始对话吧' : '欢迎使用 FM2024 战术顾问'}</h2>
              <p>
                {activeSquadId
                  ? `已加载 ${players.length} 名球员。AI 助理教练可以帮你分析阵容、设计战术、制定赛前方案。`
                  : '我是你的 AI 助理教练。先设置 API Key，然后导入 FMRTE 阵容数据，我就能为你出谋划策。'}
              </p>
              {activeSquadId && (
                <div className="welcome-suggestions">
                  {SUGGESTIONS.map(s => (
                    <button key={s} onClick={() => handleSend(s)}>{s}</button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}

          {isStreaming && streamingText && (
            <MessageBubble message={{ role: 'assistant', content: streamingText }} isStreaming />
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          onSend={handleSend}
          disabled={isStreaming}
          placeholder={activeSquadId ? "聊聊战术，比如「帮我设计一套高压433」..." : "请先导入阵容数据"}
        />
      </div>

      {/* Modals */}
      {showSettings && (
        <SettingsModal
          apiKey={apiKey}
          apiBaseUrl={apiBaseUrl}
          onSave={handleSaveConfig}
          onClose={() => setShowSettings(false)}
        />
      )}
      {showImport && (
        <ImportModal
          squads={squads}
          onImport={handleImport}
          onSelect={selectSquad}
          onClose={() => setShowImport(false)}
        />
      )}
    </div>
  )
}
