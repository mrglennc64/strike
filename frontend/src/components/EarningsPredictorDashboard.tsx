/**
 * Earnings Beat/Miss Predictor Dashboard
 *
 * Features:
 * - Single stock earnings prediction
 * - Multi-stock edge scanner
 * - Historical prediction tracking
 * - Model performance metrics
 * - Analyst consensus visualization
 * - Options market implied probabilities
 */

import { useState } from 'react';

interface AnalystEstimates {
  symbol: string;
  company_name: string;
  current_eps_estimate: number;
  num_analysts: number;
  eps_estimate_variance: number;
  guidance_revision_trend: number;
  estimate_revisions_up: number;
  estimate_revisions_down: number;
}

interface OptionsData {
  symbol: string;
  iv_rank: number;
  vol_skew: number;
  implied_move_pct: number;
  put_call_iv_ratio: number;
  smart_money_flow: string;
  market_implied_prob_up: number;
}

interface EarningsPrediction {
  symbol: string;
  company_name: string;
  earnings_date: string;
  predicted_probability_beat: number;
  predicted_probability_miss: number;
  market_implied_prob_beat: number;
  edge_probability: number;
  edge_pct: number;
  expected_move_pct: number;
  recommendation: string;
  confidence: number;
  analyst_estimates?: AnalystEstimates;
  options_data?: OptionsData;
}

interface EdgeOpportunity extends EarningsPrediction {
  rank?: number;
}

interface BacktestMetrics {
  total_predictions: number;
  hit_rate: number;
  edge_hit_rate: number;
  avg_edge_per_prediction: number;
  profit_factor: number;
  largest_win: number;
  largest_loss: number;
  kelly_fraction: number;
}

