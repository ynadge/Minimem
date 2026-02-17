export type MessageSender = 'user' | 'alex' | 'minimem'
export type MinimemAlertType = 'warning' | 'success'
export type GameStage = 'idle' | 'misaligned' | 'aligned'

export interface Message {
  id: string
  sender: MessageSender
  content: string
  timestamp: Date
  alertType?: MinimemAlertType
  alertData?: {
    issue?: string
    relevant_decision?: string
    meeting_title?: string
    meeting_date?: string
    severity?: 'low' | 'medium' | 'high'
  }
}

export interface Meeting {
  id: number
  title: string
  date: string
  decisions: string[]
  participants: string[]
}

export interface AlignmentResult {
  aligned: boolean
  issue: string | null
  relevant_decision: string | null
  meeting_title: string | null
  meeting_date: string | null
  similarity: number
  severity: 'low' | 'medium' | 'high' | null
}
