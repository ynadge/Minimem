import { Hash, Circle, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

const CHANNELS = [
  { name: 'general', active: false },
  { name: 'sprint-planning', active: true },
  { name: 'engineering', active: false },
]

const DMS = [
  { name: 'Alex Chen', online: true, initials: 'AC' },
  { name: 'Sarah Fisher', online: true, initials: 'SF' },
  { name: 'Mike Rodriguez', online: false, initials: 'MR' },
  { name: 'Priya Nair', online: true, initials: 'PN' },
]

export function SlackSidebar() {
  return (
    <div className="hidden md:flex flex-col h-full text-[#d1d2d3] select-none flex-shrink-0" style={{ background: '#3F0E40', width: '200px' }}>
      {/* Workspace header */}
      <div className="px-4 py-3 flex items-center justify-between border-b border-white/10">
        <div>
          <div className="font-black text-white text-sm tracking-tight">PreCrimeAI</div>
          <div className="flex items-center gap-1 mt-0.5">
            <Circle className="w-2 h-2 fill-green-400 text-green-400" />
            <span className="text-[10px] text-[#d1d2d3]">You</span>
          </div>
        </div>
        <ChevronDown className="w-4 h-4" />
      </div>

      {/* Channels */}
      <div className="mt-3 px-2">
        <p className="text-[10px] font-bold uppercase tracking-wider px-2 mb-1 text-[#d1d2d3]/70">Channels</p>
        {CHANNELS.map((ch) => (
          <div key={ch.name} className={cn('flex items-center gap-2 px-2 py-[3px] rounded text-sm cursor-pointer', ch.active ? 'bg-[#1164A3] text-white font-semibold' : 'hover:bg-white/10')}>
            <Hash className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{ch.name}</span>
          </div>
        ))}
      </div>

      {/* DMs */}
      <div className="mt-3 px-2">
        <p className="text-[10px] font-bold uppercase tracking-wider px-2 mb-1 text-[#d1d2d3]/70">Direct Messages</p>
        {DMS.map((dm) => (
          <div key={dm.name} className="flex items-center gap-2 px-2 py-[3px] rounded text-sm cursor-pointer hover:bg-white/10">
            <div className="relative flex-shrink-0">
              <div className="w-4 h-4 rounded-sm bg-white/20 flex items-center justify-center">
                <span className="text-[8px] text-white font-bold">{dm.initials}</span>
              </div>
              {dm.online && <Circle className="absolute -bottom-0.5 -right-0.5 w-2 h-2 fill-green-400 text-green-400" />}
            </div>
            <span className="truncate">{dm.name}</span>
          </div>
        ))}
        {/* MiniMem bot */}
        <div className="flex items-center gap-2 px-2 py-[3px] rounded text-sm cursor-pointer hover:bg-white/10">
          <div className="relative flex-shrink-0">
            <div className="w-4 h-4 rounded-sm bg-amber-500/30 flex items-center justify-center text-[9px]">🧠</div>
            <Circle className="absolute -bottom-0.5 -right-0.5 w-2 h-2 fill-green-400 text-green-400" />
          </div>
          <span className="truncate">MiniMem</span>
          <span className="ml-auto text-[8px] bg-amber-500 text-white px-1 rounded font-bold">APP</span>
        </div>
      </div>
    </div>
  )
}
