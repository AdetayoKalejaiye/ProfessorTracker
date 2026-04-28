# ProfessorTracker

A GitHub-styled web app for searching professors and tracking your outreach status.

## Features

- **Sign up / Sign in** – credential-based accounts
- **Search Professors** – search by university name, city name (with distance range), or professor name; filter by department
- **Professor Cards** – shows name, university, department, email, city/state, and research interests
- **My List** – add professors to a personal tracking list
- **Email Status Tracking** – mark each as Not Contacted, Emailed, Answered, Rejected, or Pending
- **Inline Notes** – click to edit freeform notes per professor

## Tech Stack

- **Next.js 14** (App Router, TypeScript)
- **Prisma** + **SQLite** for the database
- **NextAuth.js v4** with credentials provider (bcryptjs for password hashing)
- **Tailwind CSS** + GitHub dark theme

## Getting Started

```bash
# 1. Install dependencies
npm install

# 2. Copy env file and set your secret
cp .env.example .env

# 3. Push DB schema and seed professors
npx prisma db push
npx prisma db seed

# 4. Start the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Database

The seed script populates ~51 professors across 15 universities (MIT, Stanford, Harvard, Carnegie Mellon, UC Berkeley, Caltech, Princeton, Yale, Columbia, University of Michigan, Georgia Tech, UT Austin, UCLA, NYU, Northwestern) in departments including Computer Science, Electrical Engineering, Physics, Mathematics, Biology, Chemistry, Economics, Psychology, Neuroscience, and Data Science.
