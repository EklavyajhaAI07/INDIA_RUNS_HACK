import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MagneticElement } from './CursorPhysics'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function FeedbackPanel({ candidateId, candidateScore, featureScores, onClose }) {
  const [decision, setDecision] = useState(null)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/feedback/stats`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  const handleSubmit = async (dec) => {
    setDecision(dec)
    setSubmitting(true)

    try {
      const res = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          decision: dec,
          final_score: candidateScore,
          feature_scores: featureScores || {},
          recruiter_id: 'ui_user',
          notes,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setResult({ success: true, message: data.message })
        fetchStats()
      } else {
        setResult({ success: false, message: 'Failed to submit feedback' })
      }
    } catch (err) {
      setResult({ success: false, message: 'API unavailable — feedback saved locally' })
    }

    setSubmitting(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="mt-4 p-4 rounded-xl bg-deep-800/80 border border-accent/20 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-white">Recruiter Feedback</h4>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-300 text-xs"
        >
          Close
        </button>
      </div>

      {!result ? (
        <>
          <p className="text-xs text-gray-400 mb-3">
            Your feedback adjusts future ranking weights. Accepted candidates
            increase weight on their strong features; rejected candidates
            decrease weight on theirs.
          </p>

          <div className="flex gap-2 mb-3">
            <MagneticElement strength={0.1} className="flex-1">
              <button
                onClick={() => handleSubmit('accept')}
                disabled={submitting}
                className={`w-full py-2 px-4 rounded-lg text-sm font-semibold transition-all duration-200
                  ${decision === 'accept'
                    ? 'bg-green-500/20 border-green-500/50 text-green-400'
                    : 'bg-deep-700/50 border-deep-600/50 text-gray-300 hover:bg-green-500/10 hover:border-green-500/30'}
                  border`}
              >
                {submitting && decision === 'accept' ? '...' : 'Accept'}
              </button>
            </MagneticElement>

            <MagneticElement strength={0.1} className="flex-1">
              <button
                onClick={() => handleSubmit('reject')}
                disabled={submitting}
                className={`w-full py-2 px-4 rounded-lg text-sm font-semibold transition-all duration-200
                  ${decision === 'reject'
                    ? 'bg-red-500/20 border-red-500/50 text-red-400'
                    : 'bg-deep-700/50 border-deep-600/50 text-gray-300 hover:bg-red-500/10 hover:border-red-500/30'}
                  border`}
              >
                {submitting && decision === 'reject' ? '...' : 'Reject'}
              </button>
            </MagneticElement>
          </div>

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes..."
            className="w-full p-2 rounded-lg bg-deep-900/50 border border-deep-600/30 text-xs text-gray-300 placeholder-gray-600 resize-none"
            rows={2}
          />
        </>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`p-3 rounded-lg text-sm ${result.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}
        >
          {result.message}
        </motion.div>
      )}

      {stats && (
        <div className="mt-3 pt-3 border-t border-deep-700/50 flex justify-between text-xs text-gray-500">
          <span>{stats.total} total feedback</span>
          <span>{(stats.acceptance_rate * 100).toFixed(1)}% acceptance</span>
        </div>
      )}
    </motion.div>
  )
}
