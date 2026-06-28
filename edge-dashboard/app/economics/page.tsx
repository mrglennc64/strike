'use client'

import { Card } from '@/components/Card'
import { VerticalLayout } from '@/components/VerticalLayout'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function EconomicsPage() {
  return (
    <VerticalLayout
      title="Economics"
      description="Economic indicators, Fed decisions, inflation trends, and market cycles. Predict macroeconomic events and their market impact."
    >
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={{ name: 'Sarah Analyst', email: 'sarah@example.com' }} />
        <Bankroll total={150000} available={110000} allocated={40000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Economic Calendar */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-2xl font-bold text-trading-text mb-6">
              Economic Calendar & Predictions
            </h2>

            <div className="space-y-4">
              {[
                {
                  date: 'Jul 2, 2026',
                  indicator: 'US Unemployment Rate',
                  forecast: '3.8%',
                  previous: '3.9%',
                  prediction: '3.7%',
                  direction: 'down',
                  confidence: 76,
                  stake: 8000,
                },
                {
                  date: 'Jul 8, 2026',
                  indicator: 'Fed Rate Decision',
                  forecast: 'Hold',
                  previous: '5.25-5.50%',
                  prediction: 'Hold',
                  direction: 'neutral',
                  confidence: 88,
                  stake: 12000,
                },
                {
                  date: 'Jul 10, 2026',
                  indicator: 'CPI (YoY)',
                  forecast: '2.9%',
                  previous: '3.1%',
                  prediction: '2.8%',
                  direction: 'down',
                  confidence: 62,
                  stake: 6500,
                },
                {
                  date: 'Jul 15, 2026',
                  indicator: 'GDP Growth (Q2)',
                  forecast: '2.1%',
                  previous: '1.4%',
                  prediction: '2.3%',
                  direction: 'up',
                  confidence: 71,
                  stake: 10000,
                },
              ].map((event, idx) => (
                <div
                  key={idx}
                  className="border border-trading-border rounded-lg p-4 hover:border-trading-accent/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3">
                    <div>
                      <p className="text-gray-400 text-xs mb-1">{event.date}</p>
                      <h3 className="text-trading-text font-semibold">
                        {event.indicator}
                      </h3>
                      <div className="flex items-center space-x-4 mt-2 text-sm">
                        <span>
                          <span className="text-gray-500">Forecast: </span>
                          <span className="text-trading-text font-mono">
                            {event.forecast}
                          </span>
                        </span>
                        <span>
                          <span className="text-gray-500">Previous: </span>
                          <span className="text-trading-text font-mono">
                            {event.previous}
                          </span>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 mt-3 md:mt-0">
                      <div className="text-center">
                        <p className="text-gray-400 text-xs">Prediction</p>
                        <div className="flex items-center space-x-1 mt-1">
                          {event.direction === 'up' && (
                            <TrendingUp
                              size={16}
                              className="text-trading-success"
                            />
                          )}
                          {event.direction === 'down' && (
                            <TrendingDown
                              size={16}
                              className="text-trading-danger"
                            />
                          )}
                          <span className="text-trading-accent font-bold">
                            {event.prediction}
                          </span>
                        </div>
                      </div>

                      <div className="text-right">
                        <p className="text-gray-400 text-xs">Confidence</p>
                        <p className="text-trading-accent font-bold">
                          {event.confidence}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        event.confidence >= 75
                          ? 'bg-trading-success'
                          : event.confidence >= 60
                          ? 'bg-trading-warning'
                          : 'bg-trading-danger'
                      }`}
                      style={{ width: `${event.confidence}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <button className="trading-btn w-full mt-6">
              + Add Economic Prediction
            </button>
          </Card>
        </div>

        {/* Market Impact Summary */}
        <div>
          <Card className="mb-6">
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Vertical Stats
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Active Calls</span>
                  <span className="text-trading-accent font-bold">4</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Total Capital</span>
                  <span className="text-trading-accent font-bold">
                    $36,500
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Unrealized P&L</span>
                  <span className="text-trading-success font-bold">
                    +$5,890
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Accuracy</span>
                  <span className="text-trading-accent font-bold">72%</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">YTD Return</span>
                  <span className="text-trading-success font-bold">14.2%</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Recent Wins
            </h3>

            <div className="space-y-3">
              {[
                { event: 'Fed Hold Decision', gain: '+$2,100' },
                { event: 'Jobs Report Beat', gain: '+$1,800' },
                { event: 'Inflation Cool Down', gain: '+$1,990' },
              ].map((win, idx) => (
                <div key={idx} className="border-l-2 border-trading-success pl-3">
                  <p className="text-trading-text text-sm font-semibold">
                    {win.event}
                  </p>
                  <p className="text-trading-success text-sm font-bold">
                    {win.gain}
                  </p>
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
