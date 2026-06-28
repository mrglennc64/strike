'use client'

import { Card } from '@/components/Card'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface BankrollProps {
  total?: number
  available?: number
  allocated?: number
  currency?: string
}

export function Bankroll({
  total = 100000,
  available = 75000,
  allocated = 25000,
  currency = 'USD',
}: BankrollProps) {
  const allocationPercentage = (allocated / total) * 100

  return (
    <Card>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-trading-text">Bankroll</h3>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400 text-sm">Total Bankroll</span>
              <span className="text-trading-text font-semibold">
                ${total.toLocaleString()} {currency}
              </span>
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400 text-sm">Available</span>
              <span className="text-trading-success font-semibold">
                ${available.toLocaleString()} {currency}
              </span>
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400 text-sm">Allocated</span>
              <span className="text-trading-accent font-semibold">
                ${allocated.toLocaleString()} {currency}
              </span>
            </div>
            <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-trading-accent to-blue-500"
                style={{ width: `${allocationPercentage}%` }}
              ></div>
            </div>
            <p className="text-gray-500 text-xs mt-1">
              {allocationPercentage.toFixed(1)}% allocated
            </p>
          </div>
        </div>

        <button className="trading-btn-secondary w-full py-2 mt-4 text-sm">
          Adjust Allocation
        </button>
      </div>
    </Card>
  )
}
