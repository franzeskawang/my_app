// Expense value formatters used by the bookkeeping presentation.
export const formatMoney = (value) => new Intl.NumberFormat('zh-TW', {
  maximumFractionDigits: 0,
}).format(value || 0)
