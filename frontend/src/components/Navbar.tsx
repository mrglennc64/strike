import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

export const Navbar: React.FC = () => {
  const logout = useAuthStore((state) => state.logout)
  const navigate = useNavigate()
  const [verticalDropdown, setVerticalDropdown] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const verticals = [
    { name: 'MLB', path: '/verticals/mlb' },
    { name: 'AI/Tech', path: '/verticals/ai' },
    { name: 'Economics', path: '/verticals/economics' },
    { name: 'Earnings', path: '/verticals/earnings' },
    { name: 'Crypto', path: '/verticals/crypto' },
  ]

  return (
    <nav className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link to="/dashboard" className="text-white font-bold text-lg">
              StrikeHub
            </Link>
            <div className="hidden md:flex space-x-1">
              <Link to="/dashboard" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Home
              </Link>

              <div className="relative group">
                <button
                  onClick={() => setVerticalDropdown(!verticalDropdown)}
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium flex items-center"
                >
                  Verticals
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </button>
                {verticalDropdown && (
                  <div className="absolute left-0 mt-0 w-48 bg-gray-700 rounded-md shadow-lg py-1 z-10">
                    {verticals.map((vertical) => (
                      <Link
                        key={vertical.path}
                        to={vertical.path}
                        className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-600 text-sm"
                        onClick={() => setVerticalDropdown(false)}
                      >
                        {vertical.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              <Link to="/portfolio" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Portfolio
              </Link>

              <Link to="/clv-tracker" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                CLV Tracker
              </Link>

              <Link to="/positions" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Positions
              </Link>

              <Link to="/audit" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Audit
              </Link>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}
