interface Slot {
  slot: string
  player: string | null
  role: string | null
  score: number
  locked?: boolean
}

interface Props {
  formation: string
  slots: Slot[]
  width?: number
  height?: number
}

// Position coordinates for common formations
const POSITION_COORDS: Record<string, {x: number; y: number}> = {
  GK: {x: 50, y: 90},
  DCR: {x: 30, y: 75},
  DC: {x: 50, y: 78},
  DCL: {x: 70, y: 75},
  DR: {x: 85, y: 72},
  DL: {x: 15, y: 72},
  WBR: {x: 92, y: 62},
  WBL: {x: 8, y: 62},
  DM: {x: 50, y: 58},
  MCR: {x: 35, y: 48},
  MCL: {x: 65, y: 48},
  MC: {x: 50, y: 50},
  MR: {x: 88, y: 48},
  ML: {x: 12, y: 48},
  AMR: {x: 88, y: 30},
  AML: {x: 12, y: 30},
  AMC: {x: 50, y: 35},
  STC: {x: 50, y: 15},
  STCR: {x: 38, y: 15},
  STCL: {x: 62, y: 15},
}

export function FormationPitch({ slots, width = 240, height = 360 }: Props) {
  return (
    <div
      className="pitch rounded-lg relative overflow-hidden mx-auto"
      style={{ width, height }}
    >
      {/* Pitch markings */}
      <div className="pitch-line" style={{ left: '10%', top: '50%', width: '80%', height: 1 }} />
      <div className="pitch-line rounded-full border" style={{
        left: '35%', top: '42%', width: '30%', height: '16%',
        borderColor: 'rgba(255,255,255,0.3)'
      }} />
      <div className="pitch-line rounded-full border" style={{
        left: '23%', top: '20%', width: '54%', height: '18%',
        borderColor: 'rgba(255,255,255,0.2)', borderRadius: '50%'
      }} />
      <div className="pitch-line" style={{ left: '10%', top: '87%', width: '12%', height: '8%', border: '1px solid rgba(255,255,255,0.3)' }} />
      <div className="pitch-line" style={{ right: '10%', top: '87%', width: '12%', height: '8%', border: '1px solid rgba(255,255,255,0.3)' }} />

      {/* Players */}
      {slots.map((slot, i) => {
        const pos = POSITION_COORDS[slot.slot] || {x: 50, y: 50}
        const hasScore = slot.score > 0
        const scoreColor = slot.score >= 80 ? '#4ade80' :
          slot.score >= 70 ? '#facc15' :
          slot.score >= 60 ? '#fb923c' : '#f87171'

        return (
          <div key={i}
            className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
            style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
          >
            {/* Jersey dot */}
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold border-2
              ${slot.locked ? 'border-yellow-400 bg-gray-800 text-yellow-400' :
                hasScore ? 'border-green-500/70 bg-gray-800/90 text-gray-200' :
                'border-red-500/50 bg-gray-800/70 text-red-300'}`}
            >
              {slot.slot}
            </div>

            {/* Player name */}
            {slot.player && (
              <div className="mt-0.5 text-[8px] text-gray-200 text-center leading-tight max-w-[60px] truncate">
                {slot.player}
              </div>
            )}

            {/* Role */}
            {slot.role && (
              <div className="text-[7px] text-gray-400 text-center leading-tight truncate max-w-[60px]">
                {slot.role}
              </div>
            )}

            {/* Score */}
            {hasScore && (
              <div className="text-[8px] font-bold mt-0.5" style={{color: scoreColor}}>
                {slot.score}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
