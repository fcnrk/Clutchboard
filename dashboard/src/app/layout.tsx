import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Clutchboard',
  description: 'CS2 Server Stats Tracker',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
          <Link href="/" className="font-bold text-orange-400 hover:text-orange-300 text-lg">
            Clutchboard
          </Link>
          <Link href="/" className="text-gray-300 hover:text-white text-sm">Leaderboard</Link>
          <Link href="/matches" className="text-gray-300 hover:text-white text-sm">Matches</Link>
          <Link href="/weapons" className="text-gray-300 hover:text-white text-sm">Weapons</Link>
          <Link href="/head-to-head" className="text-gray-300 hover:text-white text-sm">H2H</Link>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  )
}
