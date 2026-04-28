import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "../../../../lib/auth"
import { prisma } from "../../../../lib/prisma"

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 3959
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

const CITY_COORDS: Record<string, [number, number]> = {
  "new york": [40.7128, -74.0060],
  "los angeles": [34.0522, -118.2437],
  "chicago": [41.8781, -87.6298],
  "houston": [29.7604, -95.3698],
  "phoenix": [33.4484, -112.0740],
  "philadelphia": [39.9526, -75.1652],
  "san antonio": [29.4241, -98.4936],
  "san diego": [32.7157, -117.1611],
  "dallas": [32.7767, -96.7970],
  "san francisco": [37.7749, -122.4194],
  "austin": [30.2672, -97.7431],
  "seattle": [47.6062, -122.3321],
  "denver": [39.7392, -104.9903],
  "boston": [42.3601, -71.0589],
  "atlanta": [33.7490, -84.3880],
  "miami": [25.7617, -80.1918],
  "minneapolis": [44.9778, -93.2650],
  "portland": [45.5051, -122.6750],
  "cambridge": [42.3736, -71.1097],
  "pasadena": [34.1478, -118.1445],
  "stanford": [37.4275, -122.1697],
  "berkeley": [37.8716, -122.2727],
  "princeton": [40.3573, -74.6672],
  "pittsburgh": [40.4406, -79.9959],
  "evanston": [42.0450, -87.6877],
  "ann arbor": [42.2808, -83.7430],
  "new haven": [41.3082, -72.9279],
}

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const { searchParams } = new URL(req.url)
  const query = searchParams.get("q")?.toLowerCase() || ""
  const department = searchParams.get("department") || ""
  const range = parseInt(searchParams.get("range") || "50")

  const cityCoords = query ? CITY_COORDS[query] : null

  // Geo searches: apply haversine in JS (small dataset, no geo extension in SQLite)
  if (cityCoords) {
    const where = department ? { department } : {}
    const all = await prisma.professor.findMany({ where })
    const professors = all.filter(p =>
      haversine(cityCoords[0], cityCoords[1], p.latitude, p.longitude) <= range
    )
    return NextResponse.json(professors)
  }

  // Text / department searches: push filtering to the DB
  const where: Record<string, unknown> = {}
  if (department) where.department = department
  if (query) {
    where.OR = [
      { university: { contains: query } },
      { city: { contains: query } },
      { name: { contains: query } },
    ]
  }

  const professors = await prisma.professor.findMany({ where })
  return NextResponse.json(professors)
}
