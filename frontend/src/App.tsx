import { useEffect, useState } from 'react'
import AladinViewer from './AladinViewer'
import AstridChat from './AstridChat'

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
  const [viewTarget, setViewTarget] = useState<{ ra: number, dec: number } | null>(null)
  const [viewFov, setViewFov] = useState(10)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fire all three fetches simultaneously — Promise.all waits for all of them
    // One .catch() covers all three — if any fail, the user sees an error message
    Promise.all([
      fetch('/api/apods/').then(res => res.json()),
      fetch('/api/celestial-bodies/').then(res => res.json()),
      fetch('/api/collections/').then(res => res.json()),
    ])
      .then(([apodsData, bodiesData, collectionsData]) => {
        setApods(apodsData)
        setBodies(bodiesData)
        setCollections(collectionsData)
      })
      .catch(() => setError("Couldn't load the collection, try refreshing."))
      .finally(() => setLoading(false))
  }, [])

  const collectedIds = new Set(collections.map(c => c.celestial_body))

  const getApodForBody = (bodyId: number): Apod | undefined => {
    const collection = collections.find(c => c.celestial_body === bodyId)
    if (!collection) return undefined
    return apods.find(a => a.id === collection.apod)
  }

  // Convert "5h 34m" -> degrees for Aladin Lite
  function raToDegrees(ra: string): number | null {
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

  // When a collection card is clicked, pan the sky viewer to that body
  function handleBodyClick(body: CelestialBody) {
    const ra = raToDegrees(body.right_ascension)
    const dec = decToDegrees(body.declination)
    if (ra !== null && dec !== null) {
      setViewTarget({ ra, dec })
      setViewFov(1)
    }
  }

  if (loading) return (
    <div style={{ color: '#8892a4', fontStyle: 'italic', padding: '40px', textAlign: 'center' }}>
      Pondering...
    </div>
  )

  if (error) return (
    <div style={{ color: '#e57373', padding: '40px', textAlign: 'center' }}>
      {error}
    </div>
  )

  return (
    <div>
      <h1>Stargazer</h1>
      <AladinViewer
        bodies={bodies}
        targetRA={viewTarget?.ra}
        targetDec={viewTarget?.dec}
        fov={viewFov}
      />
      <AstridChat />
      <h2>Collection</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'center' }}>
        {bodies.map(body => {
          const apod = getApodForBody(body.id)
          const collected = collectedIds.has(body.id)
          return (
            <div
              key={body.id}
              onClick={() => handleBodyClick(body)}
              style={{
                padding: '16px',
                border: `1px solid ${collected ? '#1a3a5c' : '#0d1f30'}`,
                borderRadius: '12px',
                opacity: collected ? 1 : 0.35,
                width: '160px',
                background: collected ? '#0d1b2a' : '#080f17',
                transition: 'opacity 0.2s',
                cursor: 'pointer',
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
