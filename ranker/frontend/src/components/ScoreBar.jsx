import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

export default function ScoreBar({ score, rank }) {
  const percentage = (parseFloat(score) * 100).toFixed(1)

  const getBarColor = (s) => {
    if (s > 0.8) return 'from-emerald-400 via-emerald-500 to-emerald-600'
    if (s > 0.7) return 'from-accent-light via-accent to-purple-700'
    if (s > 0.6) return 'from-blue-400 via-blue-500 to-blue-700'
    if (s > 0.5) return 'from-amber-400 via-amber-500 to-amber-700'
    return 'from-gray-400 via-gray-500 to-gray-700'
  }

  const getRankBadge = (r) => {
    if (r === 1) return { icon: '🥇', label: 'Gold', glow: '#fbbf24' }
    if (r === 2) return { icon: '🥈', label: 'Silver', glow: '#9ca3af' }
    if (r === 3) return { icon: '🥉', label: 'Bronze', glow: '#d97706' }
    return null
  }

  const badge = getRankBadge(rank)

  return (
    <div className="flex items-center gap-3 w-full" role="meter" aria-valuenow={parseFloat(score) * 100} aria-valuemin={0} aria-valuemax={100} aria-label={`Score: ${score}`}>
      {badge && (
        <motion.span
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 10, delay: rank * 0.05 }}
          className="text-xl"
          style={{ filter: `drop-shadow(0 0 6px ${badge.glow})` }}
          aria-hidden="true"
        >
          {badge.icon}
        </motion.span>
      )}

      <div className="flex-1 h-3 bg-deep-700/50 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${getBarColor(score)}`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: rank * 0.03 }}
          style={{ boxShadow: `0 0 8px ${badge ? badge.glow : 'rgba(108,92,231,0.3)'}` }}
        />
      </div>

      <motion.span
        className="text-sm font-mono font-semibold min-w-[52px] text-right"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 + rank * 0.03 }}
        style={{ color: badge ? badge.glow : '#a29bfe' }}
      >
        {score}
      </motion.span>
    </div>
  )
}
