import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import FeedbackPanel from './FeedbackPanel'

export default function CandidateModal({ candidate, onClose }) {
  const overlayRef = useRef(null)
  const modalRef = useRef(null)
  const [showFeedback, setShowFeedback] = useState(false)

  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handleEsc)

    gsap.fromTo(overlayRef.current,
      { opacity: 0 },
      { opacity: 1, duration: 0.3 }
    )
    gsap.fromTo(modalRef.current,
      { scale: 0.8, opacity: 0, y: 40 },
      { scale: 1, opacity: 1, y: 0, duration: 0.4, ease: 'back.out(1.7)' }
    )

    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const scoreNum = parseFloat(candidate.score)

  // Parse breakdown scores from candidate data
  const parseBreakdown = () => {
    if (candidate.breakdown_scores) {
      const pairs = candidate.breakdown_scores.split(', ')
      const result = {}
      for (const pair of pairs) {
        const [key, val] = pair.split('=')
        result[key] = parseFloat(val)
      }
      return result
    }
    return {}
  }

  const breakdown = parseBreakdown()
  const featureScores = {
    semantic_fit: breakdown.semantic_fit || 0.5,
    must_have_coverage: breakdown.must_have_coverage || 0.5,
    experience_fit: breakdown.experience_fit || 0.5,
    role_fit: breakdown.role_fit || 0.5,
    recency: breakdown.recency || 0.5,
    behavioral_fit: breakdown.behavioral_fit || 0.5,
    bonus_fit: breakdown.bonus_fit || 0.5,
  }

  return (
    <motion.div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby={`modal-title-${candidate.candidate_id}`}
    >
      <div ref={modalRef}
           className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-gradient-to-b from-deep-800 to-deep-900
                      border border-accent/20 shadow-2xl shadow-accent/10"
           onClick={(e) => e.stopPropagation()}>

        {/* Glow top bar */}
        <div className="sticky top-0 z-10">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent via-accent-light to-accent rounded-t-2xl" aria-hidden="true" />
        </div>

        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 id={`modal-title-${candidate.candidate_id}`} className="text-xl font-bold text-white">
                Rank #{candidate.rank}
              </h3>
              <p className="font-mono text-sm text-accent-light mt-0.5">{candidate.candidate_id}</p>
            </div>
            <button
              onClick={onClose}
              aria-label="Close modal"
              className="w-8 h-8 rounded-full bg-deep-700/50 text-gray-400 hover:text-white
                         hover:bg-deep-700 transition-all flex items-center justify-center">
              ✕
            </button>
          </div>

          {/* Score display */}
          <div className="mb-5 p-4 rounded-xl bg-deep-700/30 border border-accent/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Final Score</span>
              <span className="text-2xl font-bold text-accent-light font-mono">{candidate.score}</span>
            </div>
            <div className="h-2 bg-deep-700/50 rounded-full overflow-hidden" role="progressbar" aria-valuenow={scoreNum * 100} aria-valuemin={0} aria-valuemax={100} aria-label={`Score: ${(scoreNum * 100).toFixed(1)}%`}>
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-accent to-accent-light"
                initial={{ width: 0 }}
                animate={{ width: `${(scoreNum * 100).toFixed(1)}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
                style={{ boxShadow: '0 0 12px rgba(108,92,231,0.4)' }}
              />
            </div>
          </div>

          {/* Breakdown Scores */}
          {Object.keys(breakdown).length > 0 && (
            <div className="mb-5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Score Breakdown</h4>
              <div className="space-y-2">
                {Object.entries(breakdown).map(([key, val]) => (
                  <div key={key} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-32 shrink-0">{key.replace(/_/g, ' ')}</span>
                    <div className="flex-1 h-1.5 bg-deep-700/50 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-accent/70 to-accent-light/70"
                        initial={{ width: 0 }}
                        animate={{ width: `${val * 100}%` }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                      />
                    </div>
                    <span className="text-xs font-mono text-gray-300 w-10 text-right">{(val * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Matched Skills */}
          {candidate.top_matched_skills && (
            <div className="mb-5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Matched Skills</h4>
              <div className="flex flex-wrap gap-1.5">
                {candidate.top_matched_skills.split(', ').map((skill, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing Must-Haves */}
          {candidate.missing_must_haves && (
            <div className="mb-5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Missing Must-Haves</h4>
              <div className="flex flex-wrap gap-1.5">
                {candidate.missing_must_haves.split(', ').map((skill, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Reasoning */}
          <div className="mb-5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Reasoning</h4>
            <p className="text-sm text-gray-200 leading-relaxed">
              {candidate.reasoning}
            </p>
          </div>

          {/* Feedback Toggle */}
          <button
            onClick={() => setShowFeedback(!showFeedback)}
            className="w-full py-2.5 rounded-xl border text-sm font-medium transition-all
              ${showFeedback
                ? 'bg-accent/20 text-accent-light border-accent/30'
                : 'bg-deep-700/30 text-gray-400 border-deep-600/30 hover:bg-deep-700/50 hover:text-gray-300'}"
          >
            {showFeedback ? 'Hide Feedback Panel' : 'Give Feedback'}
          </button>

          {/* Feedback Panel */}
          <AnimatePresence>
            {showFeedback && (
              <FeedbackPanel
                candidateId={candidate.candidate_id}
                candidateScore={scoreNum}
                featureScores={featureScores}
                onClose={() => setShowFeedback(false)}
              />
            )}
          </AnimatePresence>

          {/* Close button */}
          <button
            onClick={onClose}
            className="mt-3 w-full py-2.5 rounded-xl bg-accent/20 text-accent-light border border-accent/30
                       hover:bg-accent/30 transition-all text-sm font-medium">
            Close
          </button>
        </div>
      </div>
    </motion.div>
  )
}
