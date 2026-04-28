import { NextRequest, NextResponse } from "next/server"
import bcrypt from "bcryptjs"
import { prisma } from "../../../../lib/prisma"

export async function POST(req: NextRequest) {
  const { email, name, password } = await req.json()
  
  if (!email || !name || !password) {
    return NextResponse.json({ error: "All fields required" }, { status: 400 })
  }
  
  const existing = await prisma.user.findUnique({ where: { email } })
  if (existing) {
    return NextResponse.json({ error: "Email already registered" }, { status: 400 })
  }
  
  const hashed = await bcrypt.hash(password, 12)
  const user = await prisma.user.create({
    data: { email, name, password: hashed }
  })
  
  return NextResponse.json({ id: user.id, email: user.email, name: user.name })
}
