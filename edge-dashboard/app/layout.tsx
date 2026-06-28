import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'Edge AI - Multi-Vertical Prediction Platform',
  description: 'AI-powered prediction platform across multiple verticals: AI Releases, Economics, Earnings, Crypto, and MLB',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-trading-bg text-trading-text">
        <Navbar />
        {children}
      </body>
    </html>
  )
}
