import { useState } from 'react'
import { Search, ChevronRight } from 'lucide-react'
import type { Player } from '../../types'

interface Props {
  players: Player[]
}

function attrClass(val: number): string {
  if (val >= 16) return 'elite'
  if (val >= 13) return 'good'
  return 'avg'
}

export function SquadPanel({ players }: Props) {
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const filtered = players.filter(p =>
    !search || p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.position || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={{ paddingTop: 4 }}>
      <div className="section-title">球员列表</div>

      {/* Search */}
      <div className="squad-search">
        <Search size={12} />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索球员..."
        />
      </div>

      {/* List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {filtered.slice(0, 50).map(p => {
          const isOpen = selectedId === p.id
          const ca = Number(p.current_ability) || 0

          return (
            <div key={p.id}>
              <button
                onClick={() => setSelectedId(isOpen ? null : p.id)}
                className="player-mini-card"
                style={{ width: '100%', border: isOpen ? '1px solid var(--accent-dim)' : undefined }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: ca >= 150 ? 'var(--warning)' : ca >= 130 ? 'var(--accent-bright)' : ca >= 110 ? 'var(--blue)' : 'var(--text-muted)',
                    flexShrink: 0,
                  }} />
                  <span className="name" style={{ flex: 1 }}>{p.name}</span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)', marginRight: 4 }}>{p.position}</span>
                  <ChevronRight size={12} style={{
                    color: 'var(--text-muted)',
                    transform: isOpen ? 'rotate(90deg)' : 'none',
                    transition: 'transform 0.15s',
                  }} />
                </div>
              </button>

              {/* Expanded detail */}
              {isOpen && (
                <div style={{
                  background: 'var(--bg-tertiary)',
                  borderRadius: '0 0 8px 8px',
                  padding: '8px 12px',
                  marginBottom: 4,
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', marginBottom: 8 }}>
                    <Row label="年龄" value={String(p.age)} />
                    <Row label="惯用脚" value={p.preferred_foot} />
                    <Row label="CA / PA" value={`${p.current_ability} / ${p.potential_ability}`} />
                    <Row label="性格" value={p.personality} />
                  </div>
                  <div className="attr-row" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                    {([
                      ['速度', Number(p.pace) || 0],
                      ['爆发', Number(p.acceleration) || 0],
                      ['耐力', Number(p.stamina) || 0],
                      ['传球', Number(p.passing) || 0],
                      ['抢断', Number(p.tackling) || 0],
                      ['射门', Number(p.finishing) || 0],
                      ['盘带', Number(p.dribbling) || 0],
                      ['视野', Number(p.vision) || 0],
                      ['投入', Number(p.work_rate) || 0],
                    ] as [string, number][]).map(([label, val]) => (
                      <div className="attr-item" key={label}>
                        <div className="attr-label">{label}</div>
                        <div className={`attr-value ${attrClass(val)}`}>{val}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {!filtered.length && (
        <div className="empty-state">
          <div className="icon">👥</div>
          <div className="subtitle">{players.length ? '无匹配结果' : '尚未导入球员数据'}</div>
        </div>
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{value || '-'}</span>
    </div>
  )
}
