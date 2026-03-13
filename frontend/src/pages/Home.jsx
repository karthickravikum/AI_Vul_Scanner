/**
 * pages/Home.jsx
 * ---------------
 * Landing page. Hero section explaining the tool with a CTA to
 * navigate to the scanner, plus a feature highlights section.
 */

import { useNavigate } from 'react-router-dom'

const FEATURES = [
  {
    icon: '🕷',
    title: 'Smart Crawler',
    desc: 'Automatically discovers internal endpoints, forms, and input surfaces.',
  },
  {
    icon: '⚡',
    title: 'OWASP Top 10',
    desc: 'Checks for SQL Injection, XSS, missing headers, path exposure, and more.',
  },
  {
    icon: '🤖',
    title: 'AI Risk Prediction',
    desc: 'Machine learning model predicts risk levels beyond rule-based detection.',
  },
  {
    icon: '📊',
    title: 'Visual Reports',
    desc: 'Interactive severity charts, filterable tables, and expandable findings.',
  },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <main className="noise-bg hex-grid relative min-h-screen pt-14 overflow-hidden">

      {/* Background glow blobs */}
      <div className="absolute top-32 left-1/4 w-96 h-96 rounded-full opacity-5 blur-3xl pointer-events-none"
           style={{ background: 'radial-gradient(circle, #00d4ff, transparent)' }} />
      <div className="absolute top-64 right-1/4 w-72 h-72 rounded-full opacity-5 blur-3xl pointer-events-none"
           style={{ background: 'radial-gradient(circle, #ff2d55, transparent)' }} />

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-24">

        {/* ─── Hero ─── */}
        <div className="text-center mb-20 animate-fade-in">
          {/* Pre-title */}
          <div className="inline-flex items-center gap-2 border border-accent/30 bg-accent/5
                          rounded-full px-4 py-1.5 mb-8">
            <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse-dot" />
            <span className="font-mono text-xs text-accent tracking-widest uppercase">
              AI-Powered Security Analysis
            </span>
          </div>

          {/* Main title */}
          <h1 className="font-display font-black text-4xl sm:text-6xl text-white
                         leading-tight mb-6">
            <span className="text-glow text-accent">WEB</span>{' '}
            VULNERABILITY{' '}
            <br className="hidden sm:block" />
            <span className="text-glow text-accent">SCANNER</span>
          </h1>

          <p className="text-lg text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
            Identify security vulnerabilities in any website using automated crawling,
            OWASP-aligned checks, and machine-learning risk prediction — all in one scan.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap justify-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-8 py-3.5 rounded-xl font-display text-sm font-bold
                         tracking-widest uppercase text-bg transition-all
                         hover:scale-105 active:scale-95"
              style={{
                background: 'linear-gradient(135deg, #00d4ff, #0099cc)',
                boxShadow: '0 0 30px rgba(0,212,255,0.4)',
              }}
            >
              Launch Scanner →
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-8 py-3.5 rounded-xl font-display text-sm font-bold
                         tracking-widest uppercase text-accent border border-accent/30
                         hover:bg-accent/10 transition-all"
            >
              View Demo
            </button>
          </div>
        </div>

        {/* ─── Divider ─── */}
        <div className="accent-line mb-20 opacity-30" />

        {/* ─── Feature cards ─── */}
        <div className="grid sm:grid-cols-2 gap-5">
          {FEATURES.map(({ icon, title, desc }, i) => (
            <div
              key={title}
              className="panel p-6 hover:border-accent/40 transition-all
                         hover:shadow-glow group animate-slide-up"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="text-3xl mb-3">{icon}</div>
              <h3 className="font-display text-sm font-bold text-white mb-2
                             group-hover:text-accent transition-colors">
                {title}
              </h3>
              <p className="text-sm text-muted leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* ─── Footer note ─── */}
        <p className="mt-16 text-center font-mono text-xs text-muted/40">
          FOR AUTHORISED SECURITY TESTING ONLY — USE RESPONSIBLY
        </p>
      </div>
    </main>
  )
}
