import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
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
export const EarningsPredictorDashboard = () => {
    const [activeTab, setActiveTab] = useState('predict');
    const [symbol, setSymbol] = useState('');
    const [prediction, setPrediction] = useState(null);
    const [scanSymbols, setScanSymbols] = useState('TSLA,MSFT,NVDA,META,AAPL');
    const [scanResults, setScanResults] = useState([]);
    const [backtestMetrics, setBacktestMetrics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
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
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Prediction failed');
        }
        finally {
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
            const rankedPredictions = data.predictions.map((p, idx) => ({
                ...p,
                rank: idx + 1
            }));
            setScanResults(rankedPredictions);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Scan failed');
        }
        finally {
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
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Backtest failed');
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx("div", { className: "min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6", children: _jsxs("div", { className: "max-w-7xl mx-auto", children: [_jsxs("div", { className: "mb-8", children: [_jsx("h1", { className: "text-4xl font-bold text-white mb-2", children: "Earnings Predictor" }), _jsx("p", { className: "text-slate-400", children: "Beat/miss predictions with edge analysis and model metrics" })] }), _jsx("div", { className: "flex gap-4 mb-8", children: ['predict', 'scan', 'history', 'metrics'].map(tab => (_jsx("button", { onClick: () => setActiveTab(tab), className: `px-6 py-2 rounded-lg font-medium transition-colors ${activeTab === tab
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`, children: tab.charAt(0).toUpperCase() + tab.slice(1) }, tab))) }), error && (_jsx("div", { className: "mb-6 p-4 bg-red-900 border border-red-700 rounded-lg text-red-200", children: error })), activeTab === 'predict' && (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Single Stock Prediction" }), _jsxs("div", { className: "flex gap-4", children: [_jsx("input", { type: "text", value: symbol, onChange: (e) => setSymbol(e.target.value), placeholder: "Enter stock ticker (e.g., TSLA)", className: "flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500", onKeyPress: (e) => e.key === 'Enter' && handlePredict() }), _jsx("button", { onClick: handlePredict, disabled: loading, className: "px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50", children: loading ? 'Loading...' : 'Predict' })] })] }), prediction && (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsxs("h3", { className: "text-2xl font-bold text-white mb-4", children: [prediction.company_name, " (", prediction.symbol, ")"] }), _jsxs("div", { className: "grid grid-cols-2 gap-4 mb-6", children: [_jsxs("div", { className: "bg-slate-700 rounded p-4", children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Earnings Date" }), _jsx("p", { className: "text-white text-lg font-semibold", children: new Date(prediction.earnings_date).toLocaleDateString() })] }), _jsxs("div", { className: "bg-slate-700 rounded p-4", children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Expected Move" }), _jsxs("p", { className: "text-white text-lg font-semibold", children: ["\u00B1", prediction.expected_move_pct.toFixed(2), "%"] })] })] }), _jsxs("div", { className: "grid grid-cols-3 gap-4 mb-6", children: [_jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-4xl font-bold text-green-400 mb-2", children: [(prediction.predicted_probability_beat * 100).toFixed(1), "%"] }), _jsx("p", { className: "text-slate-400", children: "P(Beat)" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-4xl font-bold text-red-400 mb-2", children: [(prediction.predicted_probability_miss * 100).toFixed(1), "%"] }), _jsx("p", { className: "text-slate-400", children: "P(Miss)" })] }), _jsxs("div", { className: "text-center", children: [_jsxs("div", { className: "text-4xl font-bold text-blue-400 mb-2", children: [(prediction.market_implied_prob_beat * 100).toFixed(1), "%"] }), _jsx("p", { className: "text-slate-400", children: "Market P(Beat)" })] })] }), _jsxs("div", { className: "bg-slate-700 rounded p-4 mb-6", children: [_jsxs("div", { className: "grid grid-cols-2 gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Edge" }), _jsxs("p", { className: `text-2xl font-bold ${prediction.edge_pct > 0 ? 'text-green-400' : 'text-red-400'}`, children: [prediction.edge_pct > 0 ? '+' : '', prediction.edge_pct.toFixed(2), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Recommendation" }), _jsx("p", { className: "text-white font-bold text-lg", children: prediction.recommendation })] })] }), _jsxs("div", { className: "mt-4 pt-4 border-t border-slate-600", children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Confidence" }), _jsxs("div", { className: "flex items-center gap-2 mt-2", children: [_jsx("div", { className: "flex-1 bg-slate-600 rounded-full h-2", children: _jsx("div", { className: "bg-blue-500 h-2 rounded-full", style: { width: `${prediction.confidence}%` } }) }), _jsxs("span", { className: "text-white font-semibold", children: [prediction.confidence.toFixed(1), "%"] })] })] })] })] }), prediction.analyst_estimates && (_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsx("h4", { className: "text-lg font-bold text-white mb-4", children: "Analyst Consensus" }), _jsxs("div", { className: "grid grid-cols-2 gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Number of Analysts" }), _jsx("p", { className: "text-white font-semibold text-xl", children: prediction.analyst_estimates.num_analysts })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "EPS Estimate" }), _jsxs("p", { className: "text-white font-semibold text-xl", children: ["$", prediction.analyst_estimates.current_eps_estimate.toFixed(2)] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Guidance Revision" }), _jsxs("p", { className: `font-semibold text-xl ${prediction.analyst_estimates.guidance_revision_trend > 0
                                                                ? 'text-green-400'
                                                                : 'text-red-400'}`, children: [prediction.analyst_estimates.guidance_revision_trend > 0 ? '+' : '', prediction.analyst_estimates.guidance_revision_trend.toFixed(2), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Revisions" }), _jsxs("div", { className: "flex gap-2 mt-1", children: [_jsxs("span", { className: "text-green-400 font-semibold", children: ["\u2191", prediction.analyst_estimates.estimate_revisions_up] }), _jsxs("span", { className: "text-red-400 font-semibold", children: ["\u2193", prediction.analyst_estimates.estimate_revisions_down] })] })] })] })] })), prediction.options_data && (_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsx("h4", { className: "text-lg font-bold text-white mb-4", children: "Options Market" }), _jsxs("div", { className: "grid grid-cols-3 gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "IV Rank" }), _jsx("p", { className: "text-white font-semibold text-xl", children: prediction.options_data.iv_rank.toFixed(0) })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Vol Skew" }), _jsxs("p", { className: `font-semibold text-xl ${prediction.options_data.vol_skew > 0
                                                                ? 'text-red-400'
                                                                : 'text-green-400'}`, children: [prediction.options_data.vol_skew > 0 ? '+' : '', prediction.options_data.vol_skew.toFixed(2)] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Smart Money" }), _jsx("p", { className: `font-semibold text-lg ${prediction.options_data.smart_money_flow === 'bullish'
                                                                ? 'text-green-400'
                                                                : prediction.options_data.smart_money_flow === 'bearish'
                                                                    ? 'text-red-400'
                                                                    : 'text-gray-400'}`, children: prediction.options_data.smart_money_flow.toUpperCase() })] })] })] }))] }))] })), activeTab === 'scan' && (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Multi-Stock Edge Scan" }), _jsxs("div", { className: "flex gap-4", children: [_jsx("input", { type: "text", value: scanSymbols, onChange: (e) => setScanSymbols(e.target.value), placeholder: "Enter tickers separated by commas", className: "flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500" }), _jsx("button", { onClick: handleScan, disabled: loading, className: "px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50", children: loading ? 'Scanning...' : 'Scan' })] })] }), scanResults.length > 0 && (_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700 overflow-x-auto", children: [_jsxs("h3", { className: "text-lg font-bold text-white mb-4", children: [scanResults.length, " Stocks with Edge"] }), _jsxs("table", { className: "w-full text-sm", children: [_jsx("thead", { children: _jsxs("tr", { className: "border-b border-slate-700", children: [_jsx("th", { className: "text-left px-4 py-2 text-slate-300", children: "Rank" }), _jsx("th", { className: "text-left px-4 py-2 text-slate-300", children: "Symbol" }), _jsx("th", { className: "text-right px-4 py-2 text-slate-300", children: "P(Beat)" }), _jsx("th", { className: "text-right px-4 py-2 text-slate-300", children: "Market P(Beat)" }), _jsx("th", { className: "text-right px-4 py-2 text-slate-300", children: "Edge %" }), _jsx("th", { className: "text-left px-4 py-2 text-slate-300", children: "Rec" }), _jsx("th", { className: "text-right px-4 py-2 text-slate-300", children: "Conf" })] }) }), _jsx("tbody", { children: scanResults.map((pred) => (_jsxs("tr", { className: "border-b border-slate-700 hover:bg-slate-700", children: [_jsxs("td", { className: "px-4 py-2 text-white font-semibold", children: ["#", pred.rank] }), _jsx("td", { className: "px-4 py-2 text-white font-semibold", children: pred.symbol }), _jsx("td", { className: "px-4 py-2 text-right", children: _jsxs("span", { className: "text-green-400", children: [(pred.predicted_probability_beat * 100).toFixed(1), "%"] }) }), _jsxs("td", { className: "px-4 py-2 text-right text-slate-300", children: [(pred.market_implied_prob_beat * 100).toFixed(1), "%"] }), _jsx("td", { className: "px-4 py-2 text-right", children: _jsxs("span", { className: pred.edge_pct > 0 ? 'text-green-400 font-semibold' : 'text-red-400', children: [pred.edge_pct > 0 ? '+' : '', pred.edge_pct.toFixed(2), "%"] }) }), _jsx("td", { className: "px-4 py-2 text-white text-sm", children: pred.recommendation }), _jsxs("td", { className: "px-4 py-2 text-right text-blue-400 font-semibold", children: [pred.confidence.toFixed(0), "%"] })] }, pred.symbol))) })] })] }))] })), activeTab === 'metrics' && (_jsxs("div", { className: "space-y-6", children: [_jsx("button", { onClick: handleBacktest, disabled: loading, className: "px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50", children: loading ? 'Running Backtest...' : 'Run 90-Day Backtest' }), backtestMetrics && (_jsxs("div", { className: "grid grid-cols-2 gap-6", children: [_jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsx("h4", { className: "text-lg font-bold text-white mb-4", children: "Performance Metrics" }), _jsxs("div", { className: "space-y-3", children: [_jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Total Predictions" }), _jsx("p", { className: "text-white font-semibold text-xl", children: backtestMetrics.total_predictions })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Overall Hit Rate" }), _jsxs("p", { className: "text-blue-400 font-semibold text-xl", children: [(backtestMetrics.hit_rate * 100).toFixed(1), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Edge Hit Rate" }), _jsxs("p", { className: "text-green-400 font-semibold text-xl", children: [(backtestMetrics.edge_hit_rate * 100).toFixed(1), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Avg Edge/Prediction" }), _jsxs("p", { className: "text-green-400 font-semibold text-xl", children: [backtestMetrics.avg_edge_per_prediction.toFixed(2), "%"] })] })] })] }), _jsxs("div", { className: "bg-slate-800 rounded-lg p-6 border border-slate-700", children: [_jsx("h4", { className: "text-lg font-bold text-white mb-4", children: "Risk Metrics" }), _jsxs("div", { className: "space-y-3", children: [_jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Profit Factor" }), _jsxs("p", { className: "text-white font-semibold text-xl", children: [backtestMetrics.profit_factor.toFixed(2), "x"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Largest Win" }), _jsxs("p", { className: "text-green-400 font-semibold text-xl", children: ["+", backtestMetrics.largest_win.toFixed(2), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Largest Loss" }), _jsxs("p", { className: "text-red-400 font-semibold text-xl", children: [backtestMetrics.largest_loss.toFixed(2), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-slate-400 text-sm", children: "Recommended Kelly" }), _jsxs("p", { className: "text-blue-400 font-semibold text-xl", children: [(backtestMetrics.kelly_fraction * 100).toFixed(1), "%"] })] })] })] })] }))] }))] }) }));
};
