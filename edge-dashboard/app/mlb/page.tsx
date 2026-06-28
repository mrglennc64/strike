'use client'

import { Card } from '@/components/Card'
import { VerticalLayout } from '@/components/VerticalLayout'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { TrendingUp, TrendingDown, Trophy } from 'lucide-react'

export default function MLBPage() {
  return (
    <VerticalLayout
      title="MLB"
      description="Baseball strikeout edges, pitcher matchups, and in-game predictions. Exploit market inefficiencies in prop betting."
    >
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={{ name: 'Sports Analyst', email: 'sports@example.com' }} />
        <Bankroll total={50000} available={38000} allocated={12000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Strikeout Predictions */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="text-2xl font-bold text-trading-text mb-6">
              Strikeout Edge Predictions
            </h2>

            <div className="space-y-4">
              {[
                {
                  pitcher: 'Lucas Giolito',
                  team: 'LAD',
                  opponent: 'NYM',
                  date: '2026-07-02',
                  ks_prediction: 7.8,
                  ks_line: 7.5,
                  edge: 'OVER',
                  confidence: 74,
                  implied_odds: '-120',
                  stake: 2500,
                },
                {
                  pitcher: 'Gerrit Cole',
                  team: 'NYY',
                  opponent: 'HOU',
                  date: '2026-07-03',
                  ks_prediction: 8.2,
                  ks_line: 8.0,
                  edge: 'OVER',
                  confidence: 68,
                  implied_odds: '-110',
                  stake: 2000,
                },
                {
                  pitcher: 'Kodai Senga',
                  team: 'NYM',
                  opponent: 'LAD',
                  date: '2026-07-02',
                  ks_prediction: 6.1,
                  ks_line: 6.5,
                  edge: 'UNDER',
                  confidence: 71,
                  implied_odds: '+105',
                  stake: 1800,
                },
                {
                  pitcher: 'Max Scherzer',
                  team: 'NYM',
                  opponent: 'PHI',
                  date: '2026-07-04',
                  ks_prediction: 7.5,
                  ks_line: 6.5,
                  edge: 'OVER',
                  confidence: 82,
                  implied_odds: '-130',
                  stake: 3000,
                },
              ].map((pred, idx) => (
                <div
                  key={idx}
                  className="border border-trading-border rounded-lg p-4 hover:border-trading-accent/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3">
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <Trophy size={18} className="text-yellow-400" />
                        <span className="font-bold text-trading-text text-lg">
                          {pred.pitcher}
                        </span>
                        <span className="text-gray-400 text-sm">
                          {pred.team} vs {pred.opponent}
                        </span>
                      </div>
                      <p className="text-gray-400 text-xs mb-2">{pred.date}</p>
                      <div className="flex items-center space-x-4 text-sm">
                        <span>
                          <span className="text-gray-500">Line: </span>
                          <span className="text-trading-text font-mono">
                            {pred.ks_line} K
                          </span>
                        </span>
                        <span>
                          <span className="text-gray-500">Prediction: </span>
                          <span className="text-trading-accent font-mono font-bold">
                            {pred.ks_prediction} K
                          </span>
                        </span>
                        <span>
                          <span className="text-gray-500">Odds: </span>
                          <span className="text-trading-text font-mono">
                            {pred.implied_odds}
                          </span>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 mt-3 md:mt-0">
                      <div className="text-center">
                        <p className="text-gray-400 text-xs">Edge</p>
                        <div className="flex items-center space-x-1 mt-1">
                          {pred.edge === 'OVER' ? (
                            <TrendingUp
                              size={16}
                              className="text-trading-success"
                            />
                          ) : (
                            <TrendingDown
                              size={16}
                              className="text-trading-danger"
                            />
                          )}
                          <span
                            className={`font-bold ${
                              pred.edge === 'OVER'
                                ? 'text-trading-success'
                                : 'text-trading-danger'
                            }`}
                          >
                            {pred.edge}
                          </span>
                        </div>
                      </div>

                      <div className="text-center">
                        <p className="text-gray-400 text-xs">Confidence</p>
                        <p className="text-trading-accent font-bold">
                          {pred.confidence}%
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

                  <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        pred.confidence >= 75
                          ? 'bg-trading-success'
                          : pred.confidence >= 65
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
              + Add Strikeout Prediction
            </button>
          </Card>
        </div>

        {/* MLB Stats */}
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
                  <span className="text-gray-400 text-sm">Total Wagered</span>
                  <span className="text-trading-accent font-bold">
                    $9,300
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Current P&L</span>
                  <span className="text-trading-success font-bold">
                    +$2,150
                  </span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">Hit Rate</span>
                  <span className="text-trading-accent font-bold">61%</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400 text-sm">ROI</span>
                  <span className="text-trading-success font-bold">23.1%</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-trading-text mb-4">
              Today's Games
            </h3>

            <div className="space-y-3">
              {[
                { matchup: 'LAD vs NYM', time: '7:10 PM ET' },
                { matchup: 'HOU vs TB', time: '7:10 PM ET' },
                { matchup: 'BOS vs TOR', time: '7:07 PM ET' },
              ].map((game, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-trading-bg rounded border-l-2 border-trading-accent"
                >
                  <span className="text-trading-text font-semibold text-sm">
                    {game.matchup}
                  </span>
                  <span className="text-gray-400 text-xs">{game.time}</span>
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
