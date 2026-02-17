'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText } from 'lucide-react'

const AGENDA_NOTES = {
  meeting: 'Q1 All-Hands: The Pivot to B2B',
  date: 'January 15, 2025',
  decisions: [
    'Pivot entirely to B2B enterprise — consumer app is frozen',
    'GoodBad Score app gets zero engineering resources this quarter',
    'Top priorities: enterprise SDK, API dashboard, SSO integration',
    'Target: 3 signed enterprise pilots by March 31st',
    'TrustGuard Security is the lead prospect — close them first',
    'No consumer features without explicit CEO sign-off',
  ],
  attendees: 'Sarah Fisher (CEO), Mike Rodriguez (CTO), Alex Chen (Senior Eng), Priya Nair (Head of Product), Jordan Lee (Sales)',
}

export function MeetingNotesPanel() {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="mx-4 mb-3 rounded-lg border border-[#e8e8e8] overflow-hidden text-[#1d1c1d]">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-3 md:py-2 bg-[#f8f8f8] hover:bg-[#f0f0f0] transition-colors text-left"
      >
        <FileText className="w-3.5 h-3.5 text-[#616061] flex-shrink-0" />
        <span className="text-[12px] font-bold text-[#1d1c1d] flex-1">📌 Pinned: {AGENDA_NOTES.meeting}</span>
        <span className="text-[10px] text-[#616061] mr-1">{AGENDA_NOTES.date}</span>
        {expanded
          ? <ChevronUp className="w-3.5 h-3.5 text-[#616061]" />
          : <ChevronDown className="w-3.5 h-3.5 text-[#616061]" />
        }
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="px-3 py-2.5 bg-white border-t border-[#e8e8e8]">
          <p className="text-[10px] font-bold uppercase tracking-wider text-[#616061] mb-1.5">Key Decisions</p>
          <ul className="space-y-1">
            {AGENDA_NOTES.decisions.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-[12px] text-[#1d1c1d]">
                <span className="text-emerald-500 font-bold mt-0.5 flex-shrink-0">✓</span>
                <span>{d}</span>
              </li>
            ))}
          </ul>
          <p className="text-[10px] text-[#a0a0a0] mt-2">👥 {AGENDA_NOTES.attendees}</p>
        </div>
      )}
    </div>
  )
}