export const EarningsPredictorDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'predict' | 'scan' | 'history' | 'metrics'>('predict');
  const [symbol, setSymbol] = useState('');
  const [prediction, setPrediction] = useState<EarningsPrediction | null>(null);
  const [scanSymbols, setScanSymbols] = useState('TSLA,MSFT,NVDA,META,AAPL');
  const [scanResults, setScanResults] = useState<EdgeOpportunity[]>([]);
  const [backtestMetrics, setBacktestMetrics] = useState<BacktestMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/verticals/earnings/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: symbol.toUpperCase() })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    try {
      setLoading(true);
      setError(null);

      const symbols = scanSymbols
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);

      const response = await fetch('/api/verticals/earnings/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols,
          min_edge_pct: 5.0,
          only_with_edge: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const rankedPredictions = data.predictions.map((p: EarningsPrediction, idx: number) => ({
        ...p,
        rank: idx + 1
      }));
      setScanResults(rankedPredictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBacktest = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/verticals/earnings/backtest?days=90');

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setBacktestMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Earnings Predictor</h1>
          <p className="text-slate-400">
            Beat/miss predictions with edge analysis and model metrics
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8">
          {(['predict', 'scan', 'history', 'metrics'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Single Prediction Tab */}
        {activeTab === 'predict' && (
          <div className="space-y-6">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h2 className="text-xl font-bold text-white mb-4">Single Stock Prediction</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="Enter stock ticker (e.g., TSLA)"
                  className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handlePredict()}
                />
                <button
                  onClick={handlePredict}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Predict'}
                </button>
              </div>
            </div>

            {prediction && (
              <div className="space-y-6">
                {/* Main Prediction Card */}
                <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                  <h3 className="text-2xl font-bold text-white mb-4">
                    {prediction.company_name} ({prediction.symbol})
                  </h3>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-slate-700 rounded p-4">
                      <p className="text-slate-400 text-sm">Earnings Date</p>
                      <p className="text-white text-lg font-semibold">
                        {new Date(prediction.earnings_date).toLocaleDateString()}
                      </p>
                    </div>

                    <div className="bg-slate-700 rounded p-4">
                      <p className="text-slate-400 text-sm">Expected Move</p>
                      <p className="text-white text-lg font-semibold">
                        ±{prediction.expected_move_pct.toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {/* Probability Visualization */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-400 mb-2">
                        {(prediction.predicted_probability_beat * 100).toFixed(1)}%
                      </div>
                      <p className="text-slate-400">P(Beat)</p>
                    </div>

                    <div className="text-center">
                      <div className="text-4xl font-bold text-red-400 mb-2">
                        {(prediction.predicted_probability_miss * 100).toFixed(1)}%
                      </div>
                      <p className="text-slate-400">P(Miss)</p>
                    </div>

                    <div className="text-center">
                      <div className="text-4xl font-bold text-blue-400 mb-2">
                        {(prediction.market_implied_prob_beat * 100).toFixed(1)}%
                      </div>
                      <p className="text-slate-400">Market P(Beat)</p>
                    </div>
                  </div>

                  {/* Edge & Recommendation */}
                  <div className="bg-slate-700 rounded p-4 mb-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-slate-400 text-sm">Edge</p>
                        <p className={`text-2xl font-bold ${
                          prediction.edge_pct > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {prediction.edge_pct > 0 ? '+' : ''}{prediction.edge_pct.toFixed(2)}%
                        </p>
                      </div>

                      <div>
                        <p className="text-slate-400 text-sm">Recommendation</p>
                        <p className="text-white font-bold text-lg">
                          {prediction.recommendation}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-slate-600">
                      <p className="text-slate-400 text-sm">Confidence</p>
                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex-1 bg-slate-600 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${prediction.confidence}%` }}
                          />
                        </div>
                        <span className="text-white font-semibold">
                          {prediction.confidence.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Analyst Consensus */}
                {prediction.analyst_estimates && (
                  <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <h4 className="text-lg font-bold text-white mb-4">Analyst Consensus</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-slate-400 text-sm">Number of Analysts</p>
                        <p className="text-white font-semibold text-xl">
                          {prediction.analyst_estimates.num_analysts}
                        </p>
                      </div>

                      <div>
                        <p className="text-slate-400 text-sm">EPS Estimate</p>
                        <p className="text-white font-semibold text-xl">
                          ${prediction.analyst_estimates.current_eps_estimate.toFixed(2)}
                        </p>
                      </div>

                      <div>
                        <p className="text-slate-400 text-sm">Guidance Revision</p>
                        <p className={`font-semibold text-xl ${
                          prediction.analyst_estimates.guidance_revision_trend > 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }`}>
                          {prediction.analyst_estimates.guidance_revision_trend > 0 ? '+' : ''}
                          {prediction.analyst_estimates.guidance_revision_trend.toFixed(2)}%
                        </p>
                      </div>

                      <div>
                        <p className="text-slate-400 text-sm">Revisions</p>
                        <div className="flex gap-2 mt-1">
                          <span className="text-green-400 font-semibold">
                            ↑{prediction.analyst_estimates.estimate_revisions_up}
                          </span>
                          <span className="text-red-400 font-semibold">
                            ↓{prediction.analyst_estimates.estimate_revisions_down}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Options Market Data */}
                {prediction.options_data && (
                  <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                    <h4 className="text-lg font-bold text-white mb-4">Options Market</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <p className="text-slate-400 text-sm">IV Rank</p>
                        <p className="text-white font-semibold text-xl">
                          {prediction.options_data.iv_rank.toFixed(0)}
                        </p>
                      </div>

                      <div>
                        <p className="text-slate-400 text-sm">Vol Skew</p>
                        <p className={`font-semibold text-xl ${
                          prediction.options_data.vol_skew > 0
                            ? 'text-red-400'
                            : 'text-green-400'
                        }`}>
                          {prediction.options_data.vol_skew > 0 ? '+' : ''}
                          {prediction.options_data.vol_skew.toFixed(2)}
                        </p>
                      </div>

                      <div>
                        <p className="text-slate-400 text-sm">Smart Money</p>
                        <p className={`font-semibold text-lg ${
                          prediction.options_data.smart_money_flow === 'bullish'
                            ? 'text-green-400'
                            : prediction.options_data.smart_money_flow === 'bearish'
                            ? 'text-red-400'
                            : 'text-gray-400'
                        }`}>
                          {prediction.options_data.smart_money_flow.toUpperCase()}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Edge Scanner Tab */}
        {activeTab === 'scan' && (
          <div className="space-y-6">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h2 className="text-xl font-bold text-white mb-4">Multi-Stock Edge Scan</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={scanSymbols}
                  onChange={(e) => setScanSymbols(e.target.value)}
                  placeholder="Enter tickers separated by commas"
                  className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleScan}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
                >
                  {loading ? 'Scanning...' : 'Scan'}
                </button>
              </div>
            </div>

            {scanResults.length > 0 && (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 overflow-x-auto">
                <h3 className="text-lg font-bold text-white mb-4">
                  {scanResults.length} Stocks with Edge
                </h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left px-4 py-2 text-slate-300">Rank</th>
                      <th className="text-left px-4 py-2 text-slate-300">Symbol</th>
                      <th className="text-right px-4 py-2 text-slate-300">P(Beat)</th>
                      <th className="text-right px-4 py-2 text-slate-300">Market P(Beat)</th>
                      <th className="text-right px-4 py-2 text-slate-300">Edge %</th>
                      <th className="text-left px-4 py-2 text-slate-300">Rec</th>
                      <th className="text-right px-4 py-2 text-slate-300">Conf</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scanResults.map((pred) => (
                      <tr key={pred.symbol} className="border-b border-slate-700 hover:bg-slate-700">
                        <td className="px-4 py-2 text-white font-semibold">#{pred.rank}</td>
                        <td className="px-4 py-2 text-white font-semibold">{pred.symbol}</td>
                        <td className="px-4 py-2 text-right">
                          <span className="text-green-400">
                            {(pred.predicted_probability_beat * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right text-slate-300">
                          {(pred.market_implied_prob_beat * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-2 text-right">
                          <span className={pred.edge_pct > 0 ? 'text-green-400 font-semibold' : 'text-red-400'}>
                            {pred.edge_pct > 0 ? '+' : ''}{pred.edge_pct.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-4 py-2 text-white text-sm">
                          {pred.recommendation}
                        </td>
                        <td className="px-4 py-2 text-right text-blue-400 font-semibold">
                          {pred.confidence.toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Model Metrics Tab */}
        {activeTab === 'metrics' && (
          <div className="space-y-6">
            <button
              onClick={handleBacktest}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
            >
              {loading ? 'Running Backtest...' : 'Run 90-Day Backtest'}
            </button>

            {backtestMetrics && (
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                  <h4 className="text-lg font-bold text-white mb-4">Performance Metrics</h4>
                  <div className="space-y-3">
                    <div>
                      <p className="text-slate-400 text-sm">Total Predictions</p>
                      <p className="text-white font-semibold text-xl">
                        {backtestMetrics.total_predictions}
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-400 text-sm">Overall Hit Rate</p>
                      <p className="text-blue-400 font-semibold text-xl">
                        {(backtestMetrics.hit_rate * 100).toFixed(1)}%
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-400 text-sm">Edge Hit Rate</p>
                      <p className="text-green-400 font-semibold text-xl">
                        {(backtestMetrics.edge_hit_rate * 100).toFixed(1)}%
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-400 text-sm">Avg Edge/Prediction</p>
                      <p className="text-green-400 font-semibold text-xl">
                        {backtestMetrics.avg_edge_per_prediction.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                  <h4 className="text-lg font-bold text-white mb-4">Risk Metrics</h4>
                  <div className="space-y-3">
                    <div>
                      <p className="text-slate-400 text-sm">Profit Factor</p>
                      <p className="text-white font-semibold text-xl">
                        {backtestMetrics.profit_factor.toFixed(2)}x
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-400 text-sm">Largest Win</p>
                      <p className="text-green-400 font-semibold text-xl">
                        +{backtestMetrics.largest_win.toFixed(2)}%
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-400 text-sm">Largest Loss</p>
                      <p className="text-red-400 font-semibold text-xl">
                        {backtestMetrics.largest_loss.toFixed(2)}%
                      </p>
                    </div>

                    <div>
                      <p className="text-slate-400 text-sm">Recommended Kelly</p>
                      <p className="text-blue-400 font-semibold text-xl">
                        {(backtestMetrics.kelly_fraction * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
