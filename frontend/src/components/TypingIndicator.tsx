export function TypingIndicator({ name }: { name: string }) {
  return (
    <div className="flex gap-3 px-4 py-1 message-enter">
      <div className="w-9 h-9 rounded-lg bg-[#2eb67d] flex-shrink-0 flex items-center justify-center">
        <span className="text-white text-xs font-bold">AC</span>
      </div>
      <div className="flex-1">
        <div className="flex items-baseline gap-2 mb-1.5">
          <span className="font-bold text-sm text-[#1d1c1d]">{name}</span>
          <span className="text-[11px] text-[#616061]">is typing...</span>
        </div>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <div key={i} className="w-2 h-2 rounded-full bg-[#616061]"
              style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
          ))}
        </div>
      </div>
    </div>
  )
}
