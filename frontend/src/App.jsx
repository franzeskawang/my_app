import { useEffect, useMemo, useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, CalendarDays, Check, ChevronDown, CircleHelp, Coffee, LoaderCircle, Plus, RotateCcw, Send, Sparkles, Trash2, Wallet } from 'lucide-react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const today = new Date().toISOString().slice(0, 10)
const money = (value) => new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 0 }).format(value || 0)
const blankExpense = () => ({ item: '', amount: '', spent_on: today })

export default function App() {
  const [dashboard, setDashboard] = useState({ today: 0, this_month: 0, big_boss: 0, daily: 0, expenses: [] })
  const [expenses, setExpenses] = useState([blankExpense()])
  const [comment, setComment] = useState('')
  const [advice, setAdvice] = useState('')
  const [aiError, setAiError] = useState('')
  const [loading, setLoading] = useState(false)
  const [reversingId, setReversingId] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('全部')

  const refresh = async () => {
    try {
      const response = await fetch(`${API}/api/dashboard`)
      if (!response.ok) throw new Error('無法讀取資料')
      setDashboard(await response.json())
      setError('')
    } catch { setError('目前連不上記帳伺服器，請確認 FastAPI 已啟動。') }
  }
  useEffect(() => { refresh() }, [])

  const filtered = useMemo(() => dashboard.expenses.filter((entry) => tab === '全部' || entry.category === tab), [dashboard.expenses, tab])
  const updateExpense = (index, key, value) => setExpenses((items) => items.map((item, i) => i === index ? { ...item, [key]: value } : item))
  const addExpense = () => setExpenses((items) => [...items, blankExpense()])
  const removeExpense = (index) => setExpenses((items) => items.length > 1 ? items.filter((_, i) => i !== index) : items)

  const reverseExpense = async (entry) => {
    setReversingId(entry.id); setError('')
    try {
      const response = await fetch(`${API}/api/expenses/${entry.id}`, { method: 'DELETE' })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Could not reverse this expense.')
      await refresh()
    } catch (err) {
      setError(err.message || 'Reversal failed. Please try again.')
    } finally { setReversingId(null) }
  }

  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError(''); setAdvice(''); setAiError('')
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), 75_000)
    try {
      const response = await fetch(`${API}/api/expenses`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expenses: expenses.map((e) => ({ ...e, amount: Number(e.amount) })), comment }),
        signal: controller.signal,
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || '送出失敗，請檢查輸入資料。')
      setAdvice(result.advice); setAiError(result.ai_error || ''); setExpenses([blankExpense()]); setComment(''); await refresh()
    } catch (err) {
      setError(err.name === 'AbortError'
        ? '等待 Gemini 回應逾時。請查看最近記帳確認是否已保存，再決定是否重送，避免重複記帳。'
        : (err.message || '送出失敗，請確認後端服務。'))
    }
    finally { window.clearTimeout(timeoutId); setLoading(false) }
  }

  return <main className="min-h-screen bg-[#f7f7f4] text-[#252821]">
    <div className="mx-auto max-w-[1180px] px-5 py-7 sm:px-8 lg:py-10">
      <header className="mb-9 flex items-center justify-between">
        <a href="#top" className="flex items-center gap-3 text-lg font-semibold tracking-tight"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-[#314c3b] text-white"><Wallet size={19}/></span>日常記帳</a>
        <div className="hidden items-center gap-2 rounded-full border border-[#e7e8e2] bg-white px-4 py-2 text-sm text-[#687064] sm:flex"><CalendarDays size={15}/>{new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' })}<ChevronDown size={14}/></div>
        <button aria-label="說明" className="grid h-10 w-10 place-items-center rounded-full border border-[#e7e8e2] bg-white text-[#687064]"><CircleHelp size={18}/></button>
      </header>

      <section id="top" className="mb-8 grid gap-5 lg:grid-cols-[1.45fr_1fr]">
        <div className="relative overflow-hidden rounded-[28px] bg-[#314c3b] p-7 text-white sm:p-9">
          <div className="relative z-10 max-w-md"><p className="mb-2 text-sm text-[#d5e1d5]">今天的花費</p><h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">NT$ {money(dashboard.today)}</h1><p className="mt-5 text-sm text-[#d5e1d5]">每一筆記錄，都是更了解自己的開始。</p></div>
          <div className="absolute -right-8 -top-16 h-64 w-64 rounded-full border border-white/10"/><div className="absolute -right-1 -top-8 h-52 w-52 rounded-full border border-white/10"/>
          <div className="absolute bottom-5 right-8 hidden h-28 w-28 items-center justify-center rounded-full bg-[#c8d9bd] text-[#314c3b] sm:flex"><Coffee size={34}/></div>
        </div>
        <div className="grid grid-cols-2 gap-5">
          <Metric label="本月總花費" amount={dashboard.this_month} icon={<ArrowUpRight size={17}/>} tone="sage" />
          <Metric label="大魔王支出" amount={dashboard.big_boss} icon={<ArrowDownLeft size={17}/>} tone="peach" />
          <Metric label="日常支出" amount={dashboard.daily} icon={<ArrowUpRight size={17}/>} tone="cream" />
          <div className="rounded-[24px] border border-[#e7e8e2] bg-white p-5 sm:p-6"><div className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl bg-[#f3f1eb] text-[#687064]"><Sparkles size={17}/></div><p className="text-sm text-[#81867e]">記帳小提醒</p><p className="mt-2 text-sm font-medium leading-relaxed">固定支出也值得定期檢視喔。</p></div>
        </div>
      </section>

      <section className="grid items-start gap-6 lg:grid-cols-[1.05fr_.95fr]">
        <form onSubmit={submit} className="rounded-[26px] border border-[#e7e8e2] bg-white p-5 sm:p-7">
          <div className="mb-6 flex items-start justify-between"><div><p className="text-sm text-[#81867e]">新增紀錄</p><h2 className="mt-1 text-xl font-semibold">今天買了什麼？</h2></div><span className="rounded-full bg-[#f1f4ef] px-3 py-1.5 text-xs font-medium text-[#53705b]">{expenses.length} 筆</span></div>
          <div className="space-y-3">
            {expenses.map((entry, index) => <div key={index} className="grid grid-cols-[1fr_105px_42px] gap-2 sm:grid-cols-[1fr_120px_145px_42px]">
              <input required aria-label="物品名稱" placeholder="品項，例如：午餐" value={entry.item} onChange={(e) => updateExpense(index, 'item', e.target.value)} className="field min-w-0" />
              <div className="relative"><span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[#9a9e96]">$</span><input required type="number" min="1" step="1" aria-label="金額" placeholder="金額" value={entry.amount} onChange={(e) => updateExpense(index, 'amount', e.target.value)} className="field w-full pl-7" /></div>
              <input required type="date" aria-label="日期" value={entry.spent_on} onChange={(e) => updateExpense(index, 'spent_on', e.target.value)} className="field col-span-2 sm:col-span-1" />
              <button type="button" aria-label="移除項目" onClick={() => removeExpense(index)} className="grid h-11 w-10 place-items-center rounded-xl text-[#a0a49d] hover:bg-[#f8eeeb] hover:text-[#b8634f]"><Trash2 size={16}/></button>
            </div>)}
          </div>
          <button type="button" onClick={addExpense} className="mt-4 flex items-center gap-2 text-sm font-medium text-[#52715b] hover:text-[#314c3b]"><Plus size={17}/>新增一筆</button>
          <label className="mb-2 mt-7 block text-sm font-medium">留句話給自己 <span className="font-normal text-[#9a9e96]">（每次送出都會一併記錄）</span></label>
          <textarea required value={comment} onChange={(e) => setComment(e.target.value)} maxLength={2000} rows={3} placeholder="例如：今天和同事聚餐，很開心但有點超出預算……" className="field w-full resize-y" />
          {error && <p role="alert" className="mt-4 rounded-xl bg-[#fff1ed] px-4 py-3 text-sm text-[#a84e3b]">{error}</p>}
          <button disabled={loading} className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#314c3b] px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-[#263e30] disabled:opacity-60">{loading ? <LoaderCircle className="animate-spin" size={17}/> : <Send size={16}/>} {loading ? 'Gemini 分析中…' : '送出記帳'}</button>
        </form>

        <div className="space-y-6">
          {advice && <section className="rounded-[24px] border border-[#dce6d8] bg-[#eff4ed] p-5 sm:p-6"><div className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#46604c]"><Sparkles size={17}/>AI 理財小回饋</div><p className="text-sm leading-7 text-[#4f5d50]">{advice}</p>{aiError && <details className="mt-3 text-xs text-[#687064]"><summary className="cursor-pointer">查看錯誤摘要</summary><pre className="mt-2 whitespace-pre-wrap break-words rounded-lg bg-white/70 p-3 font-mono">{aiError}</pre></details>}</section>}
          <section className="rounded-[26px] border border-[#e7e8e2] bg-white p-5 sm:p-7">
            <div className="mb-5 flex items-center justify-between"><div><p className="text-sm text-[#81867e]">消費足跡</p><h2 className="mt-1 text-xl font-semibold">最近記帳</h2></div><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f3f1eb] text-[#687064]"><Check size={17}/></span></div>
            <div className="mb-4 flex gap-2">{['全部', '大魔王支出', '日常支出'].map((name) => <button key={name} onClick={() => setTab(name)} className={`rounded-full px-3 py-1.5 text-xs font-medium ${tab === name ? 'bg-[#314c3b] text-white' : 'bg-[#f4f4f0] text-[#747a70]'}`}>{name}</button>)}</div>
            <div className="divide-y divide-[#f0f0ec]">
              {filtered.length ? filtered.slice(0, 8).map((entry) => <article key={entry.id} className="flex items-center justify-between gap-3 py-3.5"><div className="flex min-w-0 items-center gap-3"><span className={`grid h-10 w-10 shrink-0 place-items-center rounded-2xl ${entry.category === '大魔王支出' ? 'bg-[#f9eee7] text-[#b87951]' : 'bg-[#eef3ed] text-[#5e765e]'}`}>{entry.category === '大魔王支出' ? <ArrowDownLeft size={17}/> : <Coffee size={17}/>}</span><div className="min-w-0"><p className="truncate text-sm font-medium">{entry.item}</p><p className="mt-1 text-xs text-[#989d94]">{entry.spent_on} · {entry.category}</p></div></div><div className="flex shrink-0 items-center gap-2"><p className="text-sm font-semibold">NT$ {money(entry.amount)}</p><button type="button" aria-label={`Reverse ${entry.item} expense`} title="Reverse this expense" disabled={reversingId === entry.id} onClick={() => reverseExpense(entry)} className="grid h-9 w-9 place-items-center rounded-xl text-[#81867e] transition hover:bg-[#f8eeeb] hover:text-[#b8634f] disabled:cursor-wait disabled:opacity-50"><RotateCcw size={16}/></button></div></article>) : <div className="py-10 text-center text-sm text-[#9a9e96]">還沒有記帳紀錄，新增第一筆吧 ☺</div>}
            </div>
          </section>
        </div>
      </section>
      <footer className="py-8 text-center text-xs text-[#a0a49d]">慢慢記錄，慢慢靠近理想的生活 ☺</footer>
    </div>
  </main>
}

function Metric({ label, amount, icon, tone }) {
  const colors = { sage: 'bg-[#eaf0e6] text-[#536d54]', peach: 'bg-[#f8ede5] text-[#b77953]', cream: 'bg-[#f2f0e8] text-[#777254]' }
  return <div className="rounded-[24px] border border-[#e7e8e2] bg-white p-5 sm:p-6"><div className={`mb-4 flex h-9 w-9 items-center justify-center rounded-xl ${colors[tone]}`}>{icon}</div><p className="text-xs text-[#81867e] sm:text-sm">{label}</p><p className="mt-2 text-lg font-semibold tracking-tight sm:text-2xl">NT$ {money(amount)}</p></div>
}
