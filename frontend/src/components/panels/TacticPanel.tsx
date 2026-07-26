import { useState, useEffect } from 'react'
import { FileText, Clock } from 'lucide-react'
import * as api from '../../api/client'
import type { TacticRecord } from '../../types'

interface Props {
  squadId: number | null
  onSelectTactic: (tactic: any) => void
}

export function TacticPanel({ squadId, onSelectTactic }: Props) {
  const [tactics, setTactics] = useState<TacticRecord[]>([])

  useEffect(() => {
    if (squadId) api.getTactics(squadId).then(setTactics)
  }, [squadId])

  return (
    <div className="space-y-1">
      <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider px-1 mb-2">
        战术历史
      </h3>
      {tactics.map(t => (
        <button
          key={t.id}
          onClick={() => {
            try {
              const roles = JSON.parse(t.player_roles_json || '{}')
              const inst = JSON.parse(t.instructions_json || '{}')
              onSelectTactic({ ...t, roles, instructions: inst })
            } catch {
              onSelectTactic(t)
            }
          }}
          className="w-full flex items-start gap-2 px-2 py-2 rounded hover:bg-gray-800 text-left"
        >
          <FileText size={14} className="text-gray-500 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-gray-300 truncate">{t.name}</p>
            <p className="text-[10px] text-gray-500">
              {t.formation} · {t.mentality}
            </p>
            <div className="flex items-center gap-1 mt-0.5">
              <Clock size={10} className="text-gray-600" />
              <span className="text-[10px] text-gray-600">
                {t.created_at?.slice(0, 10)}
              </span>
            </div>
          </div>
        </button>
      ))}
      {!tactics.length && (
        <p className="text-xs text-gray-600 text-center py-4">
          暂无保存的战术
        </p>
      )}
    </div>
  )
}
