import type { Insight, Preference, RestaurantTable, TableStatus, WaitlistEntry, WaitlistStatus } from './types'

type NewEntry = Pick<WaitlistEntry, 'name' | 'phone' | 'email' | 'partySize' | 'preference' | 'requirements' | 'notes'>
type ApiWaitlistEntry = {
  id: string; reference: string; customer_name: string; phone_number: string; email?: string; party_size: number
  seating_preference: Preference; special_requirements?: string; notes?: string; joined_at: string
  estimated_wait_minutes: number; status: WaitlistStatus; notified_at?: string; seated_at?: string; table_id?: string
}
type ApiTable = { id: string; name: string; minimum_capacity: number; maximum_capacity: number; location: string; status: TableStatus }
const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

const toEntry = (item: ApiWaitlistEntry): WaitlistEntry => ({
  id: item.id, reference: item.reference, name: item.customer_name, phone: item.phone_number, email: item.email,
  partySize: item.party_size, preference: item.seating_preference, requirements: item.special_requirements,
  notes: item.notes, joinedAt: item.joined_at, estimatedWait: item.estimated_wait_minutes, status: item.status,
  notifiedAt: item.notified_at, seatedAt: item.seated_at, tableId: item.table_id,
})
const toTable = (item: ApiTable): RestaurantTable => ({
  id: item.id, name: item.name, minimumCapacity: item.minimum_capacity, maximumCapacity: item.maximum_capacity,
  location: item.location, status: item.status,
})

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.error?.message || `Request failed (${response.status})`)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}

// This service is the single UI boundary to the FastAPI /api/v1 backend.
export const waitlistApi = {
  async dashboard() {
    const [entries, tables] = await Promise.all([
      request<ApiWaitlistEntry[]>('/waitlist'), request<ApiTable[]>('/tables'),
    ])
    return { entries: entries.map(toEntry), tables: tables.map(toTable) }
  },
  async addEntry(input: NewEntry) {
    const entry = await request<ApiWaitlistEntry>('/waitlist', {
      method: 'POST', body: JSON.stringify({
        customer_name: input.name, phone_number: input.phone, email: input.email, party_size: input.partySize,
        seating_preference: input.preference, special_requirements: input.requirements, notes: input.notes,
      }),
    })
    return toEntry(entry)
  },
  async setStatus(id: string, status: WaitlistStatus) {
    const paths: Partial<Record<WaitlistStatus, string>> = { NOTIFIED: 'notify', CONFIRMED: 'confirm', CANCELLED: 'cancel' }
    if (!paths[status]) throw new Error(`The frontend cannot set status ${status} directly.`)
    return toEntry(await request<ApiWaitlistEntry>(`/waitlist/${id}/${paths[status]}`, { method: 'POST' }))
  },
  async seat(id: string, tableId: string) {
    return toEntry(await request<ApiWaitlistEntry>(`/waitlist/${id}/seat`, { method: 'POST', body: JSON.stringify({ table_id: tableId }) }))
  },
  async updateTable(id: string, status: TableStatus) {
    return toTable(await request<ApiTable>(`/tables/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }))
  },
  async insight(): Promise<Insight> {
    const data = await request<{ insight: string; recommendation: string }>('/ai/insights')
    return { title: "Tonight's pulse", body: data.insight, action: data.recommendation }
  },
}

export const preferences: Preference[] = ['ANY', 'INDOOR', 'OUTDOOR', 'BAR', 'BOOTH', 'WINDOW']
