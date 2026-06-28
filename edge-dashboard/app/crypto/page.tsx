'use client'

import { Card } from '@/components/Card'
import { VerticalLayout } from '@/components/VerticalLayout'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { TrendingUp, TrendingDown, Bitcoin } from 'lucide-react'

export default function CryptoPage() {
  return (
    <VerticalLayout
      title="Crypto"
      description="Cryptocurrency price predictions, on-chain metrics, and market sentiment. Trade Bitcoin, Ethereum, and alt-coins with AI-driven signals."
    >
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={{ name: 'Crypto Trader', email: 'crypto@example.com' }} />
        <Bankroll total={500000} available={350000} allocated={150000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Crypto Positions */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-2xl font-bold text-trading-text mb-6">
              Active Positions & Predictions
            </h2>

            <div className="space-y-4">
              {[
                {
                  symbol: 'BTC',
                  name: 'Bitcoin',
                  current: 67500,
                  prediction: 71200,
                  direction: 'up',
                  confidence: 76,
                  position_size: 0.5,
                  entry: 66800,
                  pnl: 3500,
                  timeframe: '30 days',
                },
                {
                  symbol: 'ETH',
                  name: 'Ethereum',
                  current: 3450,
                  prediction: 3680,
                  direction: 'up',
                  confidence: 68,
                  position_size: 10,
                  entry: 3200,
                  pnl: 2500,
                  timeframe: '14 days',
                },
                {
                  symbol: 'SOL',
                  name: 'Solana',
                  current: 168,
                  prediction: 145,
                  direction: 'down',
                  confidence: 61,
                  position_size: 100,
                  entry: 175,
                  pnl: -700,
                  timeframe: '7 days',
                },
                {
                  symbol: 'ARB',
                  name: 'Arbitrum',
                  current: 1.15,
                  prediction: 1.55,
                  direction: 'up',
                  confidence: 72,
                  position_size: 5000,
                  entry: 0.95,
                  pnl: 10000,
                  timeframe: '60 days',
                },
              ].map((crypto, idx) => (
                <div
                  key={idx}
                  className="border border-trading-border rounded-lg p-4 hover:border-trading-accent/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3">
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <Bitcoin size={20} className="text-orange-400" />
                        <span className="font-bold text-trading-accent text-lg">
                          {crypto.symbol}
                        </span>
                        <span className="text-gray-400 text-sm">
                          {crypto.name}
                        </span>
                      </div>
                      <p className="text-trading-text text-sm mb-2">
                        Current: ${crypto.current.toLocaleString()}
                      </p>
                      <div className="flex items-center space-x-2 text-xs">
                        <span className="text-gray-500">Position:</span>
                        <span className="text-trading-text font-mono">
                          {crypto.position_size} {crypto.symbol}
                        </span>
                        <span className="text-gray-500">Entry:</span>
                        <span className="text-trading-text font-mono">
                          ${crypto.entry.toLocaleString()}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 mt-3 md:mt-0">
                      <div className="text-center">
                        <p className="text-gray-400 text-xs">Target</p>
                        <div className="flex items-center space-x-1 mt-1">
                          {crypto.direction === 'up' && (
                            <TrendingUp
                              size={16}
                              className="text-trading-success"
                            />
                          )}
                          {crypto.direction === 'down' && (
                            <TrendingDown
                              size={16}
                              className="text-trading-danger"
                            />
                          )}
                          <span className="text-trading-accent font-bold">
                            ${crypto.prediction.toLocaleString()}
                          </span>
                        </div>
                        <p className="text-gray-500 text-xs mt-1">
                          {crypto.timeframe}
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-gray-400 text-xs">Confidence</p>
                        <p className="text-trading-accent font-bold">
                          {crypto.confidence}%
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-gray-400 text-xs">P&L</p>
                        <p
                          className={`font-bold ${
                            crypto.pnl > 0
                              ? 'text-trading-success'
                              : 'text-trading-danger'
                          }`}
                        >
                          {crypto.pnl > 0 ? '+' : ''}${crypto.pnl.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        crypto.confidence >= 70
                          ? 'bg-trading-success'
                          : crypto.confidence >= 60
                          ? 'bg-trading-warning'
                          : 'bg-trading-danger'
                      }`}
                      style={{ width: `${crypto.confidence}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <button className="trading-btn w-full mt-6">
              + Open New Position
            </button>
          </Card>
        </div>

        {/* Crypto Stats */}
        <div>
          <Card className="mb-6">
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Portfolio Stats
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Open Positions</span>
                  <span className="text-trading-accent font-bold">4</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Total Invested</span>
                  <span className="text-trading-accent font-bold">
                    $150,000
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Unrealized P&L</span>
                  <span className="text-trading-success font-bold">
                    +$15,300
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Win Rate</span>
                  <span className="text-trading-accent font-bold">67%</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">YTD Return</span>
                  <span className="text-trading-success font-bold">35.6%</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              On-Chain Signals
            </h3>

            <div className="space-y-3">
              {[
                {
                  signal: 'Whale Accumulation',
                  asset: 'BTC',
                  strength: 'Strong',
                },
                { signal: 'Exchange Outflow', asset: 'ETH', strength: 'Medium' },
                { signal: 'Large Transfers', asset: 'SOL', strength: 'Weak' },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="border border-trading-border rounded p-2"
                >
                  <p className="text-trading-text text-sm font-semibold">
                    {item.signal}
                  </p>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-trading-accent text-xs">
                      {item.asset}
                    </span>
                    <span
                      className={`text-xs font-bold ${
                        item.strength === 'Strong'
                          ? 'text-trading-success'
                          : item.strength === 'Medium'
                          ? 'text-trading-warning'
                          : 'text-trading-danger'
                      }`}
                    >
                      {item.strength}
                    </span>
                  </div>
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
