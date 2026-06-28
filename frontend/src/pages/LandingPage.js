import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from 'react-router-dom';
const verticals = [
    {
        id: 'mlb',
        name: 'MLB Props',
        icon: '⚾',
        description: 'Pitcher strikeout predictions vs DraftKings/FanDuel',
        color: 'from-blue-600 to-blue-800',
        path: '/verticals/mlb',
        markets: ['DraftKings', 'FanDuel'],
    },
    {
        id: 'ai-releases',
        name: 'AI Releases',
        icon: '⚡',
        description: 'Claude, GPT, xAI release date predictions',
        color: 'from-purple-600 to-purple-800',
        path: '/verticals/ai-releases',
        markets: ['Polymarket'],
    },
    {
        id: 'economics',
        name: 'Fed & Economics',
        icon: '📊',
        description: 'CPI, interest rates, unemployment predictions',
        color: 'from-green-600 to-green-800',
        path: '/verticals/economics',
        markets: ['Polymarket', 'Kalshi'],
    },
    {
        id: 'earnings',
        name: 'Company Earnings',
        icon: '📈',
        description: 'Beat/miss probability predictions',
        color: 'from-amber-600 to-amber-800',
        path: '/verticals/earnings',
        markets: ['Options Market'],
    },
    {
        id: 'crypto',
        name: 'Crypto Events',
        icon: '₿',
        description: 'Bitcoin price targets, ETF approvals, milestones',
        color: 'from-orange-600 to-orange-800',
        path: '/verticals/crypto',
        markets: ['Polymarket'],
    },
];
export function LandingPage() {
    return (_jsxs("div", { className: "min-h-screen bg-gray-900 text-white", children: [_jsx("div", { className: "bg-gradient-to-r from-gray-900 to-gray-800 py-20 px-4", children: _jsxs("div", { className: "max-w-6xl mx-auto text-center", children: [_jsx("h1", { className: "text-5xl font-bold mb-4", children: "Edge AI" }), _jsx("p", { className: "text-xl text-gray-300 mb-8", children: "Multi-Vertical Prediction Platform" }), _jsx("p", { className: "text-lg text-gray-400", children: "Identify market mispricings across sports, economics, AI releases, earnings, and crypto" })] }) }), _jsxs("div", { className: "max-w-6xl mx-auto px-4 py-16", children: [_jsx("h2", { className: "text-3xl font-bold mb-12 text-center", children: "Choose Your Market" }), _jsx("div", { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4", children: verticals.map((vertical) => (_jsx(Link, { to: vertical.path, className: "group", children: _jsxs("div", { className: `bg-gradient-to-br ${vertical.color} rounded-lg p-6 h-full transform transition hover:scale-105 hover:shadow-2xl`, children: [_jsx("div", { className: "text-4xl mb-4", children: vertical.icon }), _jsx("h3", { className: "text-xl font-bold mb-2", children: vertical.name }), _jsx("p", { className: "text-sm text-gray-100 mb-4", children: vertical.description }), _jsx("div", { className: "flex flex-wrap gap-1", children: vertical.markets.map((market) => (_jsx("span", { className: "text-xs bg-black bg-opacity-30 px-2 py-1 rounded", children: market }, market))) })] }) }, vertical.id))) })] }), _jsx("div", { className: "bg-gray-800 py-16 px-4 mt-16", children: _jsxs("div", { className: "max-w-6xl mx-auto", children: [_jsx("h2", { className: "text-3xl font-bold mb-12 text-center", children: "How It Works" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-8", children: [_jsxs("div", { className: "text-center", children: [_jsx("div", { className: "text-3xl mb-4", children: "\uD83D\uDCCA" }), _jsx("h3", { className: "text-lg font-bold mb-2", children: "Collect Data" }), _jsx("p", { className: "text-gray-300", children: "Aggregate data from multiple sources" })] }), _jsxs("div", { className: "text-center", children: [_jsx("div", { className: "text-3xl mb-4", children: "\uD83E\uDDE0" }), _jsx("h3", { className: "text-lg font-bold mb-2", children: "Predict" }), _jsx("p", { className: "text-gray-300", children: "AI models estimate true probability" })] }), _jsxs("div", { className: "text-center", children: [_jsx("div", { className: "text-3xl mb-4", children: "\u2696\uFE0F" }), _jsx("h3", { className: "text-lg font-bold mb-2", children: "Compare" }), _jsx("p", { className: "text-gray-300", children: "Compare to market implied probability" })] }), _jsxs("div", { className: "text-center", children: [_jsx("div", { className: "text-3xl mb-4", children: "\uD83D\uDCB0" }), _jsx("h3", { className: "text-lg font-bold mb-2", children: "Act" }), _jsx("p", { className: "text-gray-300", children: "Kelly-sized bets on mispricings" })] })] })] }) }), _jsxs("div", { className: "max-w-4xl mx-auto px-4 py-16 text-center", children: [_jsx("h2", { className: "text-3xl font-bold mb-6", children: "Ready to Find Edges?" }), _jsx(Link, { to: "/verticals/mlb", className: "bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg text-lg inline-block transition", children: "Start with MLB Props" })] })] }));
}
