/**
 * components/ScanForm.jsx
 * ------------------------
 * URL input form. Validates the URL client-side before
 * calling the onScan callback provided by the parent page.
 */

import { useState } from 'react'

export default function ScanForm({ onScan, isScanning }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  function validate(value) {
    try {
      const u = new URL(value)
      return u.protocol === 'http:' || u.protocol === 'https:'
    } catch {
      return false
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = url.trim()

    if (!trimmed) {
      setError('Please enter a URL.')
      return
    }
    if (!validate(trimmed)) {
      setError('Enter a valid URL starting with http:// or https://')
      return
    }

    setError('')
    onScan(trimmed)
  }

  return (
    <div className="panel p-6 scan-border">
      {/* Header */}
      <div className="mb-5">
        <p className="font-mono text-xs text-accent tracking-widest uppercase mb-1">
          // TARGET ACQUISITION
        </p>
        <h2 className="font-display text-lg font-bold text-white">
          Enter Target URL
        </h2>
        <p className="text-muted text-sm mt-1">
          Provide the website you want to analyse for vulnerabilities.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* URL input row */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            {/* Protocol label */}
            <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-xs text-muted pointer-events-none select-none">
              &gt;
            </span>
            <input
              type="text"
              value={url}
              onChange={e => { setUrl(e.target.value); setError('') }}
              placeholder="https://target-website.com"
              disabled={isScanning}
              className="w-full bg-surface border border-border rounded-lg pl-7 pr-4 py-3
                         font-mono text-sm text-white placeholder-muted/50
                         focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={isScanning}
            className="relative px-7 py-3 rounded-lg font-display text-xs font-bold
                       tracking-widest uppercase text-bg overflow-hidden
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: 'linear-gradient(135deg, #00d4ff, #0099cc)',
              boxShadow: '0 0 20px rgba(0,212,255,0.3)',
            }}
          >
            {isScanning ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-bg/50 border-t-bg rounded-full animate-spin" />
                Scanning...
              </span>
            ) : (
              'Initiate Scan'
            )}
          </button>
        </div>

        {/* Error message */}
        {error && (
          <p className="font-mono text-xs text-critical flex items-center gap-2">
            <span>⚠</span> {error}
          </p>
        )}

        {/* Helper text */}
        <p className="font-mono text-xs text-muted/60">
          Scans check for OWASP Top 10 vulnerabilities using AI-assisted risk prediction.
        </p>
      </form>
    </div>
  )
}
