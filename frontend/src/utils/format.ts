export function formatCurrency(value: unknown): string {
  return '₱' + Number(value || 0).toLocaleString('en-PH')
}

export function formatDate(value: unknown): string {
  if (!value) return '—'
  return String(value)
}

export function formatDateTime(value: unknown): string {
  if (!value) return '—'
  const datePart = String(value).split(/[ T]/)[0]
  const [year, month, day] = datePart.split('-').map(Number)
  if (!year || !month || !day) return String(value)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatAuditDateTime(value: unknown): string {
  if (!value) return '—'
  const [datePart, timePart = ''] = String(value).trim().split(/[ T]/)
  const [year, month, day] = datePart.split('-').map(Number)
  if (!year || !month || !day) return String(value)
  const [hour = 0, minute = 0] = timePart.split(':').map(Number)
  const date = new Date(year, month - 1, day, hour, minute)
  return date.toLocaleString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function displayValue(value: unknown): string {
  if (value == null || value === '') return '—'
  return String(value)
}
