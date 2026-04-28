"use client"
import { useState } from "react"
import { signIn } from "next-auth/react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin")
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)

    if (mode === "signup") {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, password })
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error)
        setLoading(false)
        return
      }
    }

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false
    })

    if (result?.error) {
      setError("Invalid email or password")
      setLoading(false)
    } else {
      router.push("/search")
    }
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f6f8fa", display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
      <div style={{ width: "100%", maxWidth: "340px" }}>
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <svg height="48" viewBox="0 0 16 16" fill="#24292f" style={{ marginBottom: "12px" }}>
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          <h1 style={{ color: "#24292f", fontSize: "24px", fontWeight: "300", margin: 0 }}>ProfessorTracker</h1>
        </div>

        <div style={{ backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", padding: "24px" }}>
          <h2 style={{ color: "#24292f", fontSize: "20px", fontWeight: "400", textAlign: "center", marginTop: 0, marginBottom: "20px" }}>
            {mode === "signin" ? "Sign in" : "Create your account"}
          </h2>

          {error && (
            <div style={{ backgroundColor: "#ffebe9", border: "1px solid #ff8182", borderRadius: "6px", padding: "12px", marginBottom: "16px", color: "#d1242f", fontSize: "14px" }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {mode === "signup" && (
              <div>
                <label style={{ display: "block", color: "#24292f", fontSize: "14px", fontWeight: "600", marginBottom: "6px" }}>Name</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} required style={{ width: "100%", padding: "8px 12px", backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", color: "#24292f", fontSize: "14px" }} />
              </div>
            )}
            <div>
              <label style={{ display: "block", color: "#24292f", fontSize: "14px", fontWeight: "600", marginBottom: "6px" }}>Email address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ width: "100%", padding: "8px 12px", backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", color: "#24292f", fontSize: "14px" }} />
            </div>
            <div>
              <label style={{ display: "block", color: "#24292f", fontSize: "14px", fontWeight: "600", marginBottom: "6px" }}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: "100%", padding: "8px 12px", backgroundColor: "#ffffff", border: "1px solid #d0d7de", borderRadius: "6px", color: "#24292f", fontSize: "14px" }} />
            </div>
            <button type="submit" disabled={loading} style={{ width: "100%", padding: "9px 12px", backgroundColor: "#1a7f37", border: "1px solid rgba(27,31,36,0.15)", borderRadius: "6px", color: "#ffffff", fontSize: "14px", fontWeight: "600", marginTop: "4px" }}>
              {loading ? "Loading..." : mode === "signin" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>

        <div style={{ marginTop: "16px", border: "1px solid #d0d7de", borderRadius: "6px", padding: "16px", textAlign: "center", backgroundColor: "#ffffff" }}>
          {mode === "signin" ? (
            <span style={{ color: "#24292f", fontSize: "14px" }}>
              New to ProfessorTracker?{" "}
              <button onClick={() => setMode("signup")} style={{ background: "none", border: "none", color: "#0969da", cursor: "pointer", fontSize: "14px", padding: 0 }}>
                Create an account.
              </button>
            </span>
          ) : (
            <span style={{ color: "#24292f", fontSize: "14px" }}>
              Already have an account?{" "}
              <button onClick={() => setMode("signin")} style={{ background: "none", border: "none", color: "#0969da", cursor: "pointer", fontSize: "14px", padding: 0 }}>
                Sign in.
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
