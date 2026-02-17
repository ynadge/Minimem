'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Hash, AtSign, Smile, Paperclip, Bold } from 'lucide-react'
import { LaptopFrame } from '@/components/LaptopFrame'
import { SlackSidebar } from '@/components/SlackSidebar'
import { ChatMessage } from '@/components/ChatMessage'
import { TypingIndicator } from '@/components/TypingIndicator'
import { MeetingNotesPanel } from '@/components/MeetingNotesPanel'
import { GamePrompt } from '@/components/GamePrompt'
import { Message, GameStage } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_TIMEOUT_MS = 15_000

const ALEX_OPENER: Omit<Message, 'id' | 'timestamp'> = {
  sender: 'alex',
  content: "Hey! Sprint planning time 🎉 I've been thinking about what we should focus on next — what do you think our top priority should be?",
}

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { ...options, signal: controller.signal })
    clearTimeout(timeoutId)
    return res
  } catch (err) {
    clearTimeout(timeoutId)
    throw err
  }
}

function MiniMemAnalyzing() {
  return (
    <div className="flex gap-3 px-4 py-1 message-enter">
      <div className="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-xl">
        🧠
      </div>
      <div className="flex-1">
        <div className="flex items-baseline gap-2 mb-1.5">
          <span className="font-bold text-sm text-amber-600">MiniMem</span>
          <span className="text-[9px] bg-amber-100 text-amber-700 border border-amber-300 px-1 rounded font-bold uppercase tracking-wide">
            BOT
          </span>
          <span className="text-[11px] text-[#616061]">is scanning context...</span>
        </div>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-amber-400"
              style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isAlexTyping, setIsAlexTyping] = useState(false)
  const [isMinimemAnalyzing, setIsMinimemAnalyzing] = useState(false)
  const [gameStage, setGameStage] = useState<GameStage>('idle')
  const [newMessageIds, setNewMessageIds] = useState<Set<string>>(new Set())
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Alex "arrives" and opens the conversation after 1.5s
  useEffect(() => {
    const t = setTimeout(() => {
      addMessage({ ...ALEX_OPENER, id: 'opener', timestamp: new Date() })
    }, 1500)
    return () => clearTimeout(t)
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isAlexTyping, isMinimemAnalyzing])

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
  }, [input])

  function addMessage(msg: Message) {
    setMessages((prev) => [...prev, msg])
    setNewMessageIds((prev) => new Set(prev).add(msg.id))
    setTimeout(() => {
      setNewMessageIds((prev) => { const n = new Set(prev); n.delete(msg.id); return n })
    }, 1200)
  }

  async function handleSend() {
    const content = input.trim()
    if (!content || isSending) return
    setIsSending(true)

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content,
      timestamp: new Date(),
    }
    addMessage(userMsg)
    setInput('')

    // Build history (exclude minimem bot messages — backend doesn't need them)
    const history = [...messages, userMsg]
      .filter((m) => m.sender !== 'minimem')
      .map((m) => ({ sender: m.sender, content: m.content, timestamp: m.timestamp.toISOString() }))

    setIsAlexTyping(true)

    try {
      // Fire both in parallel — they are independent operations
      const [chatRes, analyzeRes] = await Promise.all([
        fetchWithTimeout(
          `${API_BASE}/api/chat`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: content, history }),
          },
          API_TIMEOUT_MS
        ),
        fetchWithTimeout(
          `${API_BASE}/api/analyze`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: content, history }),
          },
          API_TIMEOUT_MS
        ),
      ])

      if (!chatRes.ok || !analyzeRes.ok) {
        throw new Error(`API error: chat=${chatRes.status} analyze=${analyzeRes.status}`)
      }

      const [chatData, alignmentData] = await Promise.all([chatRes.json(), analyzeRes.json()])

      // Alex responds after a natural-feeling delay
      setTimeout(() => {
        setIsAlexTyping(false)

        addMessage({
          id: `alex-${Date.now()}`,
          sender: 'alex',
          content: chatData.content,
          timestamp: new Date(),
        })

        setIsMinimemAnalyzing(true)

        // MiniMem posts 900ms after Alex — gives the user time to read Alex's reply first
        setTimeout(() => {
          setIsMinimemAnalyzing(false)

          if (!alignmentData.aligned) {
            // Misalignment detected
            addMessage({
              id: `minimem-${Date.now()}`,
              sender: 'minimem',
              content: '',
              timestamp: new Date(),
              alertType: 'warning',
              alertData: {
                issue:              alignmentData.issue,
                relevant_decision:  alignmentData.relevant_decision,
                meeting_title:      alignmentData.meeting_title,
                meeting_date:       alignmentData.meeting_date,
                severity:           alignmentData.severity,
              },
            })
            setGameStage('misaligned')
          } else if (gameStage === 'misaligned') {
            // Was misaligned, now back on track — post success + complete the loop
            addMessage({
              id: `minimem-success-${Date.now()}`,
              sender: 'minimem',
              content: '',
              timestamp: new Date(),
              alertType: 'success',
              alertData: {},
            })
            setGameStage('aligned')
          }

          setIsSending(false)
        }, 900)
      }, 1400)

    } catch (err) {
      // Recover gracefully — never leave the user stuck
      console.error('API error:', err)
      setIsAlexTyping(false)
      setIsMinimemAnalyzing(false)
      setIsSending(false)

      const isTimeout = err instanceof Error && err.name === 'AbortError'

      addMessage({
        id: `error-${Date.now()}`,
        sender: 'alex',
        content: isTimeout
          ? "Hmm, I'm taking a while to respond — give me a sec and try again?"
          : "Sorry, I'm having connection issues. Try again in a moment!",
        timestamp: new Date(),
      })
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <main
      className="h-screen w-screen overflow-hidden flex items-center justify-center p-4"
      style={{
        background: '#1a1a2e',
        backgroundImage: `
          radial-gradient(ellipse at 20% 50%, rgba(97, 31, 105, 0.15) 0%, transparent 50%),
          radial-gradient(ellipse at 80% 20%, rgba(74, 21, 75, 0.1) 0%, transparent 50%)
        `,
      }}
    >
      <div className="w-full h-full">
        <LaptopFrame>
          <div className="flex h-full" style={{ fontFamily: "'Lato', sans-serif" }}>
            <SlackSidebar />

            {/* Main area */}
            <div className="flex flex-col flex-1 min-w-0 bg-white">

              {/* Channel header */}
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#e8e8e8] flex-shrink-0">
                <Hash className="w-4 h-4 text-[#616061]" />
                <span className="font-black text-[#1d1c1d] text-[14px]">sprint-planning</span>
                <div className="ml-2 h-4 w-px bg-[#e8e8e8]" />
                <span className="text-[12px] text-[#616061]">3 members</span>
                <div className="ml-auto flex items-center gap-3">
                  <AtSign className="w-4 h-4 text-[#616061] cursor-pointer hover:text-[#1d1c1d]" />
                </div>
              </div>

              {/* Scrollable content: meeting notes + game prompt + messages */}
              <div className="flex-1 overflow-y-auto">
                {/* Date divider */}
                <div className="flex items-center gap-3 px-4 py-3">
                  <div className="flex-1 h-px bg-[#e8e8e8]" />
                  <span className="text-[11px] text-[#616061] font-semibold border border-[#e8e8e8] rounded-full px-2 py-0.5">
                    Today
                  </span>
                  <div className="flex-1 h-px bg-[#e8e8e8]" />
                </div>

                {/* Pinned meeting notes */}
                <MeetingNotesPanel />

                {/* Game prompt — changes with stage */}
                <GamePrompt stage={gameStage} />

                {/* Messages */}
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} isNew={newMessageIds.has(msg.id)} />
                ))}

                {isAlexTyping && <TypingIndicator name="Alex Chen" />}
                {isMinimemAnalyzing && <MiniMemAnalyzing />}

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="px-4 pb-3 flex-shrink-0">
                <div className="border border-[#e8e8e8] rounded-lg overflow-hidden">
                  <div className="flex items-center gap-1 px-3 pt-2 pb-1 border-b border-[#e8e8e8]">
                    <Bold className="w-3 h-3 text-[#616061] cursor-pointer hover:text-[#1d1c1d]" />
                    <div className="w-px h-3 bg-[#e8e8e8] mx-1" />
                    <Smile className="w-3 h-3 text-[#616061] cursor-pointer hover:text-[#1d1c1d]" />
                    <Paperclip className="w-3 h-3 text-[#616061] cursor-pointer hover:text-[#1d1c1d]" />
                  </div>
                  <div className="flex items-end gap-2 px-3 py-2">
                    <textarea
                      ref={textareaRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Message #sprint-planning"
                      className="flex-1 resize-none outline-none text-sm text-[#1d1c1d] placeholder-[#a0a0a0] max-h-[120px] overflow-y-auto"
                      rows={1}
                      disabled={isSending}
                      style={{ fontFamily: "'Lato', sans-serif", height: 'auto' }}
                    />
                    <button
                      onClick={handleSend}
                      disabled={!input.trim() || isSending}
                      className="flex-shrink-0 w-7 h-7 rounded flex items-center justify-center bg-[#611f69] text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#4A154B] transition-colors"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </LaptopFrame>
      </div>
    </main>
  )
}
