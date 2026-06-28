'use client'

import { Card } from '@/components/Card'
import { VerticalLayout } from '@/components/VerticalLayout'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'

export default function EarningsPage() {
  return (
    <VerticalLayout
      title="Earnings"
      description="Corporate earnings predictions, guidance, and analyst sentiment analysis. Trade around earnings announcements with AI-powered confidence scores."
    >
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={{ name: 'Mike Trader', email: 'mike@example.com' }} />
        <Bankroll total={200000} available={140000} allocated={60000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Earnings Calendar */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-2xl font-bold text-trading-text mb-6">
              Earnings Calendar & Analysis
            </h2>

            <div className="space-y-4">
              {[
                {
                  ticker: 'NVDA',
                  company: 'NVIDIA',
                  date: 'Aug 28, 2026',
                  epsForecast: '$0.68',
                  eps_prediction: '$0.71',
                  consensusRating: 'Buy',
                  analysis: 'AI demand strength continues',
                  confidence: 82,
                  stake: 15000,
                  expectedMove: '+4.2%',
                },
                {
                  ticker: 'MSFT',
                  company: 'Microsoft',
                  date: 'Oct 23, 2026',
                  epsForecast: '$2.31',
                  eps_prediction: '$2.45',
                  consensusRating: 'Buy',
                  analysis: 'Cloud growth accelerating',
                  confidence: 79,
                  stake: 12000,
                  expectedMove: '+3.8%',
                },
                {
                  ticker: 'AMZN',
                  company: 'Amazon',
                  date: 'Oct 27, 2026',
                  epsForecast: '$0.88',
                  eps_prediction: '$0.92',
                  consensusRating: 'Buy',
                  analysis: 'AWS recovery trend',
                  confidence: 71,
                  stake: 10000,
                  expectedMove: '+2.9%',
                },
                {
                  ticker: 'GOOGL',
                  company: 'Alphabet',
                  date: 'Oct 29, 2026',
                  epsForecast: '$1.83',
                  eps_prediction: '$1.76',
                  consensusRating: 'Hold',
                  analysis: 'Ad market headwinds concern',
                  confidence: 58,
                  stake: 8000,
                  expectedMove: '-2.1%',
                },
              ].map((stock, idx) => (
                <div
                  key={idx}
                  className="border border-trading-border rounded-lg p-4 hover:border-trading-accent/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3">
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-bold text-trading-accent text-lg">
                          {stock.ticker}
                        </span>
                        <span className="text-gray-400 text-sm">
                          {stock.company}
                        </span>
                      </div>
                      <p className="text-gray-400 text-xs mb-2">
                        Earnings: {stock.date}
                      </p>
                      <p className="text-trading-text text-sm mb-1">
                        {stock.analysis}
                      </p>
                      <div className="flex items-center space-x-3 text-xs mt-2">
                        <span>
                          <span className="text-gray-500">Consensus EPS: </span>
                          <span className="text-trading-text font-mono">
                            {stock.epsForecast}
                          </span>
                        </span>
                        <span>
                          <span className="text-gray-500">Prediction: </span>
                          <span className="text-trading-accent font-mono font-bold">
                            {stock.eps_prediction}
                          </span>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 mt-3 md:mt-0">
                      <div className="text-center">
                        <p className="text-gray-400 text-xs">Expected Move</p>
                        <p
                          className={`font-bold text-sm ${
                            stock.expectedMove.includes('+')
                              ? 'text-trading-success'
                              : 'text-trading-danger'
                          }`}
                        >
                          {stock.expectedMove}
                        </p>
                      </div>

                      <div className="text-center">
                        <p className="text-gray-400 text-xs">Confidence</p>
                        <p className="text-trading-accent font-bold">
                          {stock.confidence}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        stock.confidence >= 75
                          ? 'bg-trading-success'
                          : stock.confidence >= 60
                          ? 'bg-trading-warning'
                          : 'bg-trading-danger'
                      }`}
                      style={{ width: `${stock.confidence}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <button className="trading-btn w-full mt-6">
              + Monitor New Company
            </button>
          </Card>
        </div>

        {/* Earnings Stats */}
        <div>
          <Card className="mb-6">
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Vertical Stats
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Tracked Companies</span>
                  <span className="text-trading-accent font-bold">8</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Capital at Risk</span>
                  <span className="text-trading-accent font-bold">
                    $45,000
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Realized P&L</span>
                  <span className="text-trading-success font-bold">
                    +$8,450
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Hit Rate</span>
                  <span className="text-trading-accent font-bold">73%</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">YTD Return</span>
                  <span className="text-trading-success font-bold">18.8%</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Next Week Earnings
            </h3>

            <div className="space-y-3">
              {[
                { ticker: 'META', date: 'Jul 30' },
                { ticker: 'UBER', date: 'Jul 31' },
                { ticker: 'TSLA', date: 'Aug 5' },
              ].map((company, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-trading-bg rounded border-l-2 border-trading-warning"
                >
                  <span className="text-trading-accent font-bold">
                    {company.ticker}
                  </span>
                  <span className="text-gray-400 text-sm">{company.date}</span>
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
