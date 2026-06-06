import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import ScoreBar from './ScoreBar'
import gsap from 'gsap'

export default function CandidateRow({ candidate, rank, onClick }) {
  const rowRef = useRef(null)
  const tweenRef = useRef(null)
  const [isHovered, setIsHovered] = useState(false)

  useEffect(() => {
    tweenRef.current = gsap.fromTo(rowRef.current,
      { x: -60, opacity: 0, rotateX: 15 },
      { x: 0, opacity: 1, rotateX: 0, duration: 0.5, ease: 'power3.out', delay: rank * 0.03 }
    )

    return () => {
      if (tweenRef.current) tweenRef.current.kill()
    }
  }, [rank])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick?.(candidate)
    }
  }

  const getRankClasses = (r) => {
    if (r === 1) return 'border-gold/30 bg-gold/5'
    if (r === 2) return 'border-silver/30 bg-silver/5'
    if (r === 3) return 'border-bronze/30 bg-bronze/5'
    return 'border-deep-700/50 bg-deep-800/40'
  }

  const getRankText = (r) => {
    if (r <= 3) return 'font-bold'
    return 'font-mono'
  }

  return (
    <motion.tr
      ref={rowRef}
      className={`cursor-pointer transition-all duration-300 border-l-2 ${getRankClasses(rank)} backdrop-blur-sm
                  ${isHovered ? 'bg-accent/5 scale-[1.01] shadow-lg shadow-accent/10' : 'hover:bg-deep-700/30'}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onClick?.(candidate)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`View details for candidate ${candidate.candidate_id}, ranked ${rank}`}
      layout
    >
      <td className="py-3 px-4 text-center">
        <motion.span
          className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm ${getRankText(rank)}
                      ${rank === 1 ? 'bg-gold/20 text-gold' :
                        rank === 2 ? 'bg-silver/20 text-silver' :
                        rank === 3 ? 'bg-bronze/20 text-bronze' :
                        'bg-deep-700/50 text-gray-400'}`}
          whileHover={{ scale: 1.2 }}
          aria-hidden="true"
        >
          {rank}
        </motion.span>
      </td>

      <td className="py-3 px-2">
        <span className="font-mono text-xs text-gray-500">{candidate.candidate_id}</span>
      </td>

      <td className="py-3 px-4 min-w-[300px]">
        <p className="text-sm text-gray-200 leading-snug line-clamp-2">
          {candidate.reasoning}
        </p>
      </td>

      <td className="py-3 px-4 min-w-[180px]">
        <ScoreBar score={candidate.score} rank={rank} />
      </td>
    </motion.tr>
  )
}
