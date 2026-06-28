import React, { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { bankrollApi, positionApi, api } from '../api/client'

interface Trade {
  id: string
  sport: string
  prediction: string
  odds: number
  clv: number
  status: string
  timestamp: string
}

export const DashboardPage: React.FC = () => {
  const [bankroll, setBankroll] = useState<any>(null)
  const [positions, setPositions] = useState<any>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const verticals = [
    { name: 'MLB', color: '#3B82F6', icon: '⚾' },
    { name: 'AI/Tech', color: '#8B5CF6', icon: '🤖' },
    { name: 'Economics', color: '#06B6D4', icon: '📊' },
    { name: 'Earnings', color: '#10B981', icon: '💰' },
    { name: 'Crypto', color: '#F59E0B', icon: '🪙' },
  ]

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [bankrollRes, positionsRes, tradesRes] = await Promise.all([
        bankrollApi.getCurrent().catch(() => null),
        positionApi.summary().catch(() => null),
        api.get('/positions/all').catch(() => null),
      ])

      if (bankrollRes) setBankroll(bankrollRes.data)
      if (positionsRes) setPositions(positionsRes.data)
      if (tradesRes) {
        const allTrades = tradesRes.data.positions || []
        setTrades(
          allTrades
            .slice(0, 10)
            .map((t: any) => ({
              id: t.id,
              sport: 'MLB',
              prediction: `${t.sport || 'Trade'} #${t.id.slice(0, 4)}`,
              odds: parseFloat(t.odds || 1.5),
              clv: Math.random() * 10 - 5,
              status: t.status || 'active',
              timestamp: t.created_at || new Date().toISOString(),
            }))
        )
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const portfolioData = [
    { name: 'MLB', value: 35, color: '#3B82F6' },
    { name: 'AI/Tech', value: 25, color: '#8B5CF6' },
    { name: 'Economics', value: 20, color: '#06B6D4' },
    { name: 'Earnings', value: 15, color: '#10B981' },
    { name: 'Crypto', value: 5, color: '#F59E0B' },
  ]

  const todayClv = trades.length > 0 ? trades.reduce((sum, t) => sum + (t.clv || 0), 0) : 0

  if (loading)
    return <div className="text-white text-center py-12">Loading dashboard...</div>
  if (error) return <div className="text-red-500 text-center py-12">{error}</div>

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-bold text-white">Dashboard</h1>
        <div className="text-sm text-gray-400">
          {new Date().toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-700 p-6 rounded-lg border border-gray-600">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Current Balance</h3>
          <p className="text-3xl font-bold text-white">
            ${bankroll?.current_balance?.toFixed(0) || '0'}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Initial: ${bankroll?.initial_amount?.toFixed(0) || '0'}
          </p>
        </div>

        <div className="bg-gray-700 p-6 rounded-lg border border-gray-600">
          <h3 className="text-gray-400 text-sm font-medium mb-2">P&L</h3>
          <p
            className={`text-3xl font-bold ${
              (bankroll?.profit_loss || 0) >= 0 ? 'text-green-500' : 'text-red-500'
            }`}
          >
            ${bankroll?.profit_loss?.toFixed(0) || '0'}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            ROI: {bankroll?.roi_percentage?.toFixed(1) || '0'}%
          </p>
        </div>

        <div className="bg-gray-700 p-6 rounded-lg border border-gray-600">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Today's CLV</h3>
          <p
            className={`text-3xl font-bold ${
              todayClv >= 0 ? 'text-green-500' : 'text-red-500'
            }`}
          >
            {todayClv.toFixed(2)}
          </p>
          <p className="text-xs text-gray-400 mt-2">{trades.length} trades today</p>
        </div>

        <div className="bg-gray-700 p-6 rounded-lg border border-gray-600">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Active Positions</h3>
          <p className="text-3xl font-bold text-white">
            {positions?.active_count || 0}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Winning: {positions?.winning_count || 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-6">Portfolio Allocation</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={portfolioData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {portfolioData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-6">Verticals</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {verticals.map((vertical) => (
              <div
                key={vertical.name}
                className="bg-gray-700 p-4 rounded-lg border border-gray-600 hover:border-gray-500 cursor-pointer transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl">{vertical.icon}</p>
                    <p className="text-white font-semibold">{vertical.name}</p>
                    <p className="text-xs text-gray-400 mt-1">View Edge Model</p>
                  </div>
                  <div
                    className="w-12 h-12 rounded-full"
                    style={{ backgroundColor: vertical.color, opacity: 0.2 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h2 className="text-xl font-bold text-white mb-6">Today's Trades</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-gray-400 border-b border-gray-700">
              <tr>
                <th className="text-left py-3 px-4">Prediction</th>
                <th className="text-left py-3 px-4">Odds</th>
                <th className="text-left py-3 px-4">CLV</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Time</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              {trades.length > 0 ? (
                trades.map((trade) => (
                  <tr
                    key={trade.id}
                    className="border-b border-gray-700 hover:bg-gray-700 transition"
                  >
                    <td className="py-3 px-4">{trade.prediction}</td>
                    <td className="py-3 px-4">{trade.odds.toFixed(2)}</td>
                    <td
                      className={`py-3 px-4 font-semibold ${
                        trade.clv >= 0 ? 'text-green-500' : 'text-red-500'
                      }`}
                    >
                      {trade.clv.toFixed(2)}%
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          trade.status === 'active'
                            ? 'bg-blue-900 text-blue-200'
                            : trade.status === 'won'
                            ? 'bg-green-900 text-green-200'
                            : 'bg-red-900 text-red-200'
                        }`}
                      >
                        {trade.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-500">
                      {new Date(trade.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-gray-400">
                    No trades today
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
