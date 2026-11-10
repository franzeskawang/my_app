// Expense endpoint functions; request and response types come from FastAPI OpenAPI.
import type { paths } from '../../shared/api/generated'
import { request } from '../../platform/web/httpTransport'

type DashboardResponse = paths['/api/dashboard']['get']['responses'][200]['content']['application/json']
type SubmissionRequest = paths['/api/expenses']['post']['requestBody']['content']['application/json']
type SubmissionResponse = paths['/api/expenses']['post']['responses'][200]['content']['application/json']
type DeleteResponse = paths['/api/expenses/{expense_id}']['delete']['responses'][200]['content']['application/json']

export const expenseApi = {
  getDashboard: () => request<DashboardResponse>('/api/dashboard'),
  createExpenses: (submission: SubmissionRequest) => request<SubmissionResponse>('/api/expenses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(submission),
  }),
  deleteExpense: (expenseId: number) => request<DeleteResponse>(`/api/expenses/${expenseId}`, { method: 'DELETE' }),
}
