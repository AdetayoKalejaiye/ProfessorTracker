"use client"
import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Navbar from "../components/Navbar"

interface TrackedProfessor {
  id: string
  status: string
  notes: string
  professor: {
    id: string
    name: string
    university: string
    department: string
    email: string
    interests: string
    city: string
    state: string
  }
}

const STATUS_OPTIONS = ["NOT_CONTACTED", "EMAILED", "ANSWERED", "REJECTED", "PENDING"]

const STATUS_STYLES: Record<string, { bg: string; color: string; border: string; label: string }> = {
  NOT_CONTACTED: { bg: "#21262d", color: "#8b949e", border: "#30363d", label: "Not Contacted" },
  EMAILED: { bg: "#0c2d6b", color: "#58a6ff", border: "#1f6feb", label: "Emailed" },
  ANSWERED: { bg: "#0f2d1e", color: "#3fb950", border: "#238636", label: "Answered" },
  REJECTED: { bg: "#3d1a1a", color: "#f85149", border: "#da3633", label: "Rejected" },
  PENDING: { bg: "#2d2007", color: "#d29922", border: "#9e6a03", label: "Pending" },
}

export default function ListPage() {
  const { status } = useSession()
  const router = useRouter()
  const [tracked, setTracked] = useState<TrackedProfessor[]>([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState("")
  const [editingNotes, setEditingNotes] = useState<string | null>(null)
  const [notesDraft, setNotesDraft] = useState("")

  useEffect(() => {
    if (status === "unauthenticated") router.push("/")
  }, [status, router])

  useEffect(() => {
    if (status === "authenticated") fetchTracked()
  }, [status])

  async function fetchTracked() {
    setLoading(true)
    const res = await fetch("/api/tracked")
    if (res.ok) setTracked(await res.json())
    setLoading(false)
  }

  async function updateStatus(id: string, newStatus: string) {
    const res = await fetch("/api/tracked", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, status: newStatus })
    })
    if (res.ok) {
      setTracked(prev => prev.map(t => t.id === id ? { ...t, status: newStatus } : t))
    }
  }

  async function updateNotes(id: string, notes: string) {
    const res = await fetch("/api/tracked", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, notes })
    })
    if (res.ok) {
      setTracked(prev => prev.map(t => t.id === id ? { ...t, notes } : t))
      setEditingNotes(null)
    }
  }

  async function removeFromList(id: string) {
    const res = await fetch("/api/tracked", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id })
    })
    if (res.ok) setTracked(prev => prev.filter(t => t.id !== id))
  }

  const filtered = filterStatus ? tracked.filter(t => t.status === filterStatus) : tracked

  if (status === "loading") return <div style={{ backgroundColor: "#0d1117", minHeight: "100vh" }} />

  return (
    <div style={{ backgroundColor: "#0d1117", minHeight: "100vh" }}>
      <Navbar />
      <main style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <h1 style={{ color: "#e6edf3", fontSize: "24px", fontWeight: "600", margin: 0 }}>
            My Professors
            <span style={{ marginLeft: "12px", backgroundColor: "#21262d", border: "1px solid #30363d", borderRadius: "20px", padding: "2px 10px", fontSize: "14px", color: "#8b949e", fontWeight: "400" }}>
              {tracked.length}
            </span>
          </h1>
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            style={{ padding: "6px 12px", backgroundColor: "#21262d", border: "1px solid #30363d", borderRadius: "6px", color: "#e6edf3", fontSize: "14px" }}
          >
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.map(s => <option key={s} value={s}>{STATUS_STYLES[s].label}</option>)}
          </select>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "48px", color: "#8b949e" }}>Loading...</div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: "center", padding: "64px 16px", backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "6px" }}>
            <p style={{ color: "#8b949e", fontSize: "16px" }}>
              {tracked.length === 0 ? "You haven't added any professors yet." : "No professors match the selected filter."}
            </p>
            {tracked.length === 0 && (
              <button onClick={() => router.push("/search")} style={{ padding: "8px 20px", backgroundColor: "#238636", border: "1px solid rgba(240,246,252,0.1)", borderRadius: "6px", color: "#fff", fontSize: "14px", fontWeight: "600" }}>
                Search Professors
              </button>
            )}
          </div>
        ) : (
          <div style={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: "6px", overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" as const }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #30363d" }}>
                  {["Professor", "University", "Department", "Email", "Status", "Notes", ""].map(h => (
                    <th key={h} style={{ padding: "12px 16px", textAlign: "left" as const, color: "#8b949e", fontSize: "12px", fontWeight: "600", textTransform: "uppercase" as const, letterSpacing: "0.05em" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((item, idx) => {
                  const style = STATUS_STYLES[item.status] || STATUS_STYLES.NOT_CONTACTED
                  return (
                    <tr key={item.id} style={{ borderBottom: "1px solid #21262d", backgroundColor: idx % 2 === 0 ? "transparent" : "#0d111780" }}>
                      <td style={{ padding: "12px 16px" }}>
                        <span style={{ color: "#e6edf3", fontSize: "14px", fontWeight: "500" }}>{item.professor.name}</span>
                      </td>
                      <td style={{ padding: "12px 16px", color: "#8b949e", fontSize: "14px" }}>{item.professor.university}</td>
                      <td style={{ padding: "12px 16px", color: "#8b949e", fontSize: "14px" }}>{item.professor.department}</td>
                      <td style={{ padding: "12px 16px" }}>
                        <a href={`mailto:${item.professor.email}`} style={{ color: "#58a6ff", fontSize: "14px", textDecoration: "none" }}>{item.professor.email}</a>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <select
                          value={item.status}
                          onChange={e => updateStatus(item.id, e.target.value)}
                          style={{ padding: "4px 8px", backgroundColor: style.bg, border: `1px solid ${style.border}`, borderRadius: "20px", color: style.color, fontSize: "12px", fontWeight: "500" }}
                        >
                          {STATUS_OPTIONS.map(s => (
                            <option key={s} value={s}>{STATUS_STYLES[s].label}</option>
                          ))}
                        </select>
                      </td>
                      <td style={{ padding: "12px 16px", minWidth: "200px" }}>
                        {editingNotes === item.id ? (
                          <div style={{ display: "flex", gap: "6px" }}>
                            <input
                              type="text"
                              value={notesDraft}
                              onChange={e => setNotesDraft(e.target.value)}
                              onKeyDown={e => { if (e.key === "Enter") updateNotes(item.id, notesDraft); if (e.key === "Escape") setEditingNotes(null) }}
                              autoFocus
                              style={{ flex: 1, padding: "4px 8px", backgroundColor: "#0d1117", border: "1px solid #30363d", borderRadius: "6px", color: "#e6edf3", fontSize: "13px" }}
                            />
                            <button onClick={() => updateNotes(item.id, notesDraft)} style={{ padding: "4px 8px", backgroundColor: "#238636", border: "1px solid rgba(240,246,252,0.1)", borderRadius: "6px", color: "#fff", fontSize: "12px" }}>Save</button>
                            <button onClick={() => setEditingNotes(null)} style={{ padding: "4px 8px", backgroundColor: "#21262d", border: "1px solid #30363d", borderRadius: "6px", color: "#8b949e", fontSize: "12px" }}>✕</button>
                          </div>
                        ) : (
                          <span
                            onClick={() => { setEditingNotes(item.id); setNotesDraft(item.notes) }}
                            style={{ color: item.notes ? "#e6edf3" : "#484f58", fontSize: "13px", cursor: "pointer", display: "block", padding: "4px", borderRadius: "4px" }}
                            title="Click to edit"
                          >
                            {item.notes || "Add notes..."}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <button
                          onClick={() => removeFromList(item.id)}
                          style={{ padding: "4px 10px", backgroundColor: "transparent", border: "1px solid #da3633", borderRadius: "6px", color: "#f85149", fontSize: "12px" }}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
