import { cn } from '@/lib/utils'

export function LaptopFrame({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('flex flex-col items-center', className)}>
      <div
        className="relative w-full rounded-t-2xl rounded-b-lg overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, #2d2d2d 0%, #1a1a1a 100%)',
          padding: '14px 14px 8px 14px',
          boxShadow: '0 0 0 1px rgba(255,255,255,0.08), 0 30px 80px rgba(0,0,0,0.8)',
        }}
      >
        {/* Camera */}
        <div className="flex justify-center mb-2">
          <div className="w-2 h-2 rounded-full bg-[#3a3a3a] flex items-center justify-center">
            <div className="w-1 h-1 rounded-full bg-[#2a2a2a]" />
          </div>
        </div>
        {/* Screen — 16/10 aspect ratio is critical for the laptop illusion */}
        <div className="rounded-sm overflow-hidden" style={{ background: '#ffffff', aspectRatio: '16/10' }}>
          {children}
        </div>
      </div>
      {/* Hinge */}
      <div className="w-full h-2" style={{ background: 'linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%)', borderRadius: '0 0 2px 2px' }} />
      {/* Base */}
      <div className="w-[106%] h-4 rounded-b-2xl" style={{ background: 'linear-gradient(180deg, #2d2d2d 0%, #252525 100%)', boxShadow: '0 8px 32px rgba(0,0,0,0.6)' }} />
      {/* Reflection */}
      <div className="w-[80%] h-2 rounded-full mt-1" style={{ background: 'rgba(255,255,255,0.03)', filter: 'blur(4px)' }} />
    </div>
  )
}
