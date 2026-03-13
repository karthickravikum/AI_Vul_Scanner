/**
 * components/ScanSummary.jsx
 * ---------------------------
 * Stat cards shown at the top of the results section.
 * Displays target, endpoint count, vulnerability count, and scan time.
 */

export default function ScanSummary({ report }) {
  const {
    target,
    scan_timestamp,
    total_endpoints_scanned,
    vulnerabilities = [],
  } = report

  // Count by severity
  const counts = vulnerabilities.reduce((acc, v) => {
    const s = v.severity?.toLowerCase()
    acc[s] = (acc[s] || 0) + 1
    return acc
  }, {})

  // Format timestamp
  const scanTime = scan_timestamp
    ? new Date(scan_timestamp).toLocaleString()
    : '—'

  const stats = [
    {
      label: 'Target',
      value: target,
      icon: '🎯',
      mono: true,
    },
    {
      label: 'Endpoints Scanned',
      value: total_endpoints_scanned,
      icon: '🔍',
    },
    {
      label: 'Vulnerabilities',
      value: vulnerabilities.length,
      icon: '⚠',
      highlight: vulnerabilities.length > 0 ? 'critical' : 'low',
    },
    {
      label: 'Scan Completed',
      value: scanTime,
      icon: '🕐',
      small: true,
    },
  ]

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Title row */}
      <div className="flex items-center justify-between">
        <p className="font-mono text-xs text-accent tracking-widest uppercase">
          // SCAN SUMMARY
        </p>
        <span className="badge bg-low/10 text-low border border-low/30">
          ✓ Complete
        </span>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map(({ label, value, icon, mono, highlight, small }) => (
          <div key={label} className="panel p-4">
            <p className="font-mono text-xs text-muted uppercase tracking-wider mb-2">
              {icon} {label}
            </p>
            <p className={`font-display font-bold truncate ${
              small ? 'text-xs text-muted' :
              highlight === 'critical' ? 'text-2xl text-critical' :
              highlight === 'low' ? 'text-2xl text-low' :
              mono ? 'text-sm font-mono text-accent' :
              'text-2xl text-white'
            }`}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Severity breakdown bar */}
      {vulnerabilities.length > 0 && (
        <div className="panel p-4">
          <p className="font-mono text-xs text-muted uppercase tracking-wider mb-3">
            Severity Breakdown
          </p>
          <div className="flex gap-4 flex-wrap">
            {[
              { key: 'critical', label: 'Critical', color: 'text-critical' },
              { key: 'high',     label: 'High',     color: 'text-high' },
              { key: 'medium',   label: 'Medium',   color: 'text-medium' },
              { key: 'low',      label: 'Low',      color: 'text-low' },
            ].map(({ key, label, color }) => (
              counts[key] ? (
                <div key={key} className="flex items-center gap-2">
                  <span className={`font-display text-lg font-bold ${color}`}>
                    {counts[key]}
                  </span>
                  <span className="font-mono text-xs text-muted uppercase">{label}</span>
                </div>
              ) : null
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
