import { motion } from 'framer-motion'
import { useEffect, useRef } from 'react'
import gsap from 'gsap'

export default function CandidateModal({ candidate, onClose }) {
  const overlayRef = useRef(null)
  const modalRef = useRef(null)

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
           className="relative w-full max-w-lg rounded-2xl bg-gradient-to-b from-deep-800 to-deep-900
                      border border-accent/20 shadow-2xl shadow-accent/10 overflow-hidden"
           onClick={(e) => e.stopPropagation()}>

        {/* Glow top bar */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent via-accent-light to-accent" aria-hidden="true" />

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

          {/* Reasoning */}
          <div className="mb-5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Reasoning</h4>
            <p className="text-sm text-gray-200 leading-relaxed">
              {candidate.reasoning}
            </p>
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-xl bg-accent/20 text-accent-light border border-accent/30
                       hover:bg-accent/30 transition-all text-sm font-medium">
            Close
          </button>
        </div>
      </div>
    </motion.div>
  )
}
