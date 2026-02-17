import { cn } from '@/lib/utils'
import { GameStage } from '@/types'

interface GamePromptProps {
  stage: GameStage
}

const PROMPTS: Record<GameStage, { emoji: string; text: string; sub: string; color: string } | null> = {
  idle: {
    emoji: '👇',
    text: 'Try suggesting something off-agenda',
    sub: 'e.g. "Let\'s work on the mobile app" or "What about the consumer redesign?"',
    color: 'bg-violet-50 border-violet-200 text-violet-700',
  },
  misaligned: {
    emoji: '⚡',
    text: 'MiniMem caught it! Now try to get back on track',
    sub: 'e.g. "Right, let\'s focus on SSO integration" or "What about the enterprise dashboard?"',
    color: 'bg-amber-50 border-amber-200 text-amber-700',
  },
  aligned: null,
}

export function GamePrompt({ stage }: GamePromptProps) {
  const prompt = PROMPTS[stage]
  if (!prompt) return null

  return (
    <div className={cn('mx-4 mb-3 rounded-lg border px-3 py-2 message-enter', prompt.color)}>
      <p className="text-[12px] font-bold">
        {prompt.emoji} {prompt.text}
      </p>
      <p className="text-[11px] mt-0.5 opacity-80">{prompt.sub}</p>
    </div>
  )
}
