/**
 * components/SeverityChart.jsx
 * -----------------------------
 * Doughnut chart showing the distribution of vulnerability severities.
 * Uses Chart.js via react-chartjs-2.
 */

import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Doughnut } from 'react-chartjs-2'

ChartJS.register(ArcElement, Tooltip, Legend)

// Severity → hex colour mapping
const COLORS = {
  critical: '#ff2d55',
  high:     '#ff6b2b',
  medium:   '#ffd60a',
  low:      '#30d158',
}

export default function SeverityChart({ vulnerabilities = [] }) {
  // Count severities (case-insensitive)
  const counts = vulnerabilities.reduce((acc, v) => {
    const key = v.severity?.toLowerCase() || 'low'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})

  const labels   = Object.keys(counts).map(k => k.charAt(0).toUpperCase() + k.slice(1))
  const values   = Object.values(counts)
  const colours  = Object.keys(counts).map(k => COLORS[k] || '#4a6b8a')
  const glows    = colours.map(c => c + '88')

  const data = {
    labels,
    datasets: [{
      data: values,
      backgroundColor:   glows,
      borderColor:       colours,
      borderWidth:       2,
      hoverBorderColor:  colours,
      hoverBorderWidth:  3,
      hoverBackgroundColor: colours.map(c => c + 'bb'),
    }],
  }

  const options = {
    cutout: '72%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#4a6b8a',
          font: { family: "'Share Tech Mono'", size: 11 },
          boxWidth: 10,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: '#0d1f38',
        borderColor: '#1a3a5c',
        borderWidth: 1,
        titleColor: '#00d4ff',
        bodyColor: '#e2ecf4',
        titleFont: { family: "'Share Tech Mono'", size: 12 },
        bodyFont:  { family: "'DM Sans'", size: 13 },
        callbacks: {
          label: ctx => ` ${ctx.parsed} finding${ctx.parsed !== 1 ? 's' : ''}`,
        },
      },
    },
    animation: { animateRotate: true, duration: 800 },
  }

  if (vulnerabilities.length === 0) {
    return (
      <div className="panel p-6 flex flex-col items-center justify-center min-h-48">
        <p className="font-mono text-xs text-accent tracking-widest uppercase mb-4">
          // SEVERITY DISTRIBUTION
        </p>
        <div className="text-4xl mb-3">✓</div>
        <p className="font-mono text-sm text-low">No vulnerabilities detected</p>
      </div>
    )
  }

  return (
    <div className="panel p-6 animate-fade-in">
      <p className="font-mono text-xs text-accent tracking-widest uppercase mb-5">
        // SEVERITY DISTRIBUTION
      </p>

      {/* Chart */}
      <div className="relative max-w-xs mx-auto">
        <Doughnut data={data} options={options} />
        {/* Centre label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="font-display text-3xl font-bold text-white">
            {vulnerabilities.length}
          </span>
          <span className="font-mono text-xs text-muted uppercase tracking-wider">
            Total
          </span>
        </div>
      </div>

      {/* Legend breakdown */}
      <div className="mt-5 grid grid-cols-2 gap-2">
        {Object.entries(counts).map(([key, count]) => (
          <div key={key}
               className="flex items-center justify-between bg-surface rounded-lg px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: COLORS[key] || '#4a6b8a' }} />
              <span className="font-mono text-xs text-muted uppercase">{key}</span>
            </div>
            <span className="font-display text-sm font-bold"
                  style={{ color: COLORS[key] || '#4a6b8a' }}>
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
