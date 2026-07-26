import type { ChatMessage } from '../../types'

interface Props {
  message: ChatMessage
  isStreaming?: boolean
}

function formatContent(text: string): string {
  // Basic markdown formatting
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^\- (.+)$/gm, '<li>$1</li>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
}

const AVATARS: Record<string, { emoji: string; label: string }> = {
  user: { emoji: '👤', label: '你' },
  assistant: { emoji: '🧠', label: '战术顾问' },
  system: { emoji: '📢', label: '系统' },
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'
  const avatar = AVATARS[message.role] || AVATARS.assistant

  return (
    <div className={`message-row ${isUser ? 'user' : ''}`}>
      {/* Avatar */}
      <div className={`msg-avatar ${message.role}`}>
        {avatar.emoji}
      </div>

      {/* Content */}
      <div style={{ minWidth: 0 }}>
        <div className="msg-sender">{avatar.label}</div>
        <div className={`msg-bubble ${message.role} ${isStreaming ? 'streaming' : ''}`}>
          <div
            className="msg-content"
            dangerouslySetInnerHTML={{
              __html: isStreaming ? formatContent(message.content) + '▊' : formatContent(message.content)
            }}
          />
        </div>
      </div>
    </div>
  )
}
