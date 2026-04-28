"use client"
import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import Navbar from "../components/Navbar"

interface Professor {
  id: string
  name: string
  university: string
  department: string
  email: string
  interests: string
  city: string
  state: string
}

const DEPARTMENTS = [
  "Computer Science", "Electrical Engineering", "Physics", "Mathematics",
  "Biology", "Chemistry", "Economics", "Psychology", "Neuroscience", "Data Science"
]

export default function SearchPage() {
  const { status } = useSession()
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [department, setDepartment] = useState("")
  const [range, setRange] = useState(50)
  const [professors, setProfessors] = useState<Professor[]>([])
  const [loading, setLoading] = useState(false)
  const [trackedIds, setTrackedIds] = useState<Set<string>>(new Set())
  const [addedFeedback, setAddedFeedback] = useState<string | null>(null)

  useEffect(() => {
    if (status === "unauthenticated") router.push("/")
  }, [status, router])

  useEffect(() => {
    if (status === "authenticated") {
      fetchTracked()
      fetchProfessors("", "", 50)
    }
  }, [status])

  async function fetchTracked() {
    const res = await fetch("/api/tracked")
    if (res.ok) {
      const data = await res.json()
      setTrackedIds(new Set(data.map((t: { professorId: string }) => t.professorId)))
    }
  }

  async function fetchProfessors(q: string, dept: string, r: number) {
    setLoading(true)
    const params = new URLSearchParams()
    if (q) params.set("q", q)
    if (dept) params.set("department", dept)
    params.set("range", r.toString())
    const res = await fetch(`/api/professors/search?${params}`)
    if (res.ok) setProfessors(await res.json())
    setLoading(false)
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    fetchProfessors(query, department, range)
  }

  async function addToList(professorId: string) {
    const res = await fetch("/api/tracked", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ professorId })
    })
    if (res.ok) {
      setTrackedIds(prev => new Set(Array.from(prev).concat(professorId)))
      setAddedFeedback(professorId)
      setTimeout(() => setAddedFeedback(null), 2000)
    }
  }

  if (status === "loading") return <div style={{ backgroundColor: "#ffffff", minHeight: "100vh" }} />

  return (
    <div style={{ backgroundColor: "#ffffff", minHeight: "100vh" }}>
      <Navbar />
      <main style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 16px" }}>
        <h1 style={{ color: "#24292f", fontSize: "24px", fontWeight: "600", marginBottom: "24px" }}>Search Professors</h1>

        <form onSubmit={handleSearch} style={{ backgroundColor: "#f6f8fa", border: "1px solid #d0d7de", borderRadius: "6px", padding: "20px", marginBottom: "24px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 200px 200px auto", gap: "12px", alignItems: "end" }}>
            <div>
              <label style={{ display: "block", color: "#57606a", fontSize: "12px", marginBottom: "6px" }}>University, city, or professor name</label>
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="e.g. MIT, Boston, Stanford..."
                style={{ width: "100%", padding: "8px 12px", backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", color: "#24292f", fontSize: "14px" }}
              />
            </div>
            <div>
              <label style={{ display: "block", color: "#57606a", fontSize: "12px", marginBottom: "6px" }}>Department</label>
              <select value={department} onChange={e => setDepartment(e.target.value)} style={{ width: "100%", padding: "8px 12px", backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", color: "#24292f", fontSize: "14px" }}>
                <option value="">All Departments</option>
                {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: "block", color: "#57606a", fontSize: "12px", marginBottom: "6px" }}>Range: {range} miles</label>
              <input
                type="range"
                min="10"
                max="500"
                step="10"
                value={range}
                onChange={e => setRange(parseInt(e.target.value))}
                style={{ width: "100%", accentColor: "#1a7f37" } as React.CSSProperties}
              />
            </div>
            <button type="submit" style={{ padding: "8px 20px", backgroundColor: "#1a7f37", border: "1px solid rgba(27,31,36,0.15)", borderRadius: "6px", color: "#ffffff", fontSize: "14px", fontWeight: "600", whiteSpace: "nowrap" as const }}>
              Search
            </button>
          </div>
          <p style={{ color: "#57606a", fontSize: "12px", marginTop: "12px", marginBottom: 0 }}>
            Tip: Search by city name (e.g. &quot;Boston&quot;, &quot;San Francisco&quot;) to find professors within the specified range. Range only applies to city searches.
          </p>
        </form>

        {loading ? (
          <div style={{ textAlign: "center", padding: "48px", color: "#57606a" }}>Loading...</div>
        ) : (
          <>
            <p style={{ color: "#57606a", fontSize: "14px", marginBottom: "16px" }}>{professors.length} professor{professors.length !== 1 ? "s" : ""} found</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "16px" }}>
              {professors.map(prof => (
                <ProfessorCard
                  key={prof.id}
                  professor={prof}
                  isTracked={trackedIds.has(prof.id)}
                  justAdded={addedFeedback === prof.id}
                  onAdd={() => addToList(prof.id)}
                />
              ))}
            </div>
            {professors.length === 0 && (
              <div style={{ textAlign: "center", padding: "48px", color: "#57606a" }}>No professors found. Try a different search.</div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

function ProfessorCard({ professor, isTracked, justAdded, onAdd }: {
  professor: Professor
  isTracked: boolean
  justAdded: boolean
  onAdd: () => void
}) {
  const interests = professor.interests.split(",").map(i => i.trim())

  return (
    <div style={{ backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h3 style={{ color: "#24292f", fontSize: "16px", fontWeight: "600", margin: 0 }}>{professor.name}</h3>
          <p style={{ color: "#57606a", fontSize: "13px", margin: "2px 0 0" }}>{professor.university}</p>
        </div>
        <span style={{ backgroundColor: "#f6f8fa", border: "1px solid #d0d7de", borderRadius: "20px", padding: "2px 8px", color: "#57606a", fontSize: "12px", whiteSpace: "nowrap" as const }}>
          {professor.department}
        </span>
      </div>
      
      <div>
        <p style={{ color: "#57606a", fontSize: "12px", margin: "0 0 4px", display: "flex", alignItems: "center", gap: "4px" }}>
          <svg height="12" viewBox="0 0 16 16" fill="#57606a"><path d="M1.75 2h12.5c.966 0 1.75.784 1.75 1.75v8.5A1.75 1.75 0 0114.25 14H1.75A1.75 1.75 0 010 12.25v-8.5C0 2.784.784 2 1.75 2zM1.5 12.251c0 .138.112.25.25.25h12.5a.25.25 0 00.25-.25V5.809L8.38 9.397a.75.75 0 01-.76 0L1.5 5.809v6.442zm13-8.181L8 7.88 1.5 4.07v-.32a.25.25 0 01.25-.25h12.5a.25.25 0 01.25.25v.32z"/></svg>
          {professor.email}
        </p>
        <p style={{ color: "#57606a", fontSize: "12px", margin: 0, display: "flex", alignItems: "center", gap: "4px" }}>
          <svg height="12" viewBox="0 0 16 16" fill="#57606a"><path d="M8 0a8 8 0 100 16A8 8 0 008 0zm.75 11.25v.75a.75.75 0 01-1.5 0v-.75a.75.75 0 011.5 0zM8 4.5a1 1 0 100 2 1 1 0 000-2zm0 3.5a.75.75 0 01.75.75v2a.75.75 0 01-1.5 0v-2A.75.75 0 018 8z"/></svg>
          {professor.city}, {professor.state}
        </p>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
        {interests.slice(0, 3).map(interest => (
          <span key={interest} style={{ backgroundColor: "#ddf4ff", border: "1px solid #54aeff", borderRadius: "20px", padding: "2px 8px", color: "#0969da", fontSize: "11px" }}>
            {interest}
          </span>
        ))}
      </div>

      <button
        onClick={onAdd}
        disabled={isTracked}
        style={{
          padding: "6px 16px",
          backgroundColor: isTracked ? "#f6f8fa" : justAdded ? "#2da44e" : "#1a7f37",
          border: `1px solid ${isTracked ? "#d0d7de" : "rgba(27,31,36,0.15)"}`,
          borderRadius: "6px",
          color: isTracked ? "#57606a" : "#ffffff",
          fontSize: "14px",
          fontWeight: "500",
          marginTop: "auto",
          transition: "background-color 0.2s"
        }}
      >
        {isTracked ? "✓ In your list" : justAdded ? "✓ Added!" : "+ Add to List"}
      </button>
    </div>
  )
}
