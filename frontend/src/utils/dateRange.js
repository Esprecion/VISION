// Parse "YYYY-MM-DD" or "YYYY-MM-DD HH:mm:ss[.ffffff]" as LOCAL time
export function parseLocal(value) {
  if (!value) return null
  if (value instanceof Date) return value
  const [datePart, timePart = '00:00:00'] = String(value).split(/[ T]/)
  const [y, m, d] = datePart.split('-').map(Number)
  const [hh, mm, ss] = timePart.split(':')
  return new Date(y, m - 1, d, Number(hh) || 0, Number(mm) || 0, Math.floor(Number(ss) || 0))
}

export function startOfDayMs(value) {
  const d = parseLocal(value)
  d.setHours(0, 0, 0, 0)
  return d.getTime()
}

export function endOfDayMs(value) {
  const d = parseLocal(value)
  d.setHours(23, 59, 59, 999)
  return d.getTime()
}

// Format a Date as "YYYY-MM-DD" using LOCAL time (never toISOString)
export function formatLocalDate(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// offset 0 = this quarter, -1 = last quarter
export function quarterRange(offset = 0) {
  const t = new Date()
  const q = Math.floor(t.getMonth() / 3) + offset
  const start = new Date(t.getFullYear(), q * 3, 1)
  const end = new Date(t.getFullYear(), q * 3 + 3, 0)
  return { from: formatLocalDate(start), to: formatLocalDate(end) }
}

export function yearRange() {
  const y = new Date().getFullYear()
  return { from: `${y}-01-01`, to: `${y}-12-31` }
}
