'use client'

import { Card } from '@/components/Card'
import { ChevronRight } from 'lucide-react'

interface LogEntry {
  id: string
  timestamp: string
  action: string
  vertical: string
  result?: string
  amount?: number
}

interface AuditLogProps {
  entries?: LogEntry[]
  limit?: number
}

const defaultEntries: LogEntry[] = [
  {
    id: '1',
    timestamp: '2026-06-28 14:32:15',
    action: 'Trade Executed',
    vertical: 'MLB',
    result: 'Win',
    amount: 1500,
  },
  {
    id: '2',
    timestamp: '2026-06-28 13:15:42',
    action: 'Prediction Made',
    vertical: 'Crypto',
    result: 'Pending',
    amount: 5000,
  },
  {
    id: '3',
    timestamp: '2026-06-28 11:45:20',
    action: 'Bankroll Adjusted',
    vertical: 'Economics',
    amount: 10000,
  },
  {
    id: '4',
    timestamp: '2026-06-28 10:20:05',
    action: 'Trade Executed',
    vertical: 'Earnings',
    result: 'Loss',
    amount: -800,
  },
  {
    id: '5',
    timestamp: '2026-06-27 16:30:00',
    action: 'Portfolio Rebalanced',
    vertical: 'All',
  },
]

function getResultColor(result?: string) {
  switch (result) {
    case 'Win':
      return 'text-trading-success'
    case 'Loss':
      return 'text-trading-danger'
    case 'Pending':
      return 'text-trading-warning'
    default:
      return 'text-gray-400'
  }
}

export function AuditLog({ entries = defaultEntries, limit = 5 }: AuditLogProps) {
  const displayEntries = entries.slice(0, limit)

  return (
    <Card>
      <h3 className="text-lg font-semibold text-trading-text mb-4">Audit Log</h3>

      <div className="space-y-2">
        {displayEntries.map((entry) => (
          <div
            key={entry.id}
            className="flex items-center justify-between p-3 bg-trading-bg rounded border border-trading-border hover:border-trading-accent/50 transition-colors cursor-pointer"
          >
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <div>
                  <p className="text-trading-text font-semibold text-sm">
                    {entry.action}
                  </p>
                  <p className="text-gray-500 text-xs">{entry.timestamp}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2 mt-1">
                <span className="inline-block px-2 py-1 bg-trading-accent/10 text-trading-accent text-xs rounded">
                  {entry.vertical}
                </span>
                {entry.result && (
                  <span className={`inline-block px-2 py-1 bg-gray-800 text-xs rounded ${getResultColor(entry.result)}`}>
                    {entry.result}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {entry.amount && (
                <span className={`font-semibold text-sm ${entry.amount > 0 ? 'text-trading-success' : 'text-trading-danger'}`}>
                  {entry.amount > 0 ? '+' : ''}{entry.amount.toLocaleString()}
                </span>
              )}
              <ChevronRight size={18} className="text-gray-500" />
            </div>
          </div>
        ))}
      </div>

      {entries.length > limit && (
        <button className="trading-btn-secondary w-full py-2 mt-4 text-sm">
          View All Transactions
        </button>
      )}
    </Card>
  )
}
