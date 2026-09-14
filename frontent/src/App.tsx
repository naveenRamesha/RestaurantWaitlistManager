import { FormEvent, useEffect, useMemo, useState } from 'react'
import { preferences, waitlistApi } from './api'
import type { Insight, Preference, RestaurantTable, TableStatus, WaitlistEntry } from './types'

const statusLabel: Record<string, string> = { WAITING: 'Waiting', NOTIFIED: 'Notified', CONFIRMED: 'Ready', AVAILABLE: 'Available', OCCUPIED: 'Occupied', CLEANING: 'Cleaning', OUT_OF_SERVICE: 'Out of service' }
const clock = (date: string) => `${Math.max(0, Math.floor((Date.now() - new Date(date).getTime()) / 60_000))}m`
const preference = (value: string) => value === 'ANY' ? 'No preference' : value[0] + value.slice(1).toLowerCase()
const initials = (name: string) => name.split(' ').map(part => part[0]).join('').slice(0, 2)

export default function App() {
  const [entries, setEntries] = useState<WaitlistEntry[]>([])
  const [tables, setTables] = useState<RestaurantTable[]>([])
  const [insight, setInsight] = useState<Insight | null>(null)
  const [tab, setTab] = useState<'dashboard' | 'history'>('dashboard')
  const [query, setQuery] = useState('')
  const [modal, setModal] = useState<'add' | 'seat' | null>(null)
  const [selectedTable, setSelectedTable] = useState<RestaurantTable | null>(null)
  const [toast, setToast] = useState('')
  const [loading, setLoading] = useState(true)
  const [connectionError, setConnectionError] = useState('')

  const refresh = async () => {
    try {
      const data = await waitlistApi.dashboard()
      setEntries(data.entries); setTables(data.tables); setConnectionError('')
    } catch (error) {
      setConnectionError(error instanceof Error ? error.message : 'Unable to reach the backend.')
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { refresh(); waitlistApi.insight().then(setInsight).catch(() => undefined) }, [])
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 3200); return () => clearTimeout(timer) }, [toast])
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === 'a' && !event.metaKey && !event.ctrlKey && !['INPUT', 'TEXTAREA', 'SELECT'].includes((event.target as HTMLElement).tagName)) setModal('add')
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const activeEntries = entries.filter(entry => !['SEATED', 'CANCELLED'].includes(entry.status))
  const historicalEntries = entries.filter(entry => ['SEATED', 'CANCELLED'].includes(entry.status))
  const displayed = (tab === 'dashboard' ? activeEntries : historicalEntries).filter(entry => [entry.name, entry.phone, entry.reference].join(' ').toLowerCase().includes(query.toLowerCase()))
  const available = tables.filter(table => table.status === 'AVAILABLE')
  const recommended = activeEntries.filter(entry => entry.status === 'CONFIRMED').sort((a, b) => new Date(a.joinedAt).getTime() - new Date(b.joinedAt).getTime())[0]
  const averageWait = activeEntries.length ? Math.round(activeEntries.reduce((total, entry) => total + Math.floor((Date.now() - new Date(entry.joinedAt).getTime()) / 60_000), 0) / activeEntries.length) : 0

  async function updateStatus(entry: WaitlistEntry, status: 'NOTIFIED' | 'CONFIRMED' | 'CANCELLED') {
    await waitlistApi.setStatus(entry.id, status); await refresh()
    setToast(status === 'NOTIFIED' ? `Table-ready notification sent to ${entry.name}.` : status === 'CANCELLED' ? `${entry.name} was removed from the queue.` : `${entry.name} is ready to be seated.`)
  }
  async function changeTableStatus(table: RestaurantTable, status: TableStatus) {
    await waitlistApi.updateTable(table.id, status); await refresh(); setToast(`${table.name} is now ${statusLabel[status].toLowerCase()}.`)
  }
  function openSeat(table: RestaurantTable) { setSelectedTable(table); setModal('seat') }

  if (loading) return <div className="loader"><span>V</span> Loading floor service…</div>
  if (connectionError && !entries.length && !tables.length) return <div className="connection-screen"><div className="brand-mark">V</div><p className="section-kicker">BACKEND CONNECTION</p><h1>We can’t reach floor service.</h1><p>{connectionError}</p><code>http://127.0.0.1:8000/api/v1</code><button className="add-button" onClick={() => { setLoading(true); refresh() }}>Retry connection <span>→</span></button></div>
  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">V</div><div>verde<span>host</span></div></div>
      <div className="venue"><span className="venue-dot" /> The Garden Room <span className="chevron">⌄</span></div>
      <nav aria-label="Primary navigation">
        <button className={tab === 'dashboard' ? 'nav-item active' : 'nav-item'} onClick={() => setTab('dashboard')}><span>▦</span> Live floor <b>{activeEntries.length}</b></button>
        <button className={tab === 'history' ? 'nav-item active' : 'nav-item'} onClick={() => setTab('history')}><span>◷</span> History</button>
        <button className="nav-item"><span>◫</span> Reports <em>soon</em></button>
      </nav>
      <div className="sidebar-foot"><div className="host-avatar">SA</div><div><strong>Sam Adams</strong><small>Floor manager</small></div><button aria-label="Settings">⚙</button></div>
    </aside>

    <section className="content">
      <header className="topbar"><div><p className="eyebrow">MONDAY, OCTOBER 14 · DINNER SERVICE</p><h1>{tab === 'dashboard' ? 'Good evening, Sam.' : 'Waitlist history'}</h1></div><div className="top-actions"><button className="icon-button" aria-label="Notifications">♧<i /></button><button className="help-button">?</button><button className="add-button" onClick={() => setModal('add')}><strong>+</strong> Add party <kbd>A</kbd></button></div></header>

      {tab === 'dashboard' && <>
        <section className="metrics" aria-label="Current metrics">
          <Metric label="Waiting now" value={String(activeEntries.filter(x => x.status === 'WAITING').length)} detail={`${activeEntries.reduce((sum, x) => sum + (x.status === 'WAITING' ? x.partySize : 0), 0)} guests in queue`} tone="forest" />
          <Metric label="Average wait" value={`${averageWait} min`} detail="↓ 3 min vs. last Monday" tone="sage" />
          <Metric label="Longest wait" value={`${Math.max(0, ...activeEntries.map(x => Math.floor((Date.now() - new Date(x.joinedAt).getTime()) / 60_000)))} min`} detail="Maya Patel · party of 4" tone="sand" />
          <Metric label="Tables available" value={`${available.length} / ${tables.length}`} detail={`${tables.filter(x => x.status === 'OCCUPIED').length} occupied · ${tables.filter(x => x.status === 'CLEANING').length} cleaning`} tone="coral" />
        </section>

        <section className="workspace">
          <div className="queue-panel panel"><div className="panel-heading"><div><p className="section-kicker">LIVE QUEUE</p><h2>Waitlist <span>{activeEntries.length}</span></h2></div><div className="queue-tools"><label className="search"><span>⌕</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search guests" aria-label="Search guests" /></label><button className="filter-button">⇅ Filter</button></div></div>
            <div className="queue-header"><span>#</span><span>Guest</span><span>Party</span><span>Preference</span><span>Waited</span><span>ETA</span><span>Status</span><span /></div>
            <div className="queue-list">{displayed.length ? displayed.map((entry, index) => <QueueRow key={entry.id} entry={entry} position={index + 1} onNotify={() => updateStatus(entry, 'NOTIFIED')} onConfirm={() => updateStatus(entry, 'CONFIRMED')} onCancel={() => updateStatus(entry, 'CANCELLED')} />) : <div className="empty-state">No parties found.</div>}</div>
          </div>
          <div className="side-stack">
            <section className="recommendation"><div className="sparkle">✦</div><div><p className="section-kicker">SMART SEATING</p><h2>Best next move</h2></div><span className="confidence">HIGH CONFIDENCE</span>
              {recommended ? <><div className="recommend-guest"><div className="guest-avatar">{initials(recommended.name)}</div><div><strong>{recommended.name}</strong><p>Party of {recommended.partySize} · {clock(recommended.joinedAt)} waiting</p></div></div><p className="recommend-copy">{available.length ? `${available[0].name} fits their party and respects their ${preference(recommended.preference).toLowerCase()} preference.` : 'No suitable tables are free yet. Complete cleaning to unlock the next match.'}</p><button className="recommend-button" disabled={!available.length} onClick={() => available.length && openSeat(available[0])}>{available.length ? `Seat at ${available[0].name}` : 'Await a table'} <span>→</span></button></> : <p className="recommend-copy">The queue is clear. Great work keeping service flowing.</p>}
            </section>
            {insight && <section className="insight"><div className="insight-icon">↗</div><div><p className="section-kicker">AI FLOOR INSIGHT</p><h3>{insight.title}</h3><p>{insight.body}</p><button>{insight.action} <span>→</span></button></div></section>}
          </div>
        </section>

        <section className="tables-section"><div className="section-title"><div><p className="section-kicker">FLOOR PLAN</p><h2>Table status</h2></div><div className="legend"><span><i className="available" /> Available</span><span><i className="occupied" /> Occupied</span><span><i className="cleaning" /> Cleaning</span></div></div><div className="table-grid">{tables.map(table => <TableCard key={table.id} table={table} onSeat={() => openSeat(table)} onChange={status => changeTableStatus(table, status)} />)}</div></section>
      </>}

      {tab === 'history' && <section className="history panel"><div className="panel-heading"><div><p className="section-kicker">PAST PARTIES</p><h2>Completed & cancelled</h2></div><label className="search"><span>⌕</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by name, phone, or reference" /></label></div><div className="queue-header"><span>Ref.</span><span>Guest</span><span>Party</span><span>Preference</span><span>Joined</span><span>Table</span><span>Status</span><span /></div><div className="queue-list">{displayed.length ? displayed.map((entry, index) => <QueueRow key={entry.id} entry={entry} position={index + 1} historical onNotify={() => undefined} onConfirm={() => undefined} onCancel={() => undefined} />) : <div className="empty-state">No historical entries yet. Seat or cancel a party to see it here.</div>}</div></section>}
    </section>
    {modal === 'add' && <AddPartyModal onClose={() => setModal(null)} onSave={async input => { const entry = await waitlistApi.addEntry(input); await refresh(); setModal(null); setToast(`${entry.name} added · ${entry.reference} · ${entry.estimatedWait} min estimate.`) }} />}
    {modal === 'seat' && selectedTable && <SeatModal table={selectedTable} entries={activeEntries} onClose={() => setModal(null)} onSeat={async entry => { await waitlistApi.seat(entry.id, selectedTable.id); await refresh(); setModal(null); setToast(`${entry.name} is seated at ${selectedTable.name}.`) }} />}
    {toast && <div className="toast"><span>✓</span>{toast}</div>}
  </main>
}

