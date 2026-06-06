import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { MagneticElement } from './CursorPhysics'

gsap.registerPlugin(ScrollTrigger)

export default function Header({ candidateCount = 100, topScore = 0.85 }) {
  const headerRef = useRef(null)
  const titleRef = useRef(null)
  const subtitleRef = useRef(null)
  const statsRef = useRef(null)

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })
    tl.fromTo(titleRef.current,
      { y: -80, opacity: 0, scale: 0.8 },
      { y: 0, opacity: 1, scale: 1, duration: 1.2 }
    )
    .fromTo(subtitleRef.current,
      { y: 40, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8 },
      '-=0.6'
    )
    .fromTo(statsRef.current?.children,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, stagger: 0.15 },
      '-=0.4'
    )

    const scrollTrigger = ScrollTrigger.create({
      trigger: headerRef.current,
      start: 'top top',
      end: 'bottom top',
      onUpdate: (self) => {
        gsap.to(headerRef.current, {
          opacity: 1 - self.progress * 2,
          scale: 1 - self.progress * 0.05,
          y: -self.progress * 100,
          ease: 'power2.out',
        })
      },
    })

    return () => {
      tl.kill()
      scrollTrigger.kill()
    }
  }, [])

  return (
    <header ref={headerRef} className="relative pt-12 pb-8 px-4 sm:px-8 text-center">
      {/* Gradient accent line */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-1 bg-gradient-to-r from-transparent via-accent to-transparent rounded-full" aria-hidden="true" />

      <div ref={titleRef} className="inline-block">
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight">
          <span className="bg-gradient-to-r from-accent-light via-white to-accent bg-clip-text text-transparent"
                style={{ backgroundSize: '200% 100%', animation: 'gradient-shift 4s ease infinite' }}>
            Candidate Intelligence
          </span>
        </h1>
        <div className="h-1 w-0 mx-auto mt-4 bg-gradient-to-r from-accent to-accent-light rounded-full animate-pulse-glow"
             style={{ width: '60%' }} aria-hidden="true" />
      </div>

      <p ref={subtitleRef} className="mt-4 text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto font-light">
        AI-powered ranking for <span className="text-accent-light font-semibold">Senior AI Engineer</span> @ Redrob
      </p>

      <div ref={statsRef} className="mt-8 flex flex-wrap justify-center gap-6">
        <StatCard label="Total Ranked" value={candidateCount} icon="🏆" />
        <StatCard label="Top Score" value={topScore.toFixed(4)} icon="⭐" />
        <StatCard label="Job Role" value="Senior AI Engineer" icon="💼" />
        <StatCard label="Location" value="Pune / Noida" icon="📍" />
      </div>
    </header>
  )
}

function StatCard({ label, value, icon }) {
  const cardRef = useRef(null)

  useEffect(() => {
    gsap.fromTo(cardRef.current,
      { scale: 0, rotation: -15 },
      { scale: 1, rotation: 0, duration: 0.5, ease: 'back.out(1.7)' }
    )
  }, [])

  return (
    <MagneticElement strength={0.15}>
      <div ref={cardRef}
           className="relative px-5 py-3 rounded-xl bg-deep-800/60 border border-accent/20 backdrop-blur-sm min-w-[140px] transition-all duration-200 hover:border-accent/50 hover:shadow-[0_0_20px_rgba(108,92,231,0.3)]">
        <div className="text-2xl mb-1" aria-hidden="true">{icon}</div>
        <div className="text-xl font-bold text-white">{value}</div>
        <div className="text-xs text-gray-400 mt-0.5 uppercase tracking-wider">{label}</div>
      </div>
    </MagneticElement>
  )
}
