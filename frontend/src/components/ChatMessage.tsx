import { Message } from '@/types'
import { cn } from '@/lib/utils'
import { AlertTriangle, CheckCircle } from 'lucide-react'

interface ChatMessageProps {
  message: Message
  isNew?: boolean
}

const AVATARS = {
  user:    { initials: 'YO', bg: '#1164A3', label: 'You' },
  alex:    { initials: 'AC', bg: '#2eb67d', label: 'Alex Chen' },
  minimem: { initials: '🧠', bg: 'transparent', label: 'MiniMem' },
}

function formatTime(d: Date) {
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
}

export function ChatMessage({ message, isNew = false }: ChatMessageProps) {
  const avatar = AVATARS[message.sender]
  const isMinimem = message.sender === 'minimem'

  return (
    <div className={cn(
      'flex gap-2 md:gap-3 px-3 md:px-4 py-1 hover:bg-black/[0.03] group',
      isNew && (isMinimem
        ? `minimem-enter ${message.alertType === 'warning' ? 'minimem-pulse' : 'success-pulse'}`
        : 'message-enter')
    )}>
      {/* Avatar */}
      <div
        className="w-8 h-8 md:w-9 md:h-9 rounded-lg flex-shrink-0 flex items-center justify-center mt-0.5"
        style={{ background: avatar.bg }}
      >
        {isMinimem
          ? <span className="text-xl">🧠</span>
          : <span className="text-white text-xs font-bold">{avatar.initials}</span>
        }
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <span className={cn('font-bold text-sm', isMinimem ? 'text-amber-600' : 'text-[#1d1c1d]')}>
            {avatar.label}
          </span>
          {isMinimem && (
            <span className="text-[9px] bg-amber-100 text-amber-700 border border-amber-300 px-1 rounded font-bold uppercase tracking-wide badge-pop">
              BOT
            </span>
          )}
          <span className="text-[11px] text-[#616061]">{formatTime(message.timestamp)}</span>
        </div>

        {isMinimem
          ? <MiniMemAlert message={message} />
          : <p className="text-sm text-[#1d1c1d] mt-0.5 leading-relaxed">{message.content}</p>
        }
      </div>
    </div>
  )
}

function MiniMemAlert({ message }: { message: Message }) {
  const isWarning = message.alertType === 'warning'
  const data = message.alertData ?? {}

  return (
    <div className={cn(
      'mt-1 rounded-lg border-l-4 px-3 py-2.5 text-sm',
      isWarning
        ? 'border-amber-400 bg-amber-50'
        : 'border-emerald-400 bg-emerald-50'
    )}>
      {/* Header */}
      <div className={cn('flex items-center gap-1.5 font-bold mb-1 text-[13px]',
        isWarning ? 'text-amber-700' : 'text-emerald-700'
      )}>
        {isWarning
          ? <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          : <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
        }
        {isWarning ? '⚠️ Alignment Alert' : '✅ Back on Track'}
      </div>

      {/* Warning body */}
      {isWarning && (
        <>
          {data.issue && <p className="text-[13px] text-[#1d1c1d] mb-2">{data.issue}</p>}
          {data.relevant_decision && (
            <div className="bg-white/70 rounded px-2 py-1.5 mb-2 border border-black/5">
              <p className="text-[10px] font-bold text-[#616061] uppercase tracking-wide mb-0.5">Recorded Decision</p>
              <p className="text-[12px] text-[#1d1c1d]">&ldquo;{data.relevant_decision}&rdquo;</p>
            </div>
          )}
          {data.meeting_title && (
            <p className="text-[11px] text-[#616061]">
              📅 {data.meeting_title}
              {data.meeting_date && ` · ${new Date(data.meeting_date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`}
            </p>
          )}
        </>
      )}

      {/* Success body */}
      {!isWarning && (
        <p className="text-[13px] text-emerald-700">
          Conversation is aligned with Q1 priorities. Keep it up! 🚀
        </p>
      )}
    </div>
  )
}