function Metric({ label, value, detail, tone }: { label: string; value: string; detail: string; tone: string }) { return <article className={`metric ${tone}`}><p>{label}</p><h2>{value}</h2><small>{detail}</small></article> }

function QueueRow({ entry, position, historical, onNotify, onConfirm, onCancel }: { entry: WaitlistEntry; position: number; historical?: boolean; onNotify: () => void; onConfirm: () => void; onCancel: () => void }) {
  const actions = entry.status === 'WAITING' ? <><button onClick={onNotify}>Notify</button><button className="more" onClick={onCancel} aria-label="Cancel party">×</button></> : entry.status === 'NOTIFIED' ? <><button className="confirm" onClick={onConfirm}>Mark ready</button><button className="more" onClick={onCancel} aria-label="Cancel party">×</button></> : null
  return <div className="queue-row"><span className="position">{historical ? entry.reference : String(position).padStart(2, '0')}</span><div className="guest"><div className="guest-avatar small">{initials(entry.name)}</div><div><strong>{entry.name}</strong><small>{entry.phone}</small></div></div><span className="party-count">{entry.partySize} <small>ppl</small></span><span className="preference">{preference(entry.preference)}</span><span>{clock(entry.joinedAt)}</span><span>{entry.status === 'WAITING' ? `${entry.estimatedWait} min` : '—'}</span><span className={`badge ${entry.status.toLowerCase()}`}>{statusLabel[entry.status]}</span><div className="row-actions">{historical ? <span className="muted">{entry.tableId ? `Seated · ${entry.tableId.toUpperCase()}` : 'No table'} </span> : actions}</div></div>
}

