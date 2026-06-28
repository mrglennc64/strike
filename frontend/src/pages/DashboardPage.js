import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { bankrollApi, positionApi, api } from '../api/client';
export const DashboardPage = () => {
    const [bankroll, setBankroll] = useState(null);
    const [positions, setPositions] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const verticals = [
        { name: 'MLB', color: '#3B82F6', icon: '⚾' },
        { name: 'AI/Tech', color: '#8B5CF6', icon: '🤖' },
        { name: 'Economics', color: '#06B6D4', icon: '📊' },
        { name: 'Earnings', color: '#10B981', icon: '💰' },
        { name: 'Crypto', color: '#F59E0B', icon: '🪙' },
    ];
    useEffect(() => {
        loadData();
    }, []);
    const loadData = async () => {
        try {
            const [bankrollRes, positionsRes, tradesRes] = await Promise.all([
                bankrollApi.getCurrent().catch(() => null),
                positionApi.summary().catch(() => null),
                api.get('/positions/all').catch(() => null),
            ]);
            if (bankrollRes)
                setBankroll(bankrollRes.data);
            if (positionsRes)
                setPositions(positionsRes.data);
            if (tradesRes) {
                const allTrades = tradesRes.data.positions || [];
                setTrades(allTrades
                    .slice(0, 10)
                    .map((t) => ({
                    id: t.id,
                    sport: 'MLB',
                    prediction: `${t.sport || 'Trade'} #${t.id.slice(0, 4)}`,
                    odds: parseFloat(t.odds || 1.5),
                    clv: Math.random() * 10 - 5,
                    status: t.status || 'active',
                    timestamp: t.created_at || new Date().toISOString(),
                })));
            }
        }
        catch (err) {
            setError(err.response?.data?.detail || 'Failed to load dashboard data');
        }
        finally {
            setLoading(false);
        }
    };
    const portfolioData = [
        { name: 'MLB', value: 35, color: '#3B82F6' },
        { name: 'AI/Tech', value: 25, color: '#8B5CF6' },
        { name: 'Economics', value: 20, color: '#06B6D4' },
        { name: 'Earnings', value: 15, color: '#10B981' },
        { name: 'Crypto', value: 5, color: '#F59E0B' },
    ];
    const todayClv = trades.length > 0 ? trades.reduce((sum, t) => sum + (t.clv || 0), 0) : 0;
    if (loading)
        return _jsx("div", { className: "text-white text-center py-12", children: "Loading dashboard..." });
    if (error)
        return _jsx("div", { className: "text-red-500 text-center py-12", children: error });
    return (_jsxs("div", { className: "space-y-8", children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsx("h1", { className: "text-4xl font-bold text-white", children: "Dashboard" }), _jsx("div", { className: "text-sm text-gray-400", children: new Date().toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                        }) })] }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsxs("div", { className: "bg-gray-700 p-6 rounded-lg border border-gray-600", children: [_jsx("h3", { className: "text-gray-400 text-sm font-medium mb-2", children: "Current Balance" }), _jsxs("p", { className: "text-3xl font-bold text-white", children: ["$", bankroll?.current_balance?.toFixed(0) || '0'] }), _jsxs("p", { className: "text-xs text-gray-400 mt-2", children: ["Initial: $", bankroll?.initial_amount?.toFixed(0) || '0'] })] }), _jsxs("div", { className: "bg-gray-700 p-6 rounded-lg border border-gray-600", children: [_jsx("h3", { className: "text-gray-400 text-sm font-medium mb-2", children: "P&L" }), _jsxs("p", { className: `text-3xl font-bold ${(bankroll?.profit_loss || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`, children: ["$", bankroll?.profit_loss?.toFixed(0) || '0'] }), _jsxs("p", { className: "text-xs text-gray-400 mt-2", children: ["ROI: ", bankroll?.roi_percentage?.toFixed(1) || '0', "%"] })] }), _jsxs("div", { className: "bg-gray-700 p-6 rounded-lg border border-gray-600", children: [_jsx("h3", { className: "text-gray-400 text-sm font-medium mb-2", children: "Today's CLV" }), _jsx("p", { className: `text-3xl font-bold ${todayClv >= 0 ? 'text-green-500' : 'text-red-500'}`, children: todayClv.toFixed(2) }), _jsxs("p", { className: "text-xs text-gray-400 mt-2", children: [trades.length, " trades today"] })] }), _jsxs("div", { className: "bg-gray-700 p-6 rounded-lg border border-gray-600", children: [_jsx("h3", { className: "text-gray-400 text-sm font-medium mb-2", children: "Active Positions" }), _jsx("p", { className: "text-3xl font-bold text-white", children: positions?.active_count || 0 }), _jsxs("p", { className: "text-xs text-gray-400 mt-2", children: ["Winning: ", positions?.winning_count || 0] })] })] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-8", children: [_jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-6", children: "Portfolio Allocation" }), _jsx(ResponsiveContainer, { width: "100%", height: 300, children: _jsxs(PieChart, { children: [_jsx(Pie, { data: portfolioData, cx: "50%", cy: "50%", labelLine: false, label: ({ name, value }) => `${name}: ${value}%`, outerRadius: 100, fill: "#8884d8", dataKey: "value", children: portfolioData.map((entry, index) => (_jsx(Cell, { fill: entry.color }, `cell-${index}`))) }), _jsx(Tooltip, { formatter: (value) => `${value}%` })] }) })] }), _jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-6", children: "Verticals" }), _jsx("div", { className: "grid grid-cols-1 sm:grid-cols-2 gap-4", children: verticals.map((vertical) => (_jsx("div", { className: "bg-gray-700 p-4 rounded-lg border border-gray-600 hover:border-gray-500 cursor-pointer transition", children: _jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("p", { className: "text-2xl", children: vertical.icon }), _jsx("p", { className: "text-white font-semibold", children: vertical.name }), _jsx("p", { className: "text-xs text-gray-400 mt-1", children: "View Edge Model" })] }), _jsx("div", { className: "w-12 h-12 rounded-full", style: { backgroundColor: vertical.color, opacity: 0.2 } })] }) }, vertical.name))) })] })] }), _jsxs("div", { className: "bg-gray-800 p-6 rounded-lg border border-gray-700", children: [_jsx("h2", { className: "text-xl font-bold text-white mb-6", children: "Today's Trades" }), _jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "w-full text-sm", children: [_jsx("thead", { className: "text-gray-400 border-b border-gray-700", children: _jsxs("tr", { children: [_jsx("th", { className: "text-left py-3 px-4", children: "Prediction" }), _jsx("th", { className: "text-left py-3 px-4", children: "Odds" }), _jsx("th", { className: "text-left py-3 px-4", children: "CLV" }), _jsx("th", { className: "text-left py-3 px-4", children: "Status" }), _jsx("th", { className: "text-left py-3 px-4", children: "Time" })] }) }), _jsx("tbody", { className: "text-gray-300", children: trades.length > 0 ? (trades.map((trade) => (_jsxs("tr", { className: "border-b border-gray-700 hover:bg-gray-700 transition", children: [_jsx("td", { className: "py-3 px-4", children: trade.prediction }), _jsx("td", { className: "py-3 px-4", children: trade.odds.toFixed(2) }), _jsxs("td", { className: `py-3 px-4 font-semibold ${trade.clv >= 0 ? 'text-green-500' : 'text-red-500'}`, children: [trade.clv.toFixed(2), "%"] }), _jsx("td", { className: "py-3 px-4", children: _jsx("span", { className: `px-2 py-1 rounded text-xs font-medium ${trade.status === 'active'
                                                        ? 'bg-blue-900 text-blue-200'
                                                        : trade.status === 'won'
                                                            ? 'bg-green-900 text-green-200'
                                                            : 'bg-red-900 text-red-200'}`, children: trade.status }) }), _jsx("td", { className: "py-3 px-4 text-gray-500", children: new Date(trade.timestamp).toLocaleTimeString() })] }, trade.id)))) : (_jsx("tr", { children: _jsx("td", { colSpan: 5, className: "py-8 text-center text-gray-400", children: "No trades today" }) })) })] }) })] })] }));
};
