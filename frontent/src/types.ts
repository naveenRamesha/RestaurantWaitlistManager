export type WaitlistStatus = 'WAITING' | 'NOTIFIED' | 'CONFIRMED' | 'SEATED' | 'CANCELLED'
export type TableStatus = 'AVAILABLE' | 'OCCUPIED' | 'CLEANING' | 'OUT_OF_SERVICE'
export type Preference = 'ANY' | 'INDOOR' | 'OUTDOOR' | 'BAR' | 'BOOTH' | 'WINDOW'

export interface WaitlistEntry {
  id: string
  reference: string
  name: string
  phone: string
  email?: string
  partySize: number
  preference: Preference
  requirements?: string
  notes?: string
  joinedAt: string
  estimatedWait: number
  status: WaitlistStatus
  notifiedAt?: string
  seatedAt?: string
  tableId?: string
}

export interface RestaurantTable {
  id: string
  name: string
  minimumCapacity: number
  maximumCapacity: number
  location: string
  status: TableStatus
}

export interface Insight {
  title: string
  body: string
  action: string
}
