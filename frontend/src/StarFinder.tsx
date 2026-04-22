import { useState } from 'react'
import * as Astronomy from 'astronomy-engine'

type CelestialBody = {
  id: number
  name: string
  body_type: string
  right_ascension: string
  declination: string
  description: string
}

type BodyPosition = {
  body: CelestialBody
  altitude: number
  azimuth: number
  visible: boolean
}

type GeoLocation = {
  lat: number
  lon: number
  displayName: string
}

async function geocodeAddress(address: string): Promise<GeoLocation> {
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`
  const res = await fetch(url, {
    headers: { 'Accept-Language': 'en', 'User-Agent': 'Stargazer/1.0' }
  })
  const data = await res.json()
  if (!data.length) throw new Error('Address not found')
  return {
    lat: parseFloat(data[0].lat),
    lon: parseFloat(data[0].lon),
    displayName: data[0].display_name,
  }
}

function getAltAz(body: CelestialBody, lat: number, lon: number): { altitude: number, azimuth: number } | null {
  try {
    const ra = parseRA(body.right_ascension)
    const dec = parseDec(body.declination)
    if (ra === null || dec === null) return null

    const observer = new Astronomy.Observer(lat, lon, 0)
    const date = new Date()
    const equatorial = new Astronomy.Equatorial(ra, dec, 1000)
    const horizon = Astronomy.HorizonFromVector(
      Astronomy.VectorFromEquatorial(equatorial, date),
      observer
    )
    return {
      altitude: Math.round(horizon.altitude),
      azimuth: Math.round(horizon.azimuth),
    }
  } catch {
    return null
  }
}

function parseRA(ra: string): number | null {
  const match = ra.match(/(\d+)h\s*(\d+)m/)
  if (!match) return null
  return parseInt(match[1]) + parseInt(match[2]) / 60
}

function parseDec(dec: string): number | null {
  const match = dec.match(/([+-]?\d+)°/)
  if (!match) return null
  return parseInt(match[1])
}

function azimuthToDirection(az: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return dirs[Math.round(az / 45) % 8]
}

type Props = {
  bodies: CelestialBody[]
  onBodySelect: (body: CelestialBody, position: BodyPosition) => void
}

export default function StarFinder({ bodies, onBodySelect }: Props) {
  const [address, setAddress] = useState('')
  const [location, setLocation] = useState<GeoLocation | null>(null)
  const [positions, setPositions] = useState<BodyPosition[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSearch() {
    setLoading(true)
    setError(null)
    try {
      const geo = await geocodeAddress(address)
      setLocation(geo)

      const computed = bodies.map(body => {
        const altaz = getAltAz(body, geo.lat, geo.lon)
        return {
          body,
          altitude: altaz?.altitude ?? 0,
          azimuth: altaz?.azimuth ?? 0,
          visible: altaz ? altaz.altitude > 0 : false,
        }
      })
      setPositions(computed)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ margin: '32px 0' }}>
      <h2>Find Tonight's Sky</h2>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', justifyContent: 'center' }}>
        <input
          type="text"
          placeholder="Enter an address or city..."
          value={address}
          onChange={e => setAddress(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          style={{
            width: '360px',
            padding: '12px 16px',
            background: '#0d1b2a',
            border: '1px solid #1a3a5c',
            borderRadius: '8px',
            color: '#e8f4fd',
            fontSize: '15px',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSearch}
          disabled={loading || !address}
          style={{
            padding: '12px 24px',
            background: '#4fc3f7',
            color: '#050a0f',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            letterSpacing: '1px',
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <p style={{ color: '#f87171', textAlign: 'center' }}>{error}</p>}

      {location && (
        <p style={{ textAlign: 'center', marginBottom: '16px', color: '#4fc3f7' }}>
          {location.displayName}
        </p>
      )}

      {positions.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center' }}>
          {positions
            .sort((a, b) => b.altitude - a.altitude)
            .map(pos => (
              <div
                key={pos.body.id}
                onClick={() => onBodySelect(pos.body, pos)}
                style={{
                  padding: '12px 16px',
                  background: pos.visible ? '#0d1b2a' : '#080f17',
                  border: `1px solid ${pos.visible ? '#1a3a5c' : '#0d1f30'}`,
                  borderRadius: '10px',
                  opacity: pos.visible ? 1 : 0.4,
                  cursor: 'pointer',
                  minWidth: '140px',
                  textAlign: 'left',
                }}
              >
                <p style={{ color: '#e8f4fd', fontSize: '13px', marginBottom: '4px' }}>{pos.body.name}</p>
                <p style={{ color: '#4fc3f7', fontSize: '11px', marginBottom: '4px' }}>{pos.body.body_type}</p>
                {pos.visible
                  ? <p style={{ color: '#86efac', fontSize: '11px' }}>
                      {pos.altitude}° · {azimuthToDirection(pos.azimuth)}
                    </p>
                  : <p style={{ color: '#475569', fontSize: '11px' }}>Below horizon</p>
                }
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
