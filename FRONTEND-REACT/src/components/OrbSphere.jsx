/**
 * OrbSphere.jsx
 * Esfera de energia animada com vídeo circular da IA.
 * Props:
 *   status: 'connecting' | 'starting' | 'online' | 'offline'
 *   size: number (px, default 200)
 */

import { useRef, useEffect } from 'react'
import styles from './OrbSphere.module.css'

export default function OrbSphere({ status = 'connecting', size = 200 }) {
  const videoRef = useRef(null)

  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    v.addEventListener('error', () => { v.style.display = 'none' })
    v.addEventListener('canplay', () => { v.style.display = 'block' })
  }, [])

  const isStarting = status === 'starting' || status === 'connecting'

  return (
    <div className={styles.wrapper} style={{ '--orb': `${size}px` }}>
      {/* Anéis orbitais */}
      <div className={`${styles.ring} ${styles.ring3}`} />
      <div className={`${styles.ring} ${styles.ring2}`} />
      <div className={`${styles.ring} ${styles.ring1}`} />

      {/* Brilho difuso */}
      <div className={styles.glow} />

      {/* Núcleo */}
      <div className={`${styles.core} ${styles[status]}`}>
        {/* Vídeo circular — substitua assets/ia.mp4 pelo seu arquivo */}
        <video
          ref={videoRef}
          className={styles.video}
          src="/ia.mp4"
          autoPlay muted loop playsInline
          style={{ display: 'none' }}
        />

        {/* Fallback SVG — aparece quando não há vídeo */}
        <svg className={styles.fallback} viewBox="0 0 80 80" fill="none">
          <circle cx="40" cy="40" r="28" stroke="var(--c)" strokeWidth="1" strokeDasharray="4 4"/>
          <circle cx="40" cy="40" r="14" stroke="var(--c)" strokeWidth="1.5" opacity=".5"/>
          <circle cx="40" cy="40" r="4"  fill="var(--c)"/>
          <line x1="40" y1="12" x2="40" y2="0"  stroke="var(--c)" strokeWidth="1" opacity=".35"/>
          <line x1="40" y1="68" x2="40" y2="80" stroke="var(--c)" strokeWidth="1" opacity=".35"/>
          <line x1="12" y1="40" x2="0"  y2="40" stroke="var(--c)" strokeWidth="1" opacity=".35"/>
          <line x1="68" y1="40" x2="80" y2="40" stroke="var(--c)" strokeWidth="1" opacity=".35"/>
        </svg>

        {/* Overlay de "iniciando" */}
        {isStarting && (
          <div className={styles.startingOverlay}>
            <div className={styles.spinner} />
            <span>{status === 'starting' ? 'Iniciando' : 'Conectando'}</span>
          </div>
        )}

        {/* Indicador offline */}
        {status === 'offline' && (
          <div className={`${styles.startingOverlay} ${styles.offlineOverlay}`}>
            <span className={styles.offlineIcon}>✕</span>
            <span>Offline</span>
          </div>
        )}
      </div>
    </div>
  )
}
