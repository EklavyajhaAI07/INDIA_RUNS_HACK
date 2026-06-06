import { motion } from 'framer-motion'
import { useEffect, useRef } from 'react'
import gsap from 'gsap'

const failureCases = [
  {
    title: "Sparse Profiles",
    desc: "Candidates with minimal career descriptions or few listed skills",
    impact: "Low behavioral_fit and bonus_fit scores even for qualified candidates",
    example: "A strong candidate with only 2 skills listed may rank below a weaker candidate with 15 skills listed"
  },
  {
    title: "Title Mismatch",
    desc: "Experienced candidates with non-standard titles (e.g., 'Research Scientist' vs. 'ML Engineer')",
    impact: "Low role_fit penalizes candidates who are qualified but use different terminology",
    example: "A PhD researcher with 10 years of NLP experience might rank lower due to title mismatch"
  },
  {
    title: "Experience Boundary Effects",
    desc: "Candidates just outside the preferred experience range receive disproportionate penalties",
    impact: "A candidate with 4.8 years when 5 years is required gets penalized more than necessary",
    example: "Near-qualifying candidates may fall to rank 50+ despite strong skill matches"
  },
  {
    title: "Keyword Over-Indexing",
    desc: "BM25 retrieval can favor candidates who repeat exact keywords",
    impact: "Candidates with natural language descriptions may be outranked by keyword-stuffed profiles",
    example: "A profile mentioning 'Python' 10 times may rank higher than one mentioning it once with deeper context"
  },
  {
    title: "Static Weights",
    desc: "Current weights are fixed and do not adapt to recruiter preferences",
    impact: "Different recruiters may prioritize different factors (e.g., recency vs. experience)",
    example: "A startup recruiter may weight recency higher than an enterprise recruiter"
  }
]

const futureImprovements = [
  {
    title: "Recruiter Feedback Loop",
    desc: "Accept/reject signals from recruiters adjust feature weights over time",
    impl: "Exponential moving average on accepted candidate feature vectors",
    benefit: "System learns per-recruiter preferences automatically"
  },
  {
    title: "Cross-Encoder Reranking",
    desc: "Replace heuristic scoring with a trained cross-encoder for top 200 candidates",
    impl: "Fine-tune a small transformer on recruiter decisions",
    benefit: "Captures non-linear interactions between features"
  },
  {
    title: "Dynamic Weight Adaptation",
    desc: "Allow weights to shift based on JD context (e.g., startup vs. enterprise roles)",
    impl: "Rule-based weight presets + feedback refinement",
    benefit: "More context-aware rankings out of the box"
  },
  {
    title: "Profile Completeness Scoring",
    desc: "Penalize candidates with incomplete profiles more explicitly",
    impl: "Add a profile_completeness feature (education, skills count, summary length)",
    benefit: "Rewards candidates who invest in their profiles"
  },
  {
    title: "Diversity-Aware Ranking",
    desc: "Introduce diversity constraints to avoid homogeneous shortlists",
    impl: "MMR (Maximal Marginal Relevance) or similar diversity scoring",
    benefit: "More balanced candidate pools for recruiters"
  },
  {
    title: "Real-Time Embedding Updates",
    desc: "Refresh embeddings as new candidates join the platform",
    impl: "Incremental FAISS index updates",
    benefit: "Always-fresh rankings without full reindexing"
  },
  {
    title: "Explainability Enhancements",
    desc: "Add 'Why not ranked higher?' explanations for candidates just below the cutoff",
    impl: "Contrastive explanations comparing to higher-ranked candidates",
    benefit: "Helps recruiters understand borderline decisions"
  }
]

export default function FailureCasesModal({ onClose }) {
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
    >
      <div ref={modalRef}
           className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl bg-gradient-to-b from-deep-800 to-deep-900
                       border border-accent/20 shadow-2xl shadow-accent/10"
           onClick={(e) => e.stopPropagation()}>

        <div className="sticky top-0 z-10 bg-gradient-to-b from-deep-800 to-transparent pb-4">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent via-accent-light to-accent rounded-t-2xl" />
          <div className="flex items-start justify-between p-6 pb-2">
            <h2 className="text-2xl font-bold text-white">Failure Cases & Future Improvements</h2>
            <button
              onClick={onClose}
              aria-label="Close modal"
              className="w-8 h-8 rounded-full bg-deep-700/50 text-gray-400 hover:text-white
                         hover:bg-deep-700 transition-all flex items-center justify-center shrink-0">
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 pt-0 space-y-10">

          {/* Failure Cases */}
          <section>
            <h3 className="text-lg font-bold text-red-400 mb-4 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
              Current Failure Cases
            </h3>
            <div className="space-y-3">
              {failureCases.map((fc, i) => (
                <div key={i} className="p-4 rounded-xl bg-deep-700/30 border border-red-500/10 hover:border-red-500/20 transition-colors">
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-mono text-red-400/60 mt-0.5 shrink-0">0{i + 1}</span>
                    <div>
                      <h4 className="font-semibold text-gray-200">{fc.title}</h4>
                      <p className="text-sm text-gray-400 mt-1">{fc.desc}</p>
                      <p className="text-xs text-red-400/70 mt-2">
                        <span className="font-medium">Impact:</span> {fc.impact}
                      </p>
                      <p className="text-xs text-gray-500 mt-1 italic">
                        <span className="font-medium text-gray-500 not-italic">Example:</span> {fc.example}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Future Improvements */}
          <section>
            <h3 className="text-lg font-bold text-green-400 mb-4 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              Future Improvements
            </h3>
            <div className="space-y-3">
              {futureImprovements.map((fi, i) => (
                <div key={i} className="p-4 rounded-xl bg-deep-700/30 border border-green-500/10 hover:border-green-500/20 transition-colors">
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-mono text-green-400/60 mt-0.5 shrink-0">0{i + 1}</span>
                    <div>
                      <h4 className="font-semibold text-gray-200">{fi.title}</h4>
                      <p className="text-sm text-gray-400 mt-1">{fi.desc}</p>
                      <p className="text-xs text-green-400/70 mt-2">
                        <span className="font-medium">Implementation:</span> {fi.impl}
                      </p>
                      <p className="text-xs text-gray-500 mt-1 italic">
                        <span className="font-medium text-gray-500 not-italic">Benefit:</span> {fi.benefit}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

        </div>

        {/* Close button */}
        <div className="sticky bottom-0 p-6 pt-0 bg-gradient-to-t from-deep-900 via-deep-900/95 to-transparent">
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
