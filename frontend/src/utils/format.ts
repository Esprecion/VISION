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

export function displayValue(value: unknown): string {
  if (value == null || value === '') return '—'
  return String(value)
}
