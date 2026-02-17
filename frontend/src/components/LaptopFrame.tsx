'use client'

import { cn } from '@/lib/utils'
import { useEffect, useState } from 'react'

export function LaptopFrame({ children, className }: { children: React.ReactNode; className?: string }) {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  if (isMobile) {
    return (
      <div className="fixed inset-0 flex flex-col" style={{ fontFamily: "'Lato', sans-serif" }}>
        {children}
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col items-center w-full h-full', className)}>
      <div
        className="relative w-full h-full rounded-2xl overflow-hidden flex flex-col"
        style={{
          background: 'linear-gradient(145deg, #2d2d2d 0%, #1a1a1a 100%)',
          padding: '12px 12px 12px 12px',
          boxShadow:
            '0 0 0 1px rgba(255,255,255,0.08), 0 40px 100px rgba(0,0,0,0.85), 0 0 60px rgba(0,0,0,0.5)',
        }}
      >
        <div className="flex justify-center mb-2 flex-shrink-0">
          <div className="w-2 h-2 rounded-full bg-[#3a3a3a] flex items-center justify-center">
            <div className="w-1 h-1 rounded-full bg-[#2a2a2a]" />
          </div>
        </div>

        <div
          className="rounded-lg overflow-hidden flex-1 min-h-0"
          style={{ background: '#ffffff' }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}
