'use client'

import { useState } from 'react'
import { LogOut, User } from 'lucide-react'
import { Card } from '@/components/Card'

interface AuthenticationProps {
  user?: {
    name: string
    email: string
  }
}

export function Authentication({ user }: AuthenticationProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(!!user)

  if (!isAuthenticated) {
    return (
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-trading-text mb-2">
              Authentication Required
            </h3>
            <p className="text-gray-400 text-sm">
              Sign in to access this vertical
            </p>
          </div>
          <button className="trading-btn px-6 py-2">
            Sign In
          </button>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-full bg-trading-accent/20 flex items-center justify-center">
            <User size={20} className="text-trading-accent" />
          </div>
          <div>
            <p className="text-trading-text font-semibold">{user?.name}</p>
            <p className="text-gray-400 text-sm">{user?.email}</p>
          </div>
        </div>
        <button className="text-gray-400 hover:text-trading-accent transition-colors">
          <LogOut size={20} />
        </button>
      </div>
    </Card>
  )
}
