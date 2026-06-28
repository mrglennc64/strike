import React, { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Strategy {
  name: string
  expected_return: number
  volatility: number
  sharpe_ratio: number
  max_drawdown: number
  weight: number
}

interface AllocationData {
  optimal_weights: Record<string, number>
  portfolio_expected_return: number
  portfolio_volatility: number
  portfolio_sharpe_ratio: number
  concentration_herfindahl: number
}

interface RegimeData {
  regime_name: string
  vix_level: number
  sentiment_score: number
  regime_adjusted_weights: Record<string, number>
  recommended_action: string
  explanation: string
}

interface SimulationData {
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown_worst: number
  probability_profitable: number
  equity_curve: Array<{
    day: number
    percentile_5: number
    percentile_25: number
    median: number
    percentile_75: number
    percentile_95: number
  }>
  drawdown_distribution: Array<{
    drawdown: number
    frequency: number
  }>
  diversification_ratio: number
}

const defaultStrategies: Strategy[] = [
  {
    name: 'MLB',
    expected_return: 15,
    volatility: 12,
    sharpe_ratio: 1.25,
    max_drawdown: -0.15,
    weight: 0.2,
  },
  {
    name: 'Crypto',
    expected_return: 25,
    volatility: 40,
    sharpe_ratio: 0.625,
    max_drawdown: -0.5,
    weight: 0.15,
  },
  {
    name: 'Earnings',
    expected_return: 18,
    volatility: 18,
    sharpe_ratio: 1.0,
    max_drawdown: -0.2,
    weight: 0.25,
  },
  {
    name: 'AI',
    expected_return: 22,
    volatility: 32,
    sharpe_ratio: 0.69,
    max_drawdown: -0.35,
    weight: 0.2,
  },
  {
    name: 'Econ',
    expected_return: 12,
    volatility: 8,
    sharpe_ratio: 1.5,
    max_drawdown: -0.1,
    weight: 0.2,
  },
]

export const PortfolioPage: React.FC = () => {
  const [strategies] = useState<Strategy[]>(defaultStrategies)
  const [allocation, setAllocation] = useState<AllocationData | null>(null)
  const [regime, setRegime] = useState<RegimeData | null>(null)
  const [simulation, setSimulation] = useState<SimulationData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch allocation on component mount
  useEffect(() => {
    loadAllocation()
    loadSimulation()
    loadRegime()
  }, [])

  const loadAllocation = async () => {
    try {
      setLoading(true)
      const response = await api.post('/portfolio/allocation', {
        strategies,
        optimization_method: 'kelly',
        kelly_fraction: 0.25,
      })
      setAllocation(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load allocation')
    } finally {
      setLoading(false)
    }
  }

  const loadSimulation = async () => {
    try {
      const response = await api.post('/portfolio/simulate', {
        strategies,
        num_simulations: 1000,
        time_horizon_days: 252,
        initial_capital: 100000,
      })
      setSimulation(response.data)
    } catch (err: any) {
      console.error('Simulation failed:', err)
    }
  }

  const loadRegime = async () => {
    try {
      const response = await api.post('/portfolio/regime', {
        current_vix: 18.5,
        vix_percentile_30d: 60,
        crypto_funding_rate: 0.01,
        market_sentiment: 0.3,
        base_weights: {
          MLB: 0.2,
          Crypto: 0.15,
          Earnings: 0.25,
          AI: 0.2,
          Econ: 0.2,
        },
        strategies,
      })
      setRegime(response.data)
    } catch (err: any) {
      console.error('Regime assessment failed:', err)
    }
  }

  if (loading) return <div className="text-white">Loading portfolio data...</div>
  if (error) return <div className="text-red-500">{error}</div>

  return (
    <div className="bg-gray-900 min-h-screen p-6">
      <h1 className="text-4xl font-bold text-white mb-8">Portfolio Engine</h1>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {/* Regime Badge */}
        {regime && (
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm uppercase">Market Regime</h3>
            <p
              className={`text-2xl font-bold mt-2 ${
                regime.regime_name === 'Low Vol'
                  ? 'text-green-500'
                  : regime.regime_name === 'Normal'
                    ? 'text-blue-500'
                    : regime.regime_name === 'High Vol'
                      ? 'text-yellow-500'
                      : 'text-red-500'
              }`}
            >
              {regime.regime_name}
            </p>
            <p className="text-gray-500 text-xs mt-1">VIX: {regime.vix_level.toFixed(1)}</p>
          </div>
        )}

        {/* Projected Sharpe */}
        {allocation && (
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm uppercase">Projected Sharpe</h3>
            <p
              className={`text-2xl font-bold mt-2 ${
                allocation.portfolio_sharpe_ratio > 1 ? 'text-green-500' : 'text-amber-500'
              }`}
            >
              {allocation.portfolio_sharpe_ratio.toFixed(2)}
            </p>
            <p className="text-gray-500 text-xs mt-1">Risk-adjusted return</p>
          </div>
        )}

        {/* Correlation Drag */}
        {simulation && (
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm uppercase">Correlation Drag</h3>
            <p className="text-2xl font-bold text-blue-400 mt-2">
              -{simulation.diversification_ratio > 0 ? ((1 - 1 / simulation.diversification_ratio) * 100).toFixed(1) : '0.0'}
              %
            </p>
            <p className="text-gray-500 text-xs mt-1">Diversification ratio: {simulation.diversification_ratio.toFixed(2)}</p>
          </div>
        )}

        {/* Recommendation */}
        {regime && (
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-gray-400 text-sm uppercase">Recommendation</h3>
            <p
              className={`text-lg font-bold mt-2 ${
                regime.recommended_action === 'Hold'
                  ? 'text-green-500'
                  : regime.recommended_action === 'Increase Risk'
                    ? 'text-blue-500'
                    : regime.recommended_action === 'Reduce Risk'
                      ? 'text-red-500'
                      : 'text-yellow-500'
              }`}
            >
              {regime.recommended_action}
            </p>
            <p className="text-gray-500 text-xs mt-1">{regime.explanation.substring(0, 40)}...</p>
          </div>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Allocation Pie Chart */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-4">Current Allocation</h2>

          {allocation ? (
            <div className="space-y-4">
              <div className="relative w-48 h-48 mx-auto">
                <svg viewBox="0 0 200 200" className="w-full h-full">
                  {generatePieChart(allocation.optimal_weights)}
                </svg>
              </div>

              {/* Legend */}
              <div className="space-y-2 mt-6">
                {Object.entries(allocation.optimal_weights).map(([strategy, weight]) => (
                  <div key={strategy} className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getStrategyColor(strategy) }}
                      />
                      <span className="text-gray-300">{strategy}</span>
                    </div>
                    <span className="text-white font-mono">{(weight * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>

              {/* Metrics */}
              <div className="border-t border-gray-700 pt-4 mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Expected Return:</span>
                  <span className="text-green-400 font-mono">
                    {allocation.portfolio_expected_return.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Volatility:</span>
                  <span className="text-amber-400 font-mono">
                    {allocation.portfolio_volatility.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Concentration (HHI):</span>
                  <span className="text-blue-400 font-mono">
                    {allocation.concentration_herfindahl.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-gray-400">Loading allocation...</div>
          )}
        </div>

        {/* Middle Column - Strategy Contributions & Risk */}
        <div className="space-y-8">
          {/* Strategy Contributions Bar Chart */}
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Strategy Metrics</h2>
            <div className="space-y-4">
              {strategies.map((strategy) => (
                <div key={strategy.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">{strategy.name}</span>
                    <span className="text-gray-400">Sharpe: {strategy.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded overflow-hidden">
                    <div
                      className="h-full bg-blue-500"
                      style={{
                        width: `${Math.min((strategy.sharpe_ratio / 2) * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Return: {strategy.expected_return.toFixed(0)}%</span>
                    <span>Vol: {strategy.volatility.toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Risk Summary */}
          {simulation && (
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-4">Risk Summary</h2>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Sharpe Ratio:</span>
                  <span className="text-green-400 font-mono">{simulation.sharpe_ratio.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Sortino Ratio:</span>
                  <span className="text-green-400 font-mono">{simulation.sortino_ratio.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Max Drawdown:</span>
                  <span className="text-red-400 font-mono">{simulation.max_drawdown_worst.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Prob. Profitable:</span>
                  <span className="text-green-400 font-mono">
                    {simulation.probability_profitable.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Drawdown Distribution */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h2 className="text-xl font-bold text-white mb-4">Drawdown Distribution</h2>

          {simulation && simulation.drawdown_distribution.length > 0 ? (
            <div>
              <div className="h-64 flex items-end justify-start gap-1 px-2 py-4">
                {simulation.drawdown_distribution.slice(0, 15).map((dd, idx) => {
                  const maxFreq = Math.max(
                    ...simulation.drawdown_distribution.map((d) => d.frequency)
                  )
                  const height = (dd.frequency / maxFreq) * 100
                  return (
                    <div
                      key={idx}
                      className="flex-1 bg-red-500 rounded-t"
                      style={{ height: `${height}%`, minHeight: '2px' }}
                      title={`DD: ${(dd.drawdown * 100).toFixed(1)}% - Freq: ${dd.frequency}`}
                    />
                  )
                })}
              </div>
              <div className="text-xs text-gray-500 text-center mt-2">
                Drawdown Severity (% of simulations)
              </div>
            </div>
          ) : (
            <div className="text-gray-400">Loading drawdown data...</div>
          )}
        </div>
      </div>

      {/* Equity Curve */}
      {simulation && simulation.equity_curve.length > 0 && (
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mt-8">
          <h2 className="text-xl font-bold text-white mb-4">Equity Curve (1000-Run Monte Carlo)</h2>
          <div className="h-64 flex items-end justify-between gap-1">
            {simulation.equity_curve.map((point, idx) => {
              const maxVal = Math.max(...simulation.equity_curve.map((p) => p.percentile_95))
              const minVal = Math.min(...simulation.equity_curve.map((p) => p.percentile_5))
              const range = maxVal - minVal

              return (
                <div
                  key={idx}
                  className="relative flex-1 h-full"
                  style={{
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                  }}
                >
                  {/* Percentile bands */}
                  <div
                    className="absolute w-full bg-gray-700"
                    style={{
                      bottom: `${((point.percentile_5 - minVal) / range) * 100}%`,
                      height: `${((point.percentile_95 - point.percentile_5) / range) * 100}%`,
                      opacity: 0.3,
                    }}
                  />
                  {/* Median line */}
                  <div
                    className="absolute w-full border-b border-blue-400"
                    style={{
                      bottom: `${((point.median - minVal) / range) * 100}%`,
                    }}
                  />
                </div>
              )
            })}
          </div>
          <div className="text-xs text-gray-500 text-center mt-2">
            Bands: 5th-95th percentiles | Line: Median
          </div>
        </div>
      )}

      {/* Regime Explanation */}
      {regime && (
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mt-8">
          <h2 className="text-xl font-bold text-white mb-4">Regime Assessment</h2>
          <p className="text-gray-300 mb-4">{regime.explanation}</p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-white font-semibold text-sm mb-2">Base Weights</h3>
              <div className="space-y-1 text-sm text-gray-400">
                {strategies.map((s) => (
                  <div key={s.name} className="flex justify-between">
                    <span>{s.name}</span>
                    <span>{(s.weight * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-white font-semibold text-sm mb-2">Regime-Adjusted</h3>
              <div className="space-y-1 text-sm text-gray-400">
                {Object.entries(regime.regime_adjusted_weights).map(([name, weight]) => (
                  <div key={name} className="flex justify-between">
                    <span>{name}</span>
                    <span className={weight > (strategies.find(s => s.name === name)?.weight || 0) ? 'text-green-400' : 'text-red-400'}>
                      {(weight * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to generate pie chart SVG
function generatePieChart(weights: Record<string, number>): React.ReactNode {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
  const strategies = Object.keys(weights)
  let currentAngle = 0
  const cx = 100
  const cy = 100
  const r = 80

  return strategies.map((strategy, idx) => {
    const percentage = weights[strategy]
    const angle = percentage * 360
    const startAngle = currentAngle
    const endAngle = currentAngle + angle
    currentAngle = endAngle

    const startRad = (startAngle * Math.PI) / 180
    const endRad = (endAngle * Math.PI) / 180

    const x1 = cx + r * Math.cos(startRad)
    const y1 = cy + r * Math.sin(startRad)
    const x2 = cx + r * Math.cos(endRad)
    const y2 = cy + r * Math.sin(endRad)

    const largeArc = angle > 180 ? 1 : 0

    const d = [
      `M ${cx} ${cy}`,
      `L ${x1} ${y1}`,
      `A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`,
      'Z',
    ].join(' ')

    return (
      <path key={strategy} d={d} fill={colors[idx % colors.length]} stroke="#1a202c" strokeWidth="2" />
    )
  })
}

// Helper function to get strategy color
function getStrategyColor(strategy: string): string {
  const colors: Record<string, string> = {
    MLB: '#FF6B6B',
    Crypto: '#4ECDC4',
    Earnings: '#45B7D1',
    AI: '#FFA07A',
    Econ: '#98D8C8',
  }
  return colors[strategy] || '#95a5a6'
}
