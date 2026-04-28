import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "./providers"

export const metadata: Metadata = {
  title: "ProfessorTracker",
  description: "Track professors for PhD applications",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif', backgroundColor: "#ffffff", color: "#24292f" }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
