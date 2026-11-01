/**
 * Safe CSV export utility with spreadsheet formula-injection defense.
 */

/**
 * Sanitize a cell value to prevent CSV formula injection (CSV Injection / DDE).
 * If a cell starts with '=', '+', '-', or '@', prepend a single quote so spreadsheet
 * tools (Excel, Google Sheets, LibreOffice) treat it strictly as literal text.
 */
export function sanitizeCsvCell(value: any): string {
  if (value === null || value === undefined) {
    return ''
  }

  const str = String(value)
  // Check for formula injection indicators
  if (/^[=+\-@\t\r]/.test(str)) {
    return `"'${str.replace(/"/g, '""')}"`
  }

  // Escape quotes and wrap in quotes if contains comma, quote, or newline
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }

  return str
}

/**
 * Export table columns and rows as a downloadable CSV file in the browser.
 */
export function exportResultsToCsv(
  columns: string[],
  rows: (string | number | boolean | null)[][],
  filename: string = 'query_results.csv',
  isTruncated: boolean = false
): void {
  const headerLine = columns.map(sanitizeCsvCell).join(',')
  const rowLines = rows.map((row) => row.map(sanitizeCsvCell).join(','))

  const lines = [headerLine, ...rowLines]

  if (isTruncated) {
    lines.push('')
    lines.push(
      sanitizeCsvCell(
        '# NOTICE: Query results were truncated at server limit. Only the preview rows above were exported.'
      )
    )
  }

  const csvContent = lines.join('\r\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
