import { useEffect, useRef, useState } from 'react'

// TypeScript needs to know about the global `A` object that Aladin Lite
// injects via the CDN script tag. This tells TypeScript "trust me, this exists."
// The WHY: Aladin Lite wasn't built for React/TypeScript. It attaches to `window.A`.
// This declaration bridges the gap between their vanilla JS and our typed React code.
declare global {
  interface Window {
    A: any
  }
}

// Load the Aladin Lite script dynamically and wait for WASM init.
// The WHY: Loading external scripts in React is tricky. A <script> tag in
// index.html loads asynchronously - your component might mount before it's
// ready. Dynamic loading lets us control the timing: load script → wait for
// onload → wait for WASM init → resolve. This is a reusable pattern for
// any external library that doesn't have an npm package.
function loadAladinLite(): Promise<any> {
  // If already loaded, just wait for WASM init
  if (window.A) return window.A.init

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://aladin.cds.unistra.fr/AladinLite/api/v3/3.8.1/aladin.js'
    script.charset = 'utf-8'
    script.onload = () => {
      console.log('[Stargazer] Aladin Lite script loaded, waiting for WASM...')
      if (window.A && window.A.init) {
        window.A.init.then(() => {
          console.log('[Stargazer] Aladin Lite WASM ready!')
          resolve(window.A)
        }).catch(reject)
      } else {
        reject(new Error('Aladin Lite loaded but window.A not found'))
      }
    }
    script.onerror = () => reject(new Error('Failed to load Aladin Lite script'))
    document.head.appendChild(script)
  })
}

type CelestialBody = {
  id: number
  name: string
  body_type: string
  right_ascension: string
  declination: string
}

type Props = {
  // The target coordinates to center the view on
  targetRA?: number   // Right Ascension in degrees
  targetDec?: number  // Declination in degrees
  // Field of view in degrees (smaller = more zoomed in)
  fov?: number
  // Bodies to show as markers on the sky
  bodies?: CelestialBody[]
}

// Parse "5h 34m" format to decimal degrees (RA is in hours, 1h = 15 degrees)
function parseRADegrees(ra: string): number | null {
  const match = ra.match(/(\d+)h\s*(\d+)m/)
  if (!match) return null
  const hours = parseInt(match[1]) + parseInt(match[2]) / 60
  return hours * 15  // Convert hours to degrees (360° / 24h = 15°/h)
}

// Parse "+22°" format to decimal degrees
function parseDecDegrees(dec: string): number | null {
  const match = dec.match(/([+-]?\d+)°\s*(\d+)?/)
  if (!match) return null
  const degrees = parseInt(match[1])
  const minutes = match[2] ? parseInt(match[2]) / 60 : 0
  return degrees >= 0 ? degrees + minutes : degrees - minutes
}

