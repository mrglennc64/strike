'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, X } from 'lucide-react'

const verticals = [
  { name: 'AI Releases', href: '/ai-releases' },
  { name: 'Economics', href: '/economics' },
  { name: 'Earnings', href: '/earnings' },
  { name: 'Crypto', href: '/crypto' },
  { name: 'MLB', href: '/mlb' },
]

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const isActive = (href: string) => pathname === href

  return (
    <nav className="border-b border-trading-border bg-trading-bg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-trading-accent rounded-lg flex items-center justify-center">
              <span className="text-trading-bg font-bold">E</span>
            </div>
            <span className="text-trading-accent font-bold text-lg hidden sm:inline">
              Edge AI
            </span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center space-x-1">
            {verticals.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive(item.href)
                    ? 'bg-trading-accent/10 text-trading-accent'
                    : 'text-gray-400 hover:text-trading-accent'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* User Menu */}
          <div className="hidden md:flex items-center space-x-4">
            <Link href="/dashboard" className="text-gray-400 hover:text-trading-accent text-sm">
              Dashboard
            </Link>
            <button className="trading-btn-secondary px-4 py-2 text-sm">
              Sign In
            </button>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden text-trading-accent"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="md:hidden pb-4">
            <div className="flex flex-col space-y-2">
              {verticals.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'bg-trading-accent/10 text-trading-accent'
                      : 'text-gray-400 hover:text-trading-accent'
                  }`}
                  onClick={() => setIsOpen(false)}
                >
                  {item.name}
                </Link>
              ))}
              <Link
                href="/dashboard"
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-400 hover:text-trading-accent"
                onClick={() => setIsOpen(false)}
              >
                Dashboard
              </Link>
              <button className="trading-btn-secondary px-3 py-2 text-sm w-full text-left">
                Sign In
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