function TableCard({ table, onSeat, onChange }: { table: RestaurantTable; onSeat: () => void; onChange: (status: TableStatus) => void }) {
  return <article className={`table-card ${table.status.toLowerCase()}`}><div className="table-top"><strong>{table.name}</strong><select aria-label={`Change ${table.name} status`} value={table.status} onChange={e => onChange(e.target.value as TableStatus)}><option value="AVAILABLE">Available</option><option value="OCCUPIED">Occupied</option><option value="CLEANING">Cleaning</option><option value="OUT_OF_SERVICE">Out of service</option></select></div><div className="table-shape"><span>{table.maximumCapacity}</span></div><p><strong>{table.minimumCapacity}–{table.maximumCapacity}</strong> covers · {table.location}</p>{table.status === 'AVAILABLE' ? <button onClick={onSeat}>Assign party <span>→</span></button> : <small className="table-state"><i /> {statusLabel[table.status]}</small>}</article>
}

function AddPartyModal({ onClose, onSave }: { onClose: () => void; onSave: (input: { name: string; phone: string; email?: string; partySize: number; preference: Preference; requirements?: string; notes?: string }) => Promise<void> }) {
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); const name = String(form.get('name') || '').trim(); const phone = String(form.get('phone') || '').trim(); const partySize = Number(form.get('partySize'))
    if (!name || !phone || !partySize || partySize < 1) { setError('Please add a guest name, phone number, and party size of at least one.'); return }
    setSaving(true); await onSave({ name, phone, email: String(form.get('email') || '') || undefined, partySize, preference: String(form.get('preference')) as Preference, requirements: String(form.get('requirements') || '') || undefined, notes: String(form.get('notes') || '') || undefined })
  }
  return <div className="modal-backdrop" role="presentation"><form className="modal" onSubmit={submit} aria-labelledby="add-party-title"><button type="button" className="close" onClick={onClose}>×</button><p className="section-kicker">NEW WAITLIST ENTRY</p><h2 id="add-party-title">Add a party</h2><p className="modal-lede">We’ll calculate an initial wait estimate and create a reference automatically.</p><div className="form-grid"><label className="wide">Guest name<input name="name" autoFocus placeholder="e.g. Jordan Lee" /></label><label>Phone number<input name="phone" placeholder="(555) 000-0000" inputMode="tel" /></label><label>Email <span>optional</span><input name="email" placeholder="jordan@email.com" type="email" /></label><label>Party size<select name="partySize" defaultValue="2">{[1,2,3,4,5,6,7,8].map(number => <option key={number}>{number}</option>)}</select></label><label>Seating preference<select name="preference" defaultValue="ANY">{preferences.map(item => <option key={item} value={item}>{preference(item)}</option>)}</select></label><label className="wide">Special requirements <span>optional</span><input name="requirements" placeholder="High chair, wheelchair access…" /></label><label className="wide">Host notes <span>optional</span><textarea name="notes" placeholder="Anything the floor team should know" rows={2} /></label></div>{error && <p className="form-error" role="alert">{error}</p>}<div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="add-button" disabled={saving}>{saving ? 'Adding…' : 'Add to waitlist'} <span>→</span></button></div></form></div>
}

