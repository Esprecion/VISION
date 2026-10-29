export function formatCurrency(value: unknown): string {
  return '₱' + Number(value || 0).toLocaleString('en-PH')
}

export function formatDate(value: unknown): string {
  if (!value) return '—'
  return String(value)
}

export function displayValue(value: unknown): string {
  if (value == null || value === '') return '—'
  return String(value)
}
