import { useRef, useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import gsap from 'gsap'
import CandidateRow from './CandidateRow'
import CandidateModal from './CandidateModal'

function useDebounce(value, delay = 200) {
  const [debouncedValue, setDebouncedValue] = useState(value)
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
}

export default function CandidateTable({ candidates }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortConfig, setSortConfig] = useState({ key: 'rank', direction: 'asc' })
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const perPage = 20

  const debouncedSearch = useDebounce(searchTerm, 200)

  const filtered = candidates.filter(c =>
    c.candidate_id.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
    c.reasoning.toLowerCase().includes(debouncedSearch.toLowerCase())
  )

  const sorted = [...filtered].sort((a, b) => {
    const dir = sortConfig.direction === 'asc' ? 1 : -1
    if (sortConfig.key === 'rank') return (parseInt(a.rank) - parseInt(b.rank)) * dir
    if (sortConfig.key === 'score') return (parseFloat(a.score) - parseFloat(b.score)) * dir
    return 0
  })

  const totalPages = Math.ceil(sorted.length / perPage)
  const pageData = sorted.slice((currentPage - 1) * perPage, currentPage * perPage)

  useEffect(() => {
    setCurrentPage(1)
  }, [debouncedSearch])

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }))
  }

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-8 pb-16">
      {/* Search & controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <label htmlFor="candidate-search" className="sr-only">Search candidates by ID or reasoning</label>
          <input
            id="candidate-search"
            type="text"
            placeholder="Search by ID or reasoning..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search candidates by ID or reasoning"
            className="w-full px-4 py-2.5 pl-10 rounded-xl bg-deep-800/60 border border-accent/20 text-sm text-gray-200
                       placeholder-gray-500 focus:outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20
                       transition-all duration-300"
          />
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span className="hidden sm:inline">{sorted.length} candidates</span>
          <span className="hidden sm:inline mx-1" aria-hidden="true">·</span>
          <button
            onClick={() => handleSort('rank')}
            aria-label={`Sort by rank, currently ${sortConfig.key === 'rank' ? sortConfig.direction : 'none'}`}
            className={`px-3 py-1.5 rounded-lg border transition-all ${
              sortConfig.key === 'rank'
                ? 'border-accent/50 text-accent-light bg-accent/10'
                : 'border-deep-700 text-gray-400 hover:border-accent/30'
            }`}>
            Rank {sortConfig.key === 'rank' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
          </button>
          <button
            onClick={() => handleSort('score')}
            aria-label={`Sort by score, currently ${sortConfig.key === 'score' ? sortConfig.direction : 'none'}`}
            className={`px-3 py-1.5 rounded-lg border transition-all ${
              sortConfig.key === 'score'
                ? 'border-accent/50 text-accent-light bg-accent/10'
                : 'border-deep-700 text-gray-400 hover:border-accent/30'
            }`}>
            Score {sortConfig.key === 'score' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-2xl border border-deep-700/50 bg-deep-900/60 backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <caption className="sr-only">Candidate rankings for Senior AI Engineer position at Redrob AI</caption>
            <thead>
              <tr className="border-b border-deep-700/50 bg-deep-800/40">
                <th scope="col" className="py-3.5 px-4 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 w-16">Rank</th>
                <th scope="col" className="py-3.5 px-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 w-28">ID</th>
                <th scope="col" className="py-3.5 px-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Reasoning</th>
                <th scope="col" className="py-3.5 px-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 min-w-[180px]">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-deep-700/30">
              <AnimatePresence mode="wait">
                {pageData.map((candidate) => (
                  <CandidateRow
                    key={candidate.candidate_id}
                    candidate={candidate}
                    rank={parseInt(candidate.rank)}
                    onClick={setSelectedCandidate}
                  />
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {pageData.length === 0 && (
          <div className="py-16 text-center text-gray-500">
            <p className="text-lg">No candidates match your search</p>
            <button onClick={() => setSearchTerm('')}
                    className="mt-2 text-sm text-accent-light hover:underline">
              Clear search
            </button>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <nav aria-label="Pagination" className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            aria-label="Go to previous page"
            className="px-3 py-1.5 rounded-lg border border-deep-700 text-gray-400 hover:border-accent/30
                       disabled:opacity-30 disabled:cursor-not-allowed transition-all">
            ← Prev
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter(p => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 2)
            .map((p, idx, arr) => (
              <span key={p} className="flex items-center gap-1">
                {idx > 0 && arr[idx - 1] !== p - 1 && <span className="text-gray-600" aria-hidden="true">…</span>}
                <button
                  onClick={() => setCurrentPage(p)}
                  aria-label={`Page ${p}`}
                  aria-current={currentPage === p ? 'page' : undefined}
                  className={`w-8 h-8 rounded-lg text-sm transition-all ${
                    currentPage === p
                      ? 'bg-accent/20 text-accent-light border border-accent/30'
                      : 'text-gray-400 hover:bg-deep-700/50'
                  }`}>
                  {p}
                </button>
              </span>
            ))}
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            aria-label="Go to next page"
            className="px-3 py-1.5 rounded-lg border border-deep-700 text-gray-400 hover:border-accent/30
                       disabled:opacity-30 disabled:cursor-not-allowed transition-all">
            Next →
          </button>
        </nav>
      )}

      {/* Modal */}
      <AnimatePresence>
        {selectedCandidate && (
          <CandidateModal candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} />
        )}
      </AnimatePresence>
    </section>
  )
}
