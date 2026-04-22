type CelestialBody = {
  id: number
  name: string
  body_type: string
  right_ascension: string
  declination: string
}

function parseRA(ra: string): number | null {
  const match = ra.match(/(\d+)h\s*(\d+)m/)
  if (!match) return null
  const hours = parseInt(match[1])
  const minutes = parseInt(match[2])
  return hours + minutes / 60
}

function parseDec(dec: string): number | null {
  const match = dec.match(/([+-]?\d+)°/)
  if (!match) return null
  return parseInt(match[1])
}

type Props = {
  bodies: CelestialBody[]
}

export default function SkyMap({ bodies }: Props) {
  const width = 900
  const height = 450

  const dots = bodies.flatMap(body => {
    const ra = parseRA(body.right_ascension)
    const dec = parseDec(body.declination)
    if (ra === null || dec === null) return []
    const x = (ra / 24) * width
    const y = ((90 - dec) / 180) * height
    return [{ x, y, name: body.name, type: body.body_type }]
  })

  // Random background stars
  const bgStars = Array.from({ length: 200 }, (_, i) => ({
    x: (i * 137.5) % width,
    y: (i * 97.3) % height,
    r: i % 3 === 0 ? 1.2 : 0.6,
    opacity: 0.3 + (i % 5) * 0.1,
  }))

  // RA grid lines (every 2 hours)
  const raLines = Array.from({ length: 12 }, (_, i) => (i * 2 / 24) * width)

  // Dec grid lines (every 30 degrees)
  const decLines = Array.from({ length: 7 }, (_, i) => ((90 - (i * 30 - 90)) / 180) * height)

  return (
    <div style={{ margin: '24px 0' }}>
      <h2 style={{ color: 'white', marginBottom: '12px' }}>Sky Map</h2>
      <svg
        width={width}
        height={height}
        style={{
          background: 'radial-gradient(ellipse at center, #0d1b2a 0%, #050a0f 100%)',
          borderRadius: '16px',
          display: 'block',
          border: '1px solid #1a3a5c',
        }}
      >
        {/* Glow filter */}
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background stars */}
        {bgStars.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="white" opacity={s.opacity} />
        ))}

        {/* RA grid lines */}
        {raLines.map((x, i) => (
          <g key={i}>
            <line x1={x} y1={0} x2={x} y2={height} stroke="#1a3a5c" strokeWidth={0.5} />
            <text x={x + 4} y={14} fill="#2a5a8c" fontSize={10}>{i * 2}h</text>
          </g>
        ))}

        {/* Dec grid lines */}
        {decLines.map((y, i) => (
          <g key={i}>
            <line x1={0} y1={y} x2={width} y2={y} stroke="#1a3a5c" strokeWidth={0.5} />
            <text x={4} y={y - 3} fill="#2a5a8c" fontSize={10}>{90 - i * 30}°</text>
          </g>
        ))}

        {/* Celestial equator */}
        <line
          x1={0} y1={height / 2}
          x2={width} y2={height / 2}
          stroke="#1a5a3c" strokeWidth={1} strokeDasharray="4,4"
        />

        {/* Collected bodies */}
        {dots.map((dot, i) => (
          <g key={i} filter="url(#glow)">
            <circle cx={dot.x} cy={dot.y} r={8} fill="#4fc3f7" opacity={0.9} />
            <circle cx={dot.x} cy={dot.y} r={4} fill="white" />
            <text
              x={dot.x + 14}
              y={dot.y + 4}
              fill="white"
              fontSize={13}
              fontFamily="monospace"
            >
              {dot.name}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
