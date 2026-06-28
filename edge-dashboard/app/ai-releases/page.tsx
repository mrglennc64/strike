'use client'

import { Card } from '@/components/Card'
import { VerticalLayout } from '@/components/VerticalLayout'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { Zap, TrendingUp } from 'lucide-react'

export default function AIReleasesPage() {
  return (
    <VerticalLayout
      title="AI Releases"
      description="Track and predict AI model releases, benchmarks, and performance indicators. Capitalize on market movements surrounding major AI announcements."
    >
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={{ name: 'John Trader', email: 'john@example.com' }} />
        <Bankroll total={100000} available={75000} allocated={25000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Current Predictions */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-2xl font-bold text-trading-text mb-6">
              Active Predictions
            </h2>

            <div className="space-y-4">
              {[
                {
                  name: 'OpenAI GPT-5 Release Date',
                  prediction: 'Q3 2026',
                  confidence: 72,
                  impact: 'High',
                  stake: 5000,
                },
                {
                  name: 'DeepSeek Benchmark Beat',
                  prediction: 'Within 30 days',
                  confidence: 58,
                  impact: 'Medium',
                  stake: 3000,
                },
                {
                  name: 'Claude 4.5 Capabilities',
                  prediction: 'Exceed O1',
                  confidence: 85,
                  impact: 'Medium',
                  stake: 7500,
                },
                {
                  name: 'Open Source Model Lead',
                  prediction: 'Llama maintains 2nd',
                  confidence: 64,
                  impact: 'Low',
                  stake: 2000,
                },
              ].map((pred, idx) => (
                <div
                  key={idx}
                  className="border border-trading-border rounded-lg p-4 hover:border-trading-accent/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-3">
                    <div>
                      <h3 className="text-trading-text font-semibold mb-1">
                        {pred.name}
                      </h3>
                      <p className="text-trading-accent text-sm font-mono">
                        {pred.prediction}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4 mt-3 md:mt-0">
                      <div className="text-right">
                        <p className="text-gray-400 text-xs">Confidence</p>
                        <p className="text-trading-accent font-bold">
                          {pred.confidence}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-gray-400 text-xs">Impact</p>
                        <p className="text-trading-text font-semibold">
                          {pred.impact}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-gray-400 text-xs">Stake</p>
                        <p className="text-trading-success font-semibold">
                          ${pred.stake.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Confidence bar */}
                  <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        pred.confidence >= 70
                          ? 'bg-trading-success'
                          : pred.confidence >= 50
                          ? 'bg-trading-warning'
                          : 'bg-trading-danger'
                      }`}
                      style={{ width: `${pred.confidence}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <button className="trading-btn w-full mt-6">
              + Create New Prediction
            </button>
          </Card>
        </div>

        {/* Statistics */}
        <div>
          <Card className="mb-6">
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Vertical Stats
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Active Bets</span>
                  <span className="text-trading-accent font-bold">4</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Total Staked</span>
                  <span className="text-trading-accent font-bold">
                    $17,500
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Current P&L</span>
                  <span className="text-trading-success font-bold">
                    +$3,250
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Win Rate</span>
                  <span className="text-trading-accent font-bold">65%</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">ROI</span>
                  <span className="text-trading-success font-bold">18.6%</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Upcoming Events
            </h3>

            <div className="space-y-3">
              {[
                {
                  date: 'Jul 5, 2026',
                  event: 'NVIDIA Earnings Call',
                  impact: 'High',
                },
                {
                  date: 'Jul 8, 2026',
                  event: 'AWS re:Invent Preview',
                  impact: 'Medium',
                },
                {
                  date: 'Jul 15, 2026',
                  event: 'Google I/O Extended',
                  impact: 'Medium',
                },
              ].map((item, idx) => (
                <div key={idx} className="border-l-2 border-trading-accent/50 pl-3">
                  <p className="text-trading-text text-sm font-semibold">
                    {item.event}
                  </p>
                  <p className="text-gray-400 text-xs">{item.date}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Risk & Audit */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskMetrics />
        <AuditLog limit={5} />
      </div>
    </VerticalLayout>
  )
}
