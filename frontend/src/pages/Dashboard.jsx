/**
 * pages/Dashboard.jsx
 * --------------------
 * Main scanning interface.
 *
 * State machine:
 *   idle     → user sees ScanForm
 *   scanning → ScanProgress shown, API call in flight
 *   done     → ScanSummary + SeverityChart + cards
 *   error    → error banner, reset to idle
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { startScan, getReport } from '../services/api'
import ScanForm         from '../components/ScanForm'
import ScanProgress     from '../components/ScanProgress'
import ScanSummary      from '../components/ScanSummary'
import SeverityChart    from '../components/SeverityChart'
import VulnerabilityCard from '../components/VulnerabilityCard'
import VulnerabilityTable from '../components/VulnerabilityTable'

export default function Dashboard() {
  const navigate = useNavigate()

  const [phase,   setPhase]   = useState('idle')     // idle | scanning | done | error
  const [target,  setTarget]  = useState('')
  const [scanId,  setScanId]  = useState(null)
  const [report,  setReport]  = useState(null)
  const [errMsg,  setErrMsg]  = useState('')

  async function handleScan(url) {
    setTarget(url)
    setPhase('scanning')
    setReport(null)
    setErrMsg('')

    try {
      // Step 1 — kick off scan, get scan_id back
      const summary = await startScan(url)
      setScanId(summary.scan_id)

      // Step 2 — fetch full report
      const fullReport = await getReport(summary.scan_id)
      setReport(fullReport)
      setPhase('done')
    } catch (err) {
      const msg = err.response?.data?.error
        || err.message
        || 'Scan failed. Make sure the backend is running.'
      setErrMsg(msg)
      setPhase('error')
    }
  }

  function reset() {
    setPhase('idle')
    setTarget('')
    setScanId(null)
    setReport(null)
    setErrMsg('')
  }

  return (
    <main className="hex-grid min-h-screen pt-14">
      <div className="max-w-7xl mx-auto px-6 py-10">

        {/* ─── Page header ─── */}
        <div className="mb-8 animate-fade-in">
          <p className="font-mono text-xs text-accent tracking-widest uppercase mb-1">
            // SCANNER INTERFACE
          </p>
          <h1 className="font-display text-2xl font-bold text-white">
            Vulnerability Scanner
          </h1>
        </div>

        {/* ─── IDLE: scan form ─── */}
        {phase === 'idle' && (
          <div className="max-w-3xl animate-slide-up">
            <ScanForm onScan={handleScan} isScanning={false} />
          </div>
        )}

        {/* ─── SCANNING: progress panel ─── */}
        {phase === 'scanning' && (
          <div className="max-w-3xl">
            <ScanForm onScan={handleScan} isScanning={true} />
            <div className="mt-6">
              <ScanProgress target={target} />
            </div>
          </div>
        )}

        {/* ─── ERROR ─── */}
        {phase === 'error' && (
          <div className="max-w-3xl animate-fade-in">
            <div className="panel p-6 border-critical/40 bg-critical/5">
              <p className="font-mono text-xs text-critical uppercase tracking-wider mb-2">
                ⚠ SCAN ERROR
              </p>
              <p className="text-white mb-4">{errMsg}</p>
              <button onClick={reset}
                      className="font-mono text-xs text-accent border border-accent/30
                                 px-4 py-2 rounded hover:bg-accent/10 transition-all">
                ← Try Again
              </button>
            </div>
          </div>
        )}

        {/* ─── DONE: results ─── */}
        {phase === 'done' && report && (
          <div className="space-y-6 animate-fade-in">

            {/* Top action bar */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <button onClick={reset}
                      className="font-mono text-xs text-muted border border-border
                                 px-4 py-2 rounded hover:text-white hover:border-border/80
                                 transition-all">
                ← New Scan
              </button>
              <button
                onClick={() => navigate(`/report/${report.scan_id}`)}
                className="font-mono text-xs text-accent border border-accent/30
                           px-4 py-2 rounded hover:bg-accent/10 transition-all">
                Open Full Report →
              </button>
            </div>

            {/* Summary stats */}
            <ScanSummary report={report} />

            {/* Chart + cards side-by-side on large screens */}
            <div className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <SeverityChart vulnerabilities={report.vulnerabilities} />
              </div>

              <div className="lg:col-span-2 space-y-3">
                <p className="font-mono text-xs text-accent tracking-widest uppercase">
                  // FINDINGS
                </p>
                {report.vulnerabilities.length === 0 ? (
                  <div className="panel p-8 text-center">
                    <div className="text-4xl mb-3">✓</div>
                    <p className="font-mono text-sm text-low">
                      No vulnerabilities detected on scanned endpoints.
                    </p>
                  </div>
                ) : (
                  report.vulnerabilities.map((v, i) => (
                    <VulnerabilityCard key={i} vuln={v} index={i} />
                  ))
                )}
              </div>
            </div>

            {/* Full table */}
            <VulnerabilityTable vulnerabilities={report.vulnerabilities} />
          </div>
        )}
      </div>
    </main>
  )
}
