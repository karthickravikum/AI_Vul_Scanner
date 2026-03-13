/**
 * components/Navbar.jsx
 * ----------------------
 * Top navigation bar — fixed, transparent with a blur backdrop.
 * Shows the tool logo and navigation links.
 */

import { Link, useLocation } from 'react-router-dom'

const NAV_LINKS = [
  { to: '/',          label: 'Home' },
  { to: '/dashboard', label: 'Scanner' },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav className="fixed top-0 inset-x-0 z-50 border-b border-border/50"
         style={{ background: 'rgba(5,11,20,0.85)', backdropFilter: 'blur(12px)' }}>
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          {/* Animated shield icon */}
          <div className="relative w-8 h-8">
            <svg viewBox="0 0 32 32" fill="none" className="w-full h-full">
              <path d="M16 2L4 7v9c0 7 5.5 12.5 12 14 6.5-1.5 12-7 12-14V7L16 2z"
                    fill="rgba(0,212,255,0.1)" stroke="#00d4ff" strokeWidth="1.5"/>
              <path d="M12 16l3 3 6-6" stroke="#00d4ff" strokeWidth="1.5"
                    strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {/* Pulse ring */}
            <span className="absolute inset-0 rounded-full border border-accent/30 animate-ping" />
          </div>
          <span className="font-display text-sm font-bold tracking-wider text-white group-hover:text-accent transition-colors">
            VULNSCAN<span className="text-accent">_AI</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ to, label }) => {
            const active = pathname === to
            return (
              <Link
                key={to}
                to={to}
                className={`px-4 py-1.5 rounded font-mono text-xs tracking-widest uppercase transition-all ${
                  active
                    ? 'text-accent bg-accent/10 border border-accent/30'
                    : 'text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                {label}
              </Link>
            )
          })}

          {/* Status indicator */}
          <div className="ml-4 flex items-center gap-2 text-xs font-mono text-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-low animate-pulse-dot" />
            <span>SYSTEM ONLINE</span>
          </div>
        </div>
      </div>

      {/* Bottom glow line */}
      <div className="accent-line opacity-40" />
    </nav>
  )
}
