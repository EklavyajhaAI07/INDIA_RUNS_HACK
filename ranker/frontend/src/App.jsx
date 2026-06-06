import { Suspense, lazy, useState } from 'react'
import ThreeBackground from './components/ThreeBackground'
import CursorPhysics from './components/CursorPhysics'
import Header from './components/Header'
import CandidateTable from './components/CandidateTable'
import FailureCasesModal from './components/FailureCasesModal'
import candidates from './data/candidates.json'

function App() {
  const topScore = candidates.length > 0 ? parseFloat(candidates[0].score) : 0
  const [showFailureCases, setShowFailureCases] = useState(false)

  return (
    <div className="min-h-screen relative">
      <CursorPhysics />
      <ThreeBackground />
      <main id="main-content" className="relative z-10">
        <Header candidateCount={candidates.length} topScore={topScore} />
        <CandidateTable candidates={candidates} />
        <footer className="text-center py-8 text-gray-500 text-sm">
          <p>Redrob AI — Candidate Intelligence Dashboard</p>
          <p className="mt-1 text-xs text-gray-600">
            Powered by BM25 + Semantic Retrieval + Weighted Scoring Engine
          </p>
          <button
            onClick={() => setShowFailureCases(true)}
            className="mt-4 px-4 py-2 rounded-xl bg-deep-700/30 border border-accent/20 text-xs text-accent-light
                       hover:bg-accent/10 hover:border-accent/30 transition-all"
          >
            Failure Cases &amp; Future Improvements
          </button>
        </footer>
      </main>

      {showFailureCases && (
        <FailureCasesModal onClose={() => setShowFailureCases(false)} />
      )}
    </div>
  )
}

export default App
