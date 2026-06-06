import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Stars } from '@react-three/drei'
import * as THREE from 'three'

function ParticleField({ count = 500 }) {
  const meshRef = useRef()
  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 40
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20
      positions[i * 3 + 2] = (Math.random() - 0.5) * 30
      const c = new THREE.Color().setHSL(0.7 + Math.random() * 0.15, 0.8, 0.5 + Math.random() * 0.3)
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
      sizes[i] = 0.02 + Math.random() * 0.04
    }
    return { positions, colors, sizes }
  }, [count])

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.02
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.01) * 0.1
    }
  })

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[particles.positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[particles.colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.06}
        vertexColors
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  )
}

function GeometricRing({ radius, color, speed, offset = 0 }) {
  const ref = useRef()
  const points = useMemo(() => {
    const pts = []
    const segments = 64
    for (let i = 0; i <= segments; i++) {
      const theta = (i / segments) * Math.PI * 2
      pts.push(new THREE.Vector3(Math.cos(theta) * radius, Math.sin(theta) * radius, 0))
    }
    return pts
  }, [radius])

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.z = state.clock.elapsedTime * speed + offset
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * speed * 0.5) * 0.2
    }
  })

  return (
    <mesh ref={ref}>
      <tubeGeometry args={[new THREE.CatmullRomCurve3(points, true), 64, 0.01, 8, true]} />
      <meshBasicMaterial color={color} transparent opacity={0.3} />
    </mesh>
  )
}

function FloatingCubes({ count = 15 }) {
  const cubes = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      position: [(Math.random() - 0.5) * 20, (Math.random() - 0.5) * 10, (Math.random() - 0.5) * 15 - 5],
      size: 0.05 + Math.random() * 0.1,
      color: new THREE.Color().setHSL(0.65 + Math.random() * 0.2, 0.7, 0.5),
      speed: 0.2 + Math.random() * 0.5,
    })), [count])

  return cubes.map((cube, i) => (
    <Float key={i} speed={cube.speed} rotationIntensity={0.5} floatIntensity={0.5}>
      <mesh position={cube.position}>
        <boxGeometry args={[cube.size, cube.size, cube.size]} />
        <meshBasicMaterial color={cube.color} transparent opacity={0.15} wireframe />
      </mesh>
    </Float>
  ))
}

export default function ThreeBackground() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas camera={{ position: [0, 0, 10], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={0.5} />
        <ParticleField count={800} />
        <GeometricRing radius={3} color="#6c5ce7" speed={0.15} offset={0} />
        <GeometricRing radius={4.5} color="#a29bfe" speed={-0.1} offset={1} />
        <GeometricRing radius={2} color="#fbbf24" speed={0.2} offset={2} />
        <FloatingCubes count={20} />
        <Stars radius={100} depth={50} count={1000} factor={4} saturation={0} fade speed={1} />
      </Canvas>
    </div>
  )
}
