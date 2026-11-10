// Owns bookkeeping screen state, user actions, and calls into the API module.
import { useEffect, useMemo, useState } from 'react'
import { expenseApi } from './expenseApi'
import { getTodayIsoDate } from '../../platform/web/dateTime'
import { cancelScheduledTask, scheduleTask } from '../../platform/web/scheduler'

const blankExpense = () => ({ item: '', amount: '', spent_on: getTodayIsoDate() })
const emptyDashboard = { today: 0, this_month: 0, big_boss: 0, daily: 0, expenses: [] }

export function useExpenseTracker() {
  const [dashboard, setDashboard] = useState(emptyDashboard)
  const [expenses, setExpenses] = useState([blankExpense()])
  const [comment, setComment] = useState('')
  const [advice, setAdvice] = useState('')
  const [aiError, setAiError] = useState('')
  const [loading, setLoading] = useState(false)
  const [waitingHint, setWaitingHint] = useState(false)
  const [reversingId, setReversingId] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('全部')

  const refresh = async () => {
    try {
      setDashboard(await expenseApi.getDashboard())
      setError('')
    } catch {
      setError('目前連不上記帳伺服器，請確認 FastAPI 已啟動。')
    }
  }

  useEffect(() => { refresh() }, [])

  const filtered = useMemo(
    () => dashboard.expenses.filter((entry) => tab === '全部' || entry.category === tab),
    [dashboard.expenses, tab],
  )
  const updateExpense = (index, key, value) => setExpenses((items) => items.map(
    (item, currentIndex) => currentIndex === index ? { ...item, [key]: value } : item,
  ))
  const addExpense = () => setExpenses((items) => [...items, blankExpense()])
  const removeExpense = (index) => setExpenses((items) => (
    items.length > 1 ? items.filter((_, currentIndex) => currentIndex !== index) : items
  ))

  const reverseExpense = async (entry) => {
    setReversingId(entry.id); setError('')
    try {
      await expenseApi.deleteExpense(entry.id)
      await refresh()
    } catch (err) {
      setError(err.message || 'Reversal failed. Please try again.')
    } finally { setReversingId(null) }
  }

  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError(''); setAiError(''); setWaitingHint(false)
    const waitingHintTimer = scheduleTask(() => setWaitingHint(true), 20_000)
    try {
      const result = await expenseApi.createExpenses({
        expenses: expenses.map((entry) => ({ ...entry, amount: Number(entry.amount) })),
        comment,
      })
      setAdvice(result.advice); setAiError(result.ai_error || '')
      setExpenses([blankExpense()]); setComment(''); await refresh()
    } catch (err) {
      setError(err.message || '送出失敗，請確認後端服務。')
    } finally {
      cancelScheduledTask(waitingHintTimer)
      setWaitingHint(false)
      setLoading(false)
    }
  }

  return {
    dashboard, expenses, comment, advice, aiError, loading, waitingHint, reversingId, error, tab, filtered,
    setComment, setTab, updateExpense, addExpense, removeExpense, reverseExpense, submit,
  }
}
