import { useEffect, useState } from 'react'
import AladinViewer from './AladinViewer'
import StarFinder from './StarFinder'

type Apod = {
  id: number
  date: string
  title: string
  explanation: string
  url: string
  hdurl: string | null
  media_type: string
  copyright: string | null
}

type CelestialBody = {
  id: number
  name: string
  body_type: string
  right_ascension: string
  declination: string
  description: string
}

type Collection = {
  id: number
  apod: number
  celestial_body: number
  collected_at: string
}

function App() {
  const [apods, setApods] = useState<Apod[]>([])
  const [bodies, setBodies] = useState<CelestialBody[]>([])
  const [collections, setCollections] = useState<Collection[]>([])
  const [selected, setSelected] = useState<{ body: CelestialBody, altitude: number, azimuth: number } | null>(null)
  // Target coordinates for the sky viewer (in degrees)
  const [viewTarget, setViewTarget] = useState<{ ra: number, dec: number } | null>(null)
  const [viewFov, setViewFov] = useState(60) // Field of view in degrees

  useEffect(() => {
    fetch('/api/apods/').then(res => res.json()).then(setApods)
    fetch('/api/celestial-bodies/').then(res => res.json()).then(setBodies)
    fetch('/api/collections/').then(res => res.json()).then(setCollections)
  }, [])

  const collectedIds = new Set(collections.map(c => c.celestial_body))

  function azimuthToDirection(az: number): string {
    const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    return dirs[Math.round(az / 45) % 8]
  }

  const getApodForBody = (bodyId: number): Apod | undefined => {
    const collection = collections.find(c => c.celestial_body === bodyId)
    if (!collection) return undefined
    return apods.find(a => a.id === collection.apod)
  }

  // Convert "5h 34m" → degrees for Aladin Lite
  function raToDegreees(ra: string): number | null {
    const match = ra.match(/(\d+)h\s*(\d+)m/)
    if (!match) return null
    return (parseInt(match[1]) + parseInt(match[2]) / 60) * 15
  }
  function decToDegrees(dec: string): number | null {
    const match = dec.match(/([+-]?\d+)°\s*(\d+)?/)
    if (!match) return null
    const d = parseInt(match[1])
    const m = match[2] ? parseInt(match[2]) / 60 : 0
    return d >= 0 ? d + m : d - m
  }

  function handleBodySelect(body: CelestialBody, position: { altitude: number, azimuth: number, body: CelestialBody, visible: boolean }) {
    setSelected({ body, altitude: position.altitude, azimuth: position.azimuth })

    // Pan the sky viewer to this body's coordinates
    const ra = raToDegreees(body.right_ascension)
    const dec = decToDegrees(body.declination)
    if (ra !== null && dec !== null) {
      setViewTarget({ ra, dec })
      setViewFov(1) // Zoom in to 1 degree FoV when selecting a body
    }
  }

  return (
    <div>
      <h1>Stargazer</h1>
      <AladinViewer
        bodies={bodies}
        targetRA={viewTarget?.ra}
        targetDec={viewTarget?.dec}
        fov={viewFov}
        selectedBody={selected?.body.name}
      />
      <StarFinder
        bodies={bodies}
        onBodySelect={handleBodySelect}
      />
      {selected && (
        <div style={{
          margin: '24px auto',
          maxWidth: '600px',
          padding: '24px',
          background: '#0d1b2a',
          border: '1px solid #1a3a5c',
          borderRadius: '12px',
          textAlign: 'left',
        }}>
          <p style={{ color: '#4fc3f7', fontSize: '11px', marginBottom: '8px' }}>{selected.body.body_type}</p>
          <p style={{ color: '#e8f4fd', fontSize: '18px', marginBottom: '12px' }}>{selected.body.name}</p>
          <p style={{ color: '#a8c4d8', fontSize: '13px' }}>
            {selected.altitude > 0
              ? `Visible tonight — ${selected.altitude}° above the horizon, facing ${azimuthToDirection(selected.azimuth)}`
              : 'Currently below the horizon'}
          </p>
        </div>
      )}
      <h2>Collection</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'center' }}>
        {bodies.map(body => {
          const apod = getApodForBody(body.id)
          const collected = collectedIds.has(body.id)
          return (
            <div
              key={body.id}
              style={{
                padding: '16px',
                border: `1px solid ${collected ? '#1a3a5c' : '#0d1f30'}`,
                borderRadius: '12px',
                opacity: collected ? 1 : 0.35,
                width: '160px',
                background: collected ? '#0d1b2a' : '#080f17',
                transition: 'opacity 0.2s',
              }}
            >
              {apod
                ? <img src={apod.url} style={{ width: '100%', borderRadius: '6px', marginBottom: '10px' }} />
                : <div style={{ width: '100%', height: '100px', borderRadius: '6px', background: '#0a1520', marginBottom: '10px' }} />
              }
              <p style={{ color: '#e8f4fd', fontSize: '12px', marginBottom: '4px' }}>{body.name}</p>
              <p style={{ color: '#4fc3f7', fontSize: '11px' }}>{body.body_type}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default App
