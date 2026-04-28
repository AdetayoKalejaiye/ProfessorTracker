import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "../../../lib/auth"
import { prisma } from "../../../lib/prisma"

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const userId = (session.user as { id?: string }).id
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const tracked = await prisma.trackedProfessor.findMany({
    where: { userId },
    include: { professor: true },
    orderBy: { createdAt: "desc" }
  })
  return NextResponse.json(tracked)
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const userId = (session.user as { id?: string }).id
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const { professorId } = await req.json()
  
  const tracked = await prisma.trackedProfessor.upsert({
    where: { userId_professorId: { userId, professorId } },
    update: {},
    create: { userId, professorId }
  })
  return NextResponse.json(tracked)
}

export async function PATCH(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const userId = (session.user as { id?: string }).id
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const { id, status, notes } = await req.json()
  
  const tracked = await prisma.trackedProfessor.update({
    where: { id, userId },
    data: { ...(status && { status }), ...(notes !== undefined && { notes }) }
  })
  return NextResponse.json(tracked)
}

export async function DELETE(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const userId = (session.user as { id?: string }).id
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const { id } = await req.json()
  await prisma.trackedProfessor.delete({ where: { id, userId } })
  return NextResponse.json({ success: true })
}
