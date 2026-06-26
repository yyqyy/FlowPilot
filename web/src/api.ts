import type { Task, TaskSummary } from './types'

// In dev the UI runs on Vite (5173) and the engine on 8765; in the packaged
// build the UI is served by the engine itself, so same-origin relative URLs.
const BASE = import.meta.env.DEV ? 'http://127.0.0.1:8765' : ''

export interface EngineStatus {
  running: string[]
  hotkeys: boolean
  log: string[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`)
  }
  return (await res.json()) as T
}

export const api = {
  status: () => request<EngineStatus>('/api/status'),
  listTasks: () => request<TaskSummary[]>('/api/tasks'),
  getTask: (id: string) => request<Task>(`/api/tasks/${id}`),
  createTask: (name: string) =>
    request<Task>('/api/tasks', { method: 'POST', body: JSON.stringify({ name }) }),
  saveTask: (task: Task) =>
    request<Task>(`/api/tasks/${task.id}`, { method: 'PUT', body: JSON.stringify(task) }),
  deleteTask: (id: string) => request<{ ok: boolean }>(`/api/tasks/${id}`, { method: 'DELETE' }),
  runTask: (id: string) => request<{ ok: boolean }>(`/api/tasks/${id}/run`, { method: 'POST' }),
  stopTask: (id: string) => request<{ ok: boolean }>(`/api/tasks/${id}/stop`, { method: 'POST' }),
  stopAll: () => request<{ ok: boolean }>('/api/stop', { method: 'POST' }),
}
