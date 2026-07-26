export interface Player {
  id: number
  squad_id: number
  uid: string
  name: string
  age: number
  nationality: string
  club: string
  position: string
  best_position: string
  preferred_foot: string
  height: number
  weight: number
  personality: string
  media_description: string
  current_ability: number
  potential_ability: number
  value: string
  wage: string
  // Technical
  corners: number
  crossing: number
  dribbling: number
  finishing: number
  first_touch: number
  free_kicks: number
  heading: number
  long_shots: number
  long_throws: number
  marking: number
  passing: number
  penalty_taking: number
  tackling: number
  technique: number
  // Mental
  aggression: number
  anticipation: number
  bravery: number
  composure: number
  concentration: number
  decisions: number
  determination: number
  flair: number
  leadership: number
  off_the_ball: number
  positioning: number
  teamwork: number
  vision: number
  work_rate: number
  // Physical
  acceleration: number
  agility: number
  balance: number
  jumping_reach: number
  natural_fitness: number
  pace: number
  stamina: number
  strength: number
  // GK
  aerial_reach: number
  command_of_area: number
  communication: number
  eccentricity: number
  handling: number
  kicking: number
  one_on_ones: number
  reflexes: number
  rushing_out: number
  throwing: number
  tendency_to_punch: number
}

export interface SquadInfo {
  id: number
  name: string
  club_name: string
  import_date: string
  player_count: number
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  tool_calls?: string
  tool_use_id?: string
  timestamp?: string
}

export interface StreamChunk {
  type: 'text' | 'tool_call' | 'done' | 'error'
  content?: string
  id?: string
  name?: string
  input?: Record<string, any>
  message?: string
}

export interface TacticRecord {
  id: number
  name: string
  formation: string
  mentality: string
  created_at: string
  instructions_json: string
  player_roles_json: string
}

export interface FormationSlot {
  slot: string
  player: string
  role: string
  role_key: string
  score: number
  reasoning: string
  alternative?: Array<{player: string; role: string; score: number}>
}

export interface TacticResult {
  formation: string
  formation_name: string
  style: string
  starting_xi: FormationSlot[]
  bench: Array<{player: string; position: string; best_role: string; ca: number}>
  balance_check: {
    defend_duties: number
    support_duties: number
    attack_duties: number
    is_balanced: boolean
    issues: Array<{type: string; message: string}>
  }
  team_instructions?: any
  player_instructions?: any
}