export default function AladinViewer({ targetRA, targetDec, fov = 10, bodies = [] }: Props) {
  // useRef gives us a stable reference to the DOM div across re-renders.
  // The WHY: React re-renders when props change, but Aladin Lite is initialized
  // once and then controlled via its own API. The ref lets us initialize once
  // and then call aladin.gotoRaDec() etc. without re-creating the viewer.
  const containerRef = useRef<HTMLDivElement>(null)
  const aladinRef = useRef<any>(null)
  const catalogRef = useRef<any>(null)

  const [loading, setLoading] = useState(true)
  const [ready, setReady] = useState(false) // Tracks when Aladin is fully initialized
  const [error, setError] = useState<string | null>(null)

  // Initialize Aladin Lite ONCE when the component mounts.
  // The WHY: This is the "imperative escape hatch" pattern. React manages the
  // div's lifecycle (create/destroy), but Aladin Lite manages everything
  // inside it (WebGL canvas, tile loading, interaction).
  useEffect(() => {
    if (!containerRef.current) return

    let cancelled = false

    loadAladinLite()
      .then((A) => {
        if (cancelled || !containerRef.current) return

        const aladin = A.aladin(containerRef.current, {
          survey: 'https://alasky.cds.unistra.fr/DSS/DSSColor',
          fov: fov,
          // Moon's current RA/Dec (moves daily, but close enough for initial view)
          // Sesame resolver only knows fixed deep-sky objects, not solar system bodies.
          target: '56.25 +24',
          showReticle: true,
          showCooGrid: false,
          showLayersControl: false,
          showGotoControl: false,
          showFrame: false,
          showZoomControl: true,
          showFullscreenControl: true,
          showProjectionControl: false,
        })

        aladinRef.current = aladin
        // We don't use a shared catalog anymore - each body gets its own
        // catalog with a custom Canvas shape (dot + label text). This is
        // because labelColumn doesn't render in Aladin Lite v3.8.
        catalogRef.current = true as any // just a flag that init is done
        setLoading(false)
        setReady(true)
      })
      .catch((err) => {
        console.error('[Stargazer] Aladin Lite failed to load:', err)
        setError(err.message)
        setLoading(false)
      })

    return () => {
      cancelled = true
      aladinRef.current = null
      catalogRef.current = null
    }
  }, [])

  // Navigate when target coordinates change.
  // The WHY: This is the key integration point. When the user clicks a body
  // in StarFinder, the parent component updates targetRA/targetDec props,
  // which triggers this effect, which calls Aladin's API to pan the view.
  // React's declarative model (props) drives the imperative library (gotoRaDec).
  useEffect(() => {
    if (!aladinRef.current || targetRA === undefined || targetDec === undefined) return
    aladinRef.current.gotoRaDec(targetRA, targetDec)
  }, [targetRA, targetDec])

  // Update field of view when it changes
  useEffect(() => {
    if (!aladinRef.current) return
    aladinRef.current.setFov(fov)
  }, [fov])

  // Update markers when bodies change.
  // The WHY: We clear and re-add all sources when the body list changes.
  // This is simpler than diffing individual markers. For ~50 bodies this
  // is instant. You'd optimize if you had thousands (same tradeoff as
  // React's virtual DOM diffing vs. replacing).
  // Add labeled markers for each body.
  // Each body gets its own catalog with a custom Canvas shape (dot + text).
  // The WHY: Aladin's labelColumn doesn't render in v3.8. When a library
  // feature is broken, you draw it yourself. Canvas shapes are the escape
  // hatch - same technique as custom markers in Leaflet or Mapbox.
  useEffect(() => {
    if (!ready || !aladinRef.current || !window.A) {
      console.log(`[Stargazer] Waiting for Aladin: ready=${ready}`)
      return
    }

    console.log(`[Stargazer] Adding ${bodies.length} labeled bodies to sky viewer`)

    bodies.forEach(body => {
      const ra = parseRADegrees(body.right_ascension)
      const dec = parseDecDegrees(body.declination)
      if (ra === null || dec === null) return

      // Draw a canvas with a glowing dot and the body's name
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')!
      ctx.font = 'bold 12px sans-serif'
      const textWidth = ctx.measureText(body.name).width
      canvas.width = Math.max(textWidth + 16, 40)
      canvas.height = 32

      // Glowing dot
      ctx.shadowColor = '#4fc3f7'
      ctx.shadowBlur = 6
      ctx.fillStyle = '#4fc3f7'
      ctx.beginPath()
      ctx.arc(canvas.width / 2, 7, 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0

      // Label text
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(body.name, canvas.width / 2, 28)

      const cat = window.A.catalog({ shape: canvas, sourceSize: 32 })
      aladinRef.current.addCatalog(cat)
      cat.addSources([window.A.source(ra, dec, { name: body.name })])
    })
  }, [bodies, ready])

  return (
    <div style={{ margin: '24px 0' }}>
      <h2 style={{ color: 'white', marginBottom: '12px' }}>Sky Viewer</h2>
      <div style={{ position: 'relative' }}>
        <div
          ref={containerRef}
          style={{
            width: '100%',
            height: '70vh',
            borderRadius: '16px',
            border: '1px solid #1a3a5c',
            overflow: 'hidden',
          }}
        />
        {loading && (
          <div style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#4fc3f7',
            fontSize: '14px',
            background: 'rgba(5, 10, 15, 0.8)',
            borderRadius: '16px',
          }}>
            Loading sky viewer...
          </div>
        )}
        {error && (
          <div style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f87171',
            fontSize: '14px',
            background: 'rgba(5, 10, 15, 0.8)',
            borderRadius: '16px',
          }}>
            Sky viewer error: {error}
          </div>
        )}
      </div>
    </div>
  )
}
