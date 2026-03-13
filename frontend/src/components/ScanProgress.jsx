/**
 * components/ScanProgress.jsx
 * ----------------------------
 * Animated scanning indicator shown while the backend is processing.
 * Cycles through status messages to give the user feedback.
 */

import { useState, useEffect } from 'react'

const STAGES = [
  'Initialising scanner...',
  'Crawling target endpoints...',
  'Probing for SQL Injection vectors...',
  'Testing XSS attack surfaces...',
  'Auditing HTTP security headers...',
  'Scanning directory exposure...',
  'Running AI risk prediction...',
  'Compiling vulnerability report...',
]

export default function ScanProgress({ target }) {
  const [stageIndex, setStageIndex] = useState(0)
  const [dots, setDots] = useState('')

  // Cycle through stages every 2 seconds
  useEffect(() => {
    const id = setInterval(() => {
      setStageIndex(i => (i + 1) % STAGES.length)
    }, 2000)
    return () => clearInterval(id)
  }, [])

  // Animate trailing dots
  useEffect(() => {
    const id = setInterval(() => {
      setDots(d => (d.length >= 3 ? '' : d + '.'))
    }, 400)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="panel p-6 animate-fade-in">
      {/* Target header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="font-mono text-xs text-accent tracking-widest uppercase mb-1">
            // ACTIVE SCAN
          </p>
          <p className="font-mono text-sm text-white truncate max-w-xs">{target}</p>
        </div>
        {/* Live badge */}
        <span className="flex items-center gap-2 bg-critical/10 border border-critical/30
                         text-critical font-mono text-xs px-3 py-1 rounded-full">
          <span className="w-1.5 h-1.5 bg-critical rounded-full animate-pulse-dot" />
          LIVE
        </span>
      </div>

      {/* Radar animation */}
      <div className="flex justify-center mb-6">
        <div className="relative w-36 h-36">
          {/* Concentric rings */}
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="absolute inset-0 rounded-full border border-accent/20"
              style={{
                transform: `scale(${0.4 + i * 0.3})`,
                top: `${i * 15}%`,
                left: `${i * 15}%`,
                right: `${i * 15}%`,
                bottom: `${i * 15}%`,
              }}
            />
          ))}
          {/* Rotating sweep */}
          <div className="absolute inset-0 rounded-full overflow-hidden">
            <div
              className="absolute inset-0 rounded-full"
              style={{
                background: 'conic-gradient(from 0deg, transparent 75%, rgba(0,212,255,0.3) 100%)',
                animation: 'spin 2s linear infinite',
              }}
            />
          </div>
          {/* Center dot */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2 h-2 bg-accent rounded-full"
                 style={{ boxShadow: '0 0 8px #00d4ff' }} />
          </div>
          {/* Blip dots (random positions) */}
          {[
            { top: '25%', left: '60%' },
            { top: '65%', left: '35%' },
            { top: '40%', left: '20%' },
          ].map((pos, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-accent rounded-full animate-pulse-dot"
              style={{ ...pos, animationDelay: `${i * 0.5}s`,
                       boxShadow: '0 0 4px #00d4ff' }}
            />
          ))}
        </div>
      </div>

      {/* Current stage */}
      <div className="bg-surface rounded-lg p-4 border border-border/50">
        <p className="font-mono text-xs text-accent mb-2 tracking-wider">
          CURRENT OPERATION
        </p>
        <p className="font-mono text-sm text-white">
          {STAGES[stageIndex]}<span className="text-accent">{dots}</span>
        </p>
      </div>

      {/* Progress bar */}
      <div className="mt-4">
        <div className="flex justify-between font-mono text-xs text-muted mb-1.5">
          <span>Scan Progress</span>
          <span>{Math.round(((stageIndex + 1) / STAGES.length) * 100)}%</span>
        </div>
        <div className="h-1 bg-surface rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${((stageIndex + 1) / STAGES.length) * 100}%`,
              background: 'linear-gradient(90deg, #0099cc, #00d4ff)',
              boxShadow: '0 0 8px rgba(0,212,255,0.5)',
            }}
          />
        </div>
      </div>

      {/* Stage log */}
      <div className="mt-4 space-y-1 max-h-24 overflow-hidden">
        {STAGES.slice(0, stageIndex + 1).reverse().slice(0, 3).map((s, i) => (
          <p key={i} className={`font-mono text-xs transition-all ${
            i === 0 ? 'text-accent' : 'text-muted/50'
          }`}>
            [{i === 0 ? 'RUN' : 'OK '}] {s.replace('...', '')}
          </p>
        ))}
      </div>
    </div>
  )
}
