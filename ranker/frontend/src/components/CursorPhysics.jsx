import { useRef, useEffect, useState, useCallback } from 'react'
import { motion, useSpring, useMotionValue, useTransform } from 'framer-motion'

function CursorDot() {
  const cursorX = useMotionValue(-100)
  const cursorY = useMotionValue(-100)

  const springConfig = { damping: 25, stiffness: 400, mass: 0.5 }
  const dotX = useSpring(cursorX, springConfig)
  const dotY = useSpring(cursorY, springConfig)

  useEffect(() => {
    const handleMouseMove = (e) => {
      cursorX.set(e.clientX)
      cursorY.set(e.clientY)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [cursorX, cursorY])

  return (
    <motion.div
      className="cursor-dot"
      style={{
        x: dotX,
        y: dotY,
        position: 'fixed',
        top: 0,
        left: 0,
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #6c5ce7, #a29bfe)',
        pointerEvents: 'none',
        zIndex: 9999,
        translateX: '-50%',
        translateY: '-50%',
        boxShadow: '0 0 15px rgba(108, 92, 231, 0.6), 0 0 30px rgba(108, 92, 231, 0.3)',
      }}
    />
  )
}

function CursorRing() {
  const cursorX = useMotionValue(-100)
  const cursorY = useMotionValue(-100)

  const springConfig = { damping: 15, stiffness: 150, mass: 1 }
  const ringX = useSpring(cursorX, springConfig)
  const ringY = useSpring(cursorY, springConfig)

  const [isHovering, setIsHovering] = useState(false)

  const ringScale = useTransform(
    ringX,
    () => (isHovering ? 1.8 : 1)
  )

  useEffect(() => {
    const handleMouseMove = (e) => {
      cursorX.set(e.clientX)
      cursorY.set(e.clientY)
    }

    const handleMouseOver = (e) => {
      const target = e.target
      if (
        target.tagName === 'BUTTON' ||
        target.tagName === 'A' ||
        target.closest('button') ||
        target.closest('a') ||
        target.closest('[data-cursor-hover]') ||
        target.classList.contains('cursor-pointer')
      ) {
        setIsHovering(true)
      } else {
        setIsHovering(false)
      }
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseover', handleMouseOver)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseover', handleMouseOver)
    }
  }, [cursorX, cursorY])

  return (
    <motion.div
      className="cursor-ring"
      style={{
        x: ringX,
        y: ringY,
        position: 'fixed',
        top: 0,
        left: 0,
        width: 40,
        height: 40,
        borderRadius: '50%',
        border: '1.5px solid rgba(162, 155, 254, 0.5)',
        pointerEvents: 'none',
        zIndex: 9998,
        translateX: '-50%',
        translateY: '-50%',
        scale: ringScale,
        transition: 'width 0.2s, height 0.2s, border-color 0.2s',
      }}
    />
  )
}

function CursorTrail() {
  const [trail, setTrail] = useState([])
  const trailLength = 8

  useEffect(() => {
    const handleMouseMove = (e) => {
      setTrail((prev) => {
        const newTrail = [...prev, { x: e.clientX, y: e.clientY, id: Date.now() }]
        if (newTrail.length > trailLength) {
          return newTrail.slice(-trailLength)
        }
        return newTrail
      })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div className="cursor-trail" style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 9997 }}>
      {trail.map((point, i) => {
        const opacity = (i + 1) / trailLength * 0.4
        const size = 4 + (i / trailLength) * 4
        return (
          <motion.div
            key={point.id}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity, scale: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              left: point.x,
              top: point.y,
              width: size,
              height: size,
              borderRadius: '50%',
              background: `rgba(108, 92, 231, ${opacity})`,
              translateX: '-50%',
              translateY: '-50%',
              pointerEvents: 'none',
            }}
          />
        )
      })}
    </div>
  )
}

function MagneticElement({ children, strength = 0.3, className = '' }) {
  const ref = useRef(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const springX = useSpring(x, { damping: 20, stiffness: 300 })
  const springY = useSpring(y, { damping: 20, stiffness: 300 })

  const handleMouseMove = useCallback((e) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const deltaX = (e.clientX - centerX) * strength
    const deltaY = (e.clientY - centerY) * strength
    x.set(deltaX)
    y.set(deltaY)
  }, [x, y, strength])

  const handleMouseLeave = useCallback(() => {
    x.set(0)
    y.set(0)
  }, [x, y])

  return (
    <motion.div
      ref={ref}
      className={className}
      style={{ x: springX, y: springY }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </motion.div>
  )
}

function RippleEffect() {
  const [ripples, setRipples] = useState([])

  useEffect(() => {
    const handleClick = (e) => {
      const newRipple = {
        id: Date.now(),
        x: e.clientX,
        y: e.clientY,
      }
      setRipples((prev) => [...prev, newRipple])
      setTimeout(() => {
        setRipples((prev) => prev.filter((r) => r.id !== newRipple.id))
      }, 800)
    }
    window.addEventListener('click', handleClick)
    return () => window.removeEventListener('click', handleClick)
  }, [])

  return (
    <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 9996 }}>
      {ripples.map((ripple) => (
        <motion.div
          key={ripple.id}
          initial={{ width: 0, height: 0, opacity: 0.6 }}
          animate={{ width: 100, height: 100, opacity: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{
            position: 'fixed',
            left: ripple.x,
            top: ripple.y,
            borderRadius: '50%',
            border: '2px solid rgba(108, 92, 231, 0.6)',
            translateX: '-50%',
            translateY: '-50%',
            pointerEvents: 'none',
          }}
        />
      ))}
    </div>
  )
}

export default function CursorPhysics() {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    setIsMobile(window.matchMedia('(pointer: coarse)').matches || window.innerWidth < 768)
  }, [])

  if (isMobile) return null

  return (
    <>
      <style>{`
        * { cursor: none !important; }
        .cursor-dot, .cursor-ring { mix-blend-mode: screen; }
        @media (pointer: coarse), (max-width: 768px) {
          * { cursor: auto !important; }
          .cursor-dot, .cursor-ring, .cursor-trail { display: none !important; }
        }
      `}</style>
      <CursorDot />
      <CursorRing />
      <CursorTrail />
      <RippleEffect />
    </>
  )
}

export { MagneticElement }
