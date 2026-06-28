'use client'

import Link from 'next/link'
import { Card } from '@/components/Card'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { Zap, TrendingUp, Briefcase, Bitcoin, Trophy, ArrowRight } from 'lucide-react'

const verticals = [
  { name: 'AI Releases', href: '/ai-releases', icon: Zap, stats: { value: '4', label: 'Active Calls', color: 'text-yellow-400' } },
  { name: 'Economics', href: '/economics', icon: TrendingUp, stats: { value: '$36.5K', label: 'Capital', color: 'text-green-400' } },
  { name: 'Earnings', href: '/earnings', icon: Briefcase, stats: { value: '8', label: 'Tracked', color: 'text-blue-400' } },
  { name: 'Crypto', href: '/crypto', icon: Bitcoin, stats: { value: '+35.6%', label: 'YTD Return', color: 'text-orange-400' } },
  { name: 'MLB', href: '/mlb', icon: Trophy, stats: { value: '61%', label: 'Hit Rate', color: 'text-red-400' } },
]

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-trading-bg">
      {/* Header */}
      <section className="border-b border-trading-border py-8 md:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl md:text-5xl font-bold text-trading-text mb-2">
            Dashboard
          </h1>
          <p className="text-gray-400 text-lg">
            Central hub for all your edge trading across verticals
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Profile & Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <Authentication user={{ name: 'Premium Trader', email: 'trader@example.com' }} />
            <Bankroll total={900000} available={600000} allocated={300000} />
          </div>

          {/* Vertical Quick Links */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-trading-text mb-6">
              Vertical Overview
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {verticals.map((vertical) => {
                const IconComponent = vertical.icon
                return (
                  <Link key={vertical.href} href={vertical.href}>
                    <Card className="h-full cursor-pointer hover:border-trading-accent transition-colors">
                      <div className="flex flex-col h-full">
                        <div className={`text-4xl mb-4 ${vertical.stats.color}`}>
                          <IconComponent size={32} />
                        </div>
                        <h3 className="text-lg font-bold text-trading-text mb-2">
                          {vertical.name}
                        </h3>
                        <div className="mt-auto">
                          <p className="text-trading-accent font-bold text-lg">
                            {vertical.stats.value}
                          </p>
                          <p className="text-gray-400 text-xs">
                            {vertical.stats.label}
                          </p>
                        </div>
                        <div className="mt-4 pt-4 border-t border-trading-border">
                          <span className="text-trading-accent text-sm font-semibold flex items-center">
                            Go to vertical <ArrowRight size={14} className="ml-1" />
                          </span>
                        </div>
                      </div>
                    </Card>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Portfolio Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <Card>
              <h3 className="text-lg font-semibold text-trading-text mb-4">
                Portfolio Summary
              </h3>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400 text-sm">Total Assets</span>
                    <span className="text-trading-accent font-bold">
                      $900,000
                    </span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400 text-sm">
                      Unrealized P&L
                    </span>
                    <span className="text-trading-success font-bold">
                      +$34,590
                    </span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400 text-sm">YTD Return</span>
                    <span className="text-trading-success font-bold">
                      +18.4%
                    </span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400 text-sm">
                      Active Positions
                    </span>
                    <span className="text-trading-accent font-bold">24</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400 text-sm">
                      Overall Win Rate
                    </span>
                    <span className="text-trading-accent font-bold">66%</span>
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-trading-text mb-4">
                Capital Allocation
              </h3>

              <div className="space-y-3">
                {[
                  { vertical: 'AI Releases', pct: 20, amount: 60000 },
                  { vertical: 'Economics', pct: 25, amount: 75000 },
                  { vertical: 'Earnings', pct: 28, amount: 84000 },
                  { vertical: 'Crypto', pct: 20, amount: 60000 },
                  { vertical: 'MLB', pct: 7, amount: 21000 },
                ].map((alloc, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400 text-xs">
                        {alloc.vertical}
                      </span>
                      <span className="text-trading-text text-xs font-semibold">
                        {alloc.pct}% (${alloc.amount.toLocaleString()})
                      </span>
                    </div>
                    <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-trading-accent to-blue-500"
                        style={{ width: `${alloc.pct}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-trading-text mb-4">
                Recent Alerts
              </h3>

              <div className="space-y-3">
                {[
                  { type: 'success', text: 'BTC target hit at $71,200' },
                  { type: 'warning', text: 'SOL position at -8% loss' },
                  { type: 'info', text: 'MSFT earnings in 2 weeks' },
                  { type: 'success', text: 'Fed hold call correct' },
                ].map((alert, idx) => (
                  <div
                    key={idx}
                    className={`p-2 rounded border-l-2 ${
                      alert.type === 'success'
                        ? 'border-trading-success bg-trading-success/10'
                        : alert.type === 'warning'
                        ? 'border-trading-warning bg-trading-warning/10'
                        : 'border-trading-accent bg-trading-accent/10'
                    }`}
                  >
                    <p
                      className={`text-xs ${
                        alert.type === 'success'
                          ? 'text-trading-success'
                          : alert.type === 'warning'
                          ? 'text-trading-warning'
                          : 'text-trading-accent'
                      }`}
                    >
                      {alert.text}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Risk & Audit */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RiskMetrics />
            <AuditLog limit={8} />
          </div>
        </div>
      </section>
    </main>
  )
}
