import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { api } from '../api/client';
const defaultStrategies = [
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
];
export const PortfolioPage = () => {
    const [strategies] = useState(defaultStrategies);
    const [allocation, setAllocation] = useState(null);
    const [regime, setRegime] = useState(null);
    const [simulation, setSimulation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    // Fetch allocation on component mount
    useEffect(() => {
        loadAllocation();
        loadSimulation();
        loadRegime();
    }, []);
    const loadAllocation = async () => {
        try {
            setLoading(true);
            const response = await api.post('/portfolio/allocation', {
                strategies,
                optimization_method: 'kelly',
                kelly_fraction: 0.25,
            });
            setAllocation(response.data);
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Failed to load allocation');
        }
        finally {
            setLoading(false);
        }
    };
    const loadSimulation = async () => {
        try {
            const response = await api.post('/portfolio/simulate', {
                strategies,
                num_simulations: 1000,
                time_horizon_days: 252,
                initial_capital: 100000,
            });
            setSimulation(response.data);
        }
        catch (err) {
            console.error('Simulation failed:', err);
        }
    };
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
            });
            setRegime(response.data);
        }
        catch (err) {
            console.error('Regime assessment failed:', err);
        }
    };
    if (loading)
        return _jsx("div", { className: "text-white", children: "Loading portfolio data..." });
    if (error)
        return _jsx("div", { className: "text-red-500", children: error });
    return (_jsxs("div", { className: "bg-gray-900 min-h-screen p-6", children: [_jsx("h1", { className: "text-4xl font-bold text-white mb-8", children: "Portfolio Engine" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4 mb-8", children: [regime && (_jsxs("div", { className: "bg-gray-800 p-4 rounded-lg border border-gray-700", children: [_jsx("h3", { className: "text-gray-400 text-sm uppercase", children: "Market Regime" }), _jsx("p", { className: `text-2xl font-bold mt-2 ${regime.regime_name === 'Low Vol'
                                    ? 'text-green-500'
                                    : regime.regime_name === 'Normal'
                                        ? 'text-blue-500'
                                        : regime.regime_name === 'High Vol'
                                            ? 'text-yellow-500'
                                            : 'text-red-500'}`, children: regime.regime_name }), _jsxs("p", { className: "text-gray-500 text-xs mt-1", children: ["VIX: ", regime.vix_level.toFixed(1)] })] })), allocation && (_jsxs("div", { className: "bg-gray-800 p-4 rounded-lg border border-gray-700", children: [_jsx("h3", { className: "text-gray-400 text-sm uppercase", children: "Projected Sharpe" }), _jsx("p", { className: `text-2xl font-bold mt-2 ${allocation.portfolio_sharpe_ratio > 1 ? 'text-green-500' : 'text-amber-500'}`, children: allocation.portfolio_sharpe_ratio.toFixed(2) }), _jsx("p", { className: "text-gray-500 text-xs mt-1", children: "Risk-adjusted return" })] })), simulation && (_jsxs("div", { className: "bg-gray-800 p-4 rounded-lg border border-gray-700", children: [_jsx("h3", { className: "text-gray-400 text-sm uppercase", children: "Correlation Drag" }), _jsxs("p", { className: "text-2xl font-bold text-blue-400 mt-2", children: ["-", simulation.diversification_ratio > 0 ? ((1 - 1 / simulation.diversification_ratio) * 100).toFixed(1) : '0.0', "%"] }), _jsxs("p", { className: "text-gray-500 text-xs mt-1", children: ["Diversification ratio: ", simulation.diversification_ratio.toFixed(2)] })] })), regime && (_jsxs("div", { className: "bg-gray-800 p-4 rounded-lg border border-gray-700", children: [_jsx("h3", { className: "text-gray-400 text-sm uppercase", children: "Recommendation" }), _jsx("p", { className: `text-lg font-bold mt-2 ${regime.recommended_action === 'Hold'
                                    ? 'text-green-500'
                                    : regime.recommended_action === 'Increase Risk'
                                        ? 'text-blue-500'
                                        : regime.recommended_action === 'Reduce Risk'
                                            ? 'text-red-500'
                                            : 'text-yellow-500'}`, children: regime.recommended_action }), _jsxs("p", { className: "text-gray-500 text-xs mt-1", children: [regime.explanation.substring(0, 40), "..."] })] }))] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-3 gap-8", children: [_jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Current Allocation" }), allocation ? (_jsxs("div", { className: "space-y-4", children: [_jsx("div", { className: "relative w-48 h-48 mx-auto", children: _jsx("svg", { viewBox: "0 0 200 200", className: "w-full h-full", children: generatePieChart(allocation.optimal_weights) }) }), _jsx("div", { className: "space-y-2 mt-6", children: Object.entries(allocation.optimal_weights).map(([strategy, weight]) => (_jsxs("div", { className: "flex justify-between items-center text-sm", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx("div", { className: "w-3 h-3 rounded-full", style: { backgroundColor: getStrategyColor(strategy) } }), _jsx("span", { className: "text-gray-300", children: strategy })] }), _jsxs("span", { className: "text-white font-mono", children: [(weight * 100).toFixed(1), "%"] })] }, strategy))) }), _jsxs("div", { className: "border-t border-gray-700 pt-4 mt-4 space-y-2", children: [_jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Expected Return:" }), _jsxs("span", { className: "text-green-400 font-mono", children: [allocation.portfolio_expected_return.toFixed(1), "%"] })] }), _jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Volatility:" }), _jsxs("span", { className: "text-amber-400 font-mono", children: [allocation.portfolio_volatility.toFixed(1), "%"] })] }), _jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Concentration (HHI):" }), _jsx("span", { className: "text-blue-400 font-mono", children: allocation.concentration_herfindahl.toFixed(2) })] })] })] })) : (_jsx("div", { className: "text-gray-400", children: "Loading allocation..." }))] }), _jsxs("div", { className: "space-y-8", children: [_jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Strategy Metrics" }), _jsx("div", { className: "space-y-4", children: strategies.map((strategy) => (_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between text-sm mb-1", children: [_jsx("span", { className: "text-gray-300", children: strategy.name }), _jsxs("span", { className: "text-gray-400", children: ["Sharpe: ", strategy.sharpe_ratio.toFixed(2)] })] }), _jsx("div", { className: "h-2 bg-gray-700 rounded overflow-hidden", children: _jsx("div", { className: "h-full bg-blue-500", style: {
                                                            width: `${Math.min((strategy.sharpe_ratio / 2) * 100, 100)}%`,
                                                        } }) }), _jsxs("div", { className: "flex justify-between text-xs text-gray-500 mt-1", children: [_jsxs("span", { children: ["Return: ", strategy.expected_return.toFixed(0), "%"] }), _jsxs("span", { children: ["Vol: ", strategy.volatility.toFixed(0), "%"] })] })] }, strategy.name))) })] }), simulation && (_jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Risk Summary" }), _jsxs("div", { className: "space-y-3", children: [_jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Sharpe Ratio:" }), _jsx("span", { className: "text-green-400 font-mono", children: simulation.sharpe_ratio.toFixed(2) })] }), _jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Sortino Ratio:" }), _jsx("span", { className: "text-green-400 font-mono", children: simulation.sortino_ratio.toFixed(2) })] }), _jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Max Drawdown:" }), _jsxs("span", { className: "text-red-400 font-mono", children: [simulation.max_drawdown_worst.toFixed(1), "%"] })] }), _jsxs("div", { className: "flex justify-between text-sm", children: [_jsx("span", { className: "text-gray-400", children: "Prob. Profitable:" }), _jsxs("span", { className: "text-green-400 font-mono", children: [simulation.probability_profitable.toFixed(1), "%"] })] })] })] }))] }), _jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Drawdown Distribution" }), simulation && simulation.drawdown_distribution.length > 0 ? (_jsxs("div", { children: [_jsx("div", { className: "h-64 flex items-end justify-start gap-1 px-2 py-4", children: simulation.drawdown_distribution.slice(0, 15).map((dd, idx) => {
                                            const maxFreq = Math.max(...simulation.drawdown_distribution.map((d) => d.frequency));
                                            const height = (dd.frequency / maxFreq) * 100;
                                            return (_jsx("div", { className: "flex-1 bg-red-500 rounded-t", style: { height: `${height}%`, minHeight: '2px' }, title: `DD: ${(dd.drawdown * 100).toFixed(1)}% - Freq: ${dd.frequency}` }, idx));
                                        }) }), _jsx("div", { className: "text-xs text-gray-500 text-center mt-2", children: "Drawdown Severity (% of simulations)" })] })) : (_jsx("div", { className: "text-gray-400", children: "Loading drawdown data..." }))] })] }), simulation && simulation.equity_curve.length > 0 && (_jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700 mt-8", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Equity Curve (1000-Run Monte Carlo)" }), _jsx("div", { className: "h-64 flex items-end justify-between gap-1", children: simulation.equity_curve.map((point, idx) => {
                            const maxVal = Math.max(...simulation.equity_curve.map((p) => p.percentile_95));
                            const minVal = Math.min(...simulation.equity_curve.map((p) => p.percentile_5));
                            const range = maxVal - minVal;
                            return (_jsxs("div", { className: "relative flex-1 h-full", style: {
                                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                                }, children: [_jsx("div", { className: "absolute w-full bg-gray-700", style: {
                                            bottom: `${((point.percentile_5 - minVal) / range) * 100}%`,
                                            height: `${((point.percentile_95 - point.percentile_5) / range) * 100}%`,
                                            opacity: 0.3,
                                        } }), _jsx("div", { className: "absolute w-full border-b border-blue-400", style: {
                                            bottom: `${((point.median - minVal) / range) * 100}%`,
                                        } })] }, idx));
                        }) }), _jsx("div", { className: "text-xs text-gray-500 text-center mt-2", children: "Bands: 5th-95th percentiles | Line: Median" })] })), regime && (_jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700 mt-8", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-4", children: "Regime Assessment" }), _jsx("p", { className: "text-gray-300 mb-4", children: regime.explanation }), _jsxs("div", { className: "grid grid-cols-2 gap-4", children: [_jsxs("div", { children: [_jsx("h3", { className: "text-white font-semibold text-sm mb-2", children: "Base Weights" }), _jsx("div", { className: "space-y-1 text-sm text-gray-400", children: strategies.map((s) => (_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { children: s.name }), _jsxs("span", { children: [(s.weight * 100).toFixed(1), "%"] })] }, s.name))) })] }), _jsxs("div", { children: [_jsx("h3", { className: "text-white font-semibold text-sm mb-2", children: "Regime-Adjusted" }), _jsx("div", { className: "space-y-1 text-sm text-gray-400", children: Object.entries(regime.regime_adjusted_weights).map(([name, weight]) => (_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { children: name }), _jsxs("span", { className: weight > (strategies.find(s => s.name === name)?.weight || 0) ? 'text-green-400' : 'text-red-400', children: [(weight * 100).toFixed(1), "%"] })] }, name))) })] })] })] }))] }));
};
// Helper function to generate pie chart SVG
function generatePieChart(weights) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];
    const strategies = Object.keys(weights);
    let currentAngle = 0;
    const cx = 100;
    const cy = 100;
    const r = 80;
    return strategies.map((strategy, idx) => {
        const percentage = weights[strategy];
        const angle = percentage * 360;
        const startAngle = currentAngle;
        const endAngle = currentAngle + angle;
        currentAngle = endAngle;
        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;
        const x1 = cx + r * Math.cos(startRad);
        const y1 = cy + r * Math.sin(startRad);
        const x2 = cx + r * Math.cos(endRad);
        const y2 = cy + r * Math.sin(endRad);
        const largeArc = angle > 180 ? 1 : 0;
        const d = [
            `M ${cx} ${cy}`,
            `L ${x1} ${y1}`,
            `A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`,
            'Z',
        ].join(' ');
        return (_jsx("path", { d: d, fill: colors[idx % colors.length], stroke: "#1a202c", strokeWidth: "2" }, strategy));
    });
}
// Helper function to get strategy color
function getStrategyColor(strategy) {
    const colors = {
        MLB: '#FF6B6B',
        Crypto: '#4ECDC4',
        Earnings: '#45B7D1',
        AI: '#FFA07A',
        Econ: '#98D8C8',
    };
    return colors[strategy] || '#95a5a6';
}
