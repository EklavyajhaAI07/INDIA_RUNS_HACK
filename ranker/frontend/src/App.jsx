import { Suspense, lazy } from 'react'
import ThreeBackground from './components/ThreeBackground'
import Header from './components/Header'
import CandidateTable from './components/CandidateTable'
import candidates from './data/candidates.json'

function App() {
  const topScore = candidates.length > 0 ? parseFloat(candidates[0].score) : 0

  return (
    <div className="min-h-screen relative">
      <ThreeBackground />
      <main id="main-content" className="relative z-10">
        <Header candidateCount={candidates.length} topScore={topScore} />
        <CandidateTable candidates={candidates} />
        <footer className="text-center py-8 text-gray-500 text-sm">
          <p>Redrob AI — Candidate Intelligence Dashboard</p>
          <p className="mt-1 text-xs text-gray-600">
            Powered by BM25 + Semantic Retrieval + Weighted Scoring Engine
          </p>
        </footer>
      </main>
    </div>
  )
}

export default App
