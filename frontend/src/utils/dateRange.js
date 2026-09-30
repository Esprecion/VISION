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
