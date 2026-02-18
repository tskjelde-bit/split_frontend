import type { Config } from 'tailwindcss';

export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        hero: ['Montserrat', 'sans-serif'],
      },
      colors: {
        base: 'var(--bg-base)',
        surface: 'var(--bg-surface)',
        elevated: 'var(--bg-elevated)',
        overlay: 'var(--bg-overlay)',
        'tx-primary': 'var(--text-primary)',
        'tx-muted': 'var(--text-muted)',
        'tx-dim': 'var(--text-dim)',
        accent: { DEFAULT: 'var(--accent)', hover: 'var(--accent-hover)', subtle: 'var(--accent-subtle)' },
        positive: 'var(--color-positive)',
        warning: 'var(--color-warning)',
        negative: 'var(--color-negative)',
        neutral: 'var(--color-neutral)',
        'br-subtle': 'var(--border-subtle)',
        'br-default': 'var(--border-default)',
      },
    },
  },
  plugins: [],
} satisfies Config;
