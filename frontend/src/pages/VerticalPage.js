import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
const VERTICAL_INFO = {
    mlb: {
        name: 'MLB Props',
        icon: '⚾',
        description: 'Pitcher strikeout predictions',
        color: 'blue',
    },
    'ai-releases': {
        name: 'AI Releases',
        icon: '⚡',
        description: 'AI model release predictions',
        color: 'purple',
    },
    economics: {
        name: 'Fed & Economics',
        icon: '📊',
        description: 'Economic indicator predictions',
        color: 'green',
    },
    earnings: {
        name: 'Company Earnings',
        icon: '📈',
        description: 'Earnings beat/miss predictions',
        color: 'amber',
    },
    crypto: {
        name: 'Crypto Events',
        icon: '₿',
        description: 'Crypto market predictions',
        color: 'orange',
    },
};
export function VerticalPage() {
    const { vertical } = useParams();
    const [predictions, setPredictions] = useState([]);
    const [model, setModel] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const info = VERTICAL_INFO[vertical || ''] || { name: 'Unknown', icon: '?', description: '' };
    useEffect(() => {
        const fetchPredictions = async () => {
            try {
                const response = await fetch(`/api/verticals/${vertical}`);
                const data = await response.json();
                setPredictions(data.predictions || []);
                setModel(data.model || '');
            }
            catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load predictions');
            }
            finally {
                setLoading(false);
            }
        };
        if (vertical) {
            fetchPredictions();
        }
    }, [vertical]);
    const getEdgeColor = (edge) => {
        const a = Math.abs(edge);
        if (a >= 0.04)
            return edge > 0 ? 'text-green-400' : 'text-red-400';
        if (a >= 0.02)
            return 'text-yellow-400';
        return 'text-gray-400';
    };
    const getActionColor = (action) => {
        if (action.startsWith('BUY YES'))
            return 'bg-green-900 text-green-200';
        if (action.startsWith('BUY NO'))
            return 'bg-red-900 text-red-200';
        return 'bg-gray-700 text-gray-200';
    };
    const fmtMoney = (n) => {
        if (!n)
            return '—';
        if (n >= 1000000)
            return `$${(n / 1000000).toFixed(1)}M`;
        if (n >= 1000)
            return `$${(n / 1000).toFixed(0)}k`;
        return `$${n}`;
    };
    return (_jsxs("div", { className: "min-h-screen bg-gray-900 text-white", children: [_jsx("div", { className: "bg-gradient-to-r from-gray-800 to-gray-900 py-12 px-4 border-b border-gray-700", children: _jsxs("div", { className: "max-w-6xl mx-auto", children: [_jsx(Link, { to: "/", className: "text-blue-400 hover:text-blue-300 mb-4 inline-block", children: "\u2190 Back to All Markets" }), _jsxs("div", { className: "flex items-center gap-4", children: [_jsx("div", { className: "text-5xl", children: info.icon }), _jsxs("div", { children: [_jsx("h1", { className: "text-4xl font-bold", children: info.name }), _jsx("p", { className: "text-gray-400", children: info.description }), model && (_jsxs("p", { className: "text-xs text-gray-500 mt-2", children: [_jsx("span", { className: "inline-block w-2 h-2 rounded-full bg-green-400 mr-2 animate-pulse" }), "Live markets from Polymarket \u00B7 ", model] }))] })] })] }) }), _jsxs("div", { className: "max-w-6xl mx-auto px-4 py-12", children: [loading && (_jsx("div", { className: "text-center text-gray-400", children: "Loading predictions..." })), error && (_jsxs("div", { className: "bg-red-900 border border-red-700 rounded-lg p-4 text-red-200", children: ["Error: ", error] })), !loading && !error && predictions.length === 0 && (_jsx("div", { className: "text-center text-gray-400", children: "No predictions available yet" })), !loading && !error && predictions.length > 0 && (_jsxs("div", { children: [_jsx("h2", { className: "text-2xl font-bold mb-6", children: "Top Opportunities" }), _jsx("div", { className: "space-y-4", children: predictions.map((pred, idx) => (_jsxs("div", { className: "bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition", children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-6 gap-4 items-center", children: [_jsxs("div", { className: "md:col-span-2", children: [_jsx("h3", { className: "text-lg font-bold", children: pred.event }), pred.signal && (_jsxs("p", { className: "text-xs text-gray-500 mt-1", children: ["signal: ", pred.signal] }))] }), _jsxs("div", { className: "text-center", children: [_jsx("p", { className: "text-xs text-gray-400 mb-1", children: "Book Price" }), _jsxs("p", { className: "text-lg font-bold", children: [(pred.market_price * 100).toFixed(0), "%"] })] }), _jsxs("div", { className: "text-center", children: [_jsx("p", { className: "text-xs text-gray-400 mb-1", children: "Model Prob" }), _jsxs("p", { className: "text-lg font-bold", children: [(pred.model_probability * 100).toFixed(0), "%"] })] }), _jsxs("div", { className: "text-center", children: [_jsx("p", { className: "text-xs text-gray-400 mb-1", children: "Edge" }), _jsxs("p", { className: `text-lg font-bold ${getEdgeColor(pred.edge)}`, children: [(pred.edge * 100).toFixed(1), "%"] })] }), _jsx("div", { className: "text-center", children: _jsx("p", { className: `inline-block px-3 py-1 rounded font-bold text-sm ${getActionColor(pred.action)}`, children: pred.action }) })] }), _jsxs("div", { className: "mt-4 pt-4 border-t border-gray-700 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm", children: [_jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Kelly %" }), _jsxs("p", { className: "font-bold", children: [(pred.kelly * 100).toFixed(2), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Confidence" }), _jsx("p", { className: "font-bold capitalize", children: pred.confidence })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Liquidity" }), _jsx("p", { className: "font-bold", children: fmtMoney(pred.liquidity) })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Market" }), pred.url ? (_jsx("a", { href: pred.url, target: "_blank", rel: "noopener noreferrer", className: "font-bold text-blue-400 hover:text-blue-300", children: "View on Polymarket \u2192" })) : (_jsx("p", { className: "font-bold", children: "\u2014" }))] })] })] }, idx))) })] }))] })] }));
}
