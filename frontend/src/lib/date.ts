/**
 * Local date helpers (no UTC). Use for "today" and date inputs so that
 * in CDMX (UTC-6) the displayed/saved date matches the user's calendar.
 */

/**
 * Returns local date as YYYY-MM-DD (suitable for <input type="date" /> and API).
 * Defaults to now when no argument.
 */
export function formatLocalYYYYMMDD(d: Date = new Date()): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Returns local date-time string (ISO-like but in local time).
 * Use when you need a readable local datetime without UTC shift.
 */
export function formatLocalISODateTime(d: Date = new Date()): string {
  return new Intl.DateTimeFormat('sv-SE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
    .format(d)
    .replace(' ', 'T')
}