function SeatModal({ table, entries, onClose, onSeat }: { table: RestaurantTable; entries: WaitlistEntry[]; onClose: () => void; onSeat: (entry: WaitlistEntry) => Promise<void> }) {
  const matches = useMemo(() => entries.filter(entry => entry.partySize <= table.maximumCapacity && entry.status === 'CONFIRMED').sort((a, b) => new Date(a.joinedAt).getTime() - new Date(b.joinedAt).getTime()), [entries, table])
  const [picked, setPicked] = useState(matches[0]?.id || ''); const entry = entries.find(item => item.id === picked); const [saving, setSaving] = useState(false)
  return <div className="modal-backdrop" role="presentation"><section className="modal seat-modal" aria-labelledby="seat-title"><button className="close" onClick={onClose}>×</button><p className="section-kicker">TABLE {table.name} · {table.minimumCapacity}–{table.maximumCapacity} COVERS</p><h2 id="seat-title">Choose a party to seat</h2><p className="modal-lede">Recommendations preserve the queue unless a table is a better fit.</p><div className="match-list">{matches.length ? matches.map((match, index) => <button key={match.id} className={picked === match.id ? 'match picked' : 'match'} onClick={() => setPicked(match.id)}><span className="match-order">{index === 0 ? '✦ Best fit' : `Option ${index + 1}`}</span><div className="guest-avatar small">{initials(match.name)}</div><div><strong>{match.name}</strong><p>Party of {match.partySize} · {clock(match.joinedAt)} waiting · {preference(match.preference)}</p></div><span className="radio" /></button>) : <div className="empty-state">No active parties fit this table.</div>}</div>{entry && <div className="assignment-note">{entry.preference === 'ANY' || table.location.toUpperCase().includes(entry.preference) ? 'Preference matched.' : 'Capacity is a fit; seating preference may not be exact.'}</div>}<div className="modal-actions"><button className="secondary" onClick={onClose}>Cancel</button><button className="add-button" disabled={!entry || saving} onClick={async () => { if (entry) { setSaving(true); await onSeat(entry) } }}>{saving ? 'Seating…' : `Seat ${entry?.name.split(' ')[0] || 'party'}`} <span>→</span></button></div></section></div>
}
