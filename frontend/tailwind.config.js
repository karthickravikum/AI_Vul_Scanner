/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"Share Tech Mono"', 'monospace'],
        display: ['"Orbitron"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        bg:       '#050b14',
        surface:  '#0a1628',
        panel:    '#0d1f38',
        border:   '#1a3a5c',
        accent:   '#00d4ff',
        glow:     '#0099cc',
        critical: '#ff2d55',
        high:     '#ff6b2b',
        medium:   '#ffd60a',
        low:      '#30d158',
        muted:    '#4a6b8a',
      },
      boxShadow: {
        glow:     '0 0 20px rgba(0,212,255,0.15)',
        critical: '0 0 12px rgba(255,45,85,0.4)',
        high:     '0 0 12px rgba(255,107,43,0.4)',
      },
      animation: {
        'scan-line': 'scanLine 2s linear infinite',
        'pulse-dot': 'pulseDot 1.5s ease-in-out infinite',
        'fade-in':   'fadeIn 0.4s ease forwards',
        'slide-up':  'slideUp 0.4s ease forwards',
      },
      keyframes: {
        scanLine: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(400%)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: 1, transform: 'scale(1)' },
          '50%':      { opacity: 0.3, transform: 'scale(0.8)' },
        },
        fadeIn: {
          from: { opacity: 0 },
          to:   { opacity: 1 },
        },
        slideUp: {
          from: { opacity: 0, transform: 'translateY(16px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
