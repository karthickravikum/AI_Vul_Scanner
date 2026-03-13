/**
 * pages/Report.jsx
 * -----------------
 * Full report view loaded from /report/:id.
 * Fetches the report directly from the API using the scan_id URL param.
 * Renders ScanSummary, SeverityChart, VulnerabilityTable, and all cards.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getReport } from '../services/api'
import ScanSummary       from '../components/ScanSummary'
import SeverityChart     from '../components/SeverityChart'
import VulnerabilityCard from '../components/VulnerabilityCard'
import VulnerabilityTable from '../components/VulnerabilityTable'

export default function Report() {
  const { id }     = useParams()
  const navigate   = useNavigate()
  const [report,   setReport]  = useState(null)
  const [loading,  setLoading] = useState(true)
  const [error,    setError]   = useState('')

  useEffect(() => {
    let cancelled = false

    async function fetch() {
      try {
        const data = await getReport(id)
        if (!cancelled) setReport(data)
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.status === 404
              ? `No report found for scan ID: ${id}`
              : 'Failed to load report. Check the backend connection.'
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetch()
    return () => { cancelled = true }
  }, [id])

  /* ─── Loading ─── */
  if (loading) {
    return (
      <main className="hex-grid min-h-screen pt-14 flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="w-10 h-10 border-2 border-accent border-t-transparent
                          rounded-full animate-spin mx-auto mb-4" />
          <p className="font-mono text-sm text-muted">Loading report…</p>
        </div>
      </main>
    )
  }

  /* ─── Error ─── */
  if (error) {
    return (
      <main className="hex-grid min-h-screen pt-14 flex items-center justify-center px-6">
        <div className="panel p-8 max-w-md text-center border-critical/30 animate-fade-in">
          <div className="text-4xl mb-4">⚠</div>
          <p className="font-mono text-sm text-critical mb-6">{error}</p>
          <button onClick={() => navigate('/dashboard')}
                  className="font-mono text-xs text-accent border border-accent/30
                             px-5 py-2 rounded hover:bg-accent/10 transition-all">
            ← Back to Scanner
          </button>
        </div>
      </main>
    )
  }

  /* ─── Report ─── */
  return (
    <main className="hex-grid min-h-screen pt-14">
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4 animate-fade-in">
          <div>
            <p className="font-mono text-xs text-accent tracking-widest uppercase mb-1">
              // SCAN REPORT
            </p>
            <h1 className="font-display text-2xl font-bold text-white">
              {report.target}
            </h1>
            <p className="font-mono text-xs text-muted mt-1">
              ID: {report.scan_id}
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate('/dashboard')}
                    className="font-mono text-xs text-muted border border-border
                               px-4 py-2 rounded hover:text-white transition-all">
              ← New Scan
            </button>
            <button onClick={() => window.print()}
                    className="font-mono text-xs text-accent border border-accent/30
                               px-4 py-2 rounded hover:bg-accent/10 transition-all">
              Export Report
            </button>
          </div>
        </div>

        {/* Summary */}
        <ScanSummary report={report} />

        {/* Chart + table */}
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <SeverityChart vulnerabilities={report.vulnerabilities} />
          </div>
          <div className="lg:col-span-2">
            <VulnerabilityTable vulnerabilities={report.vulnerabilities} />
          </div>
        </div>

        {/* Detailed cards */}
        <div>
          <p className="font-mono text-xs text-accent tracking-widest uppercase mb-4">
            // DETAILED FINDINGS
          </p>
          {report.vulnerabilities.length === 0 ? (
            <div className="panel p-10 text-center">
              <div className="text-5xl mb-4">✓</div>
              <p className="font-display text-lg text-low font-bold mb-2">
                All Clear
              </p>
              <p className="font-mono text-sm text-muted">
                No vulnerabilities were detected during this scan.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {report.vulnerabilities.map((v, i) => (
                <VulnerabilityCard key={i} vuln={v} index={i} />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="accent-line opacity-20" />
        <p className="font-mono text-xs text-muted/40 text-center pb-6">
          GENERATED BY VULNSCAN_AI · FOR AUTHORISED SECURITY TESTING ONLY
        </p>
      </div>
    </main>
  )
}
