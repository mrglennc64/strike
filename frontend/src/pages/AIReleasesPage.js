import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { api } from '../api/client';
export const AIReleasesPage = () => {
    const [provider, setProvider] = useState('anthropic');
    const [modelName, setModelName] = useState('Claude 4');
    const [targetDate, setTargetDate] = useState(new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
    const [selectedPrediction, setSelectedPrediction] = useState(null);
    const [examples, setExamples] = useState([]);
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        loadExamples();
    }, []);
    const loadExamples = async () => {
        try {
            const response = await api.get('/verticals/ai-releases/examples').catch(() => ({ data: { predictions: [] } }));
            setExamples(response.data.predictions || []);
        }
        catch (err) {
            console.error('Failed to load examples', err);
        }
    };
    const handlePredict = async () => {
        setLoading(true);
        try {
            const response = await api.post('/verticals/ai-releases/predict', {
                provider,
                model_name: modelName,
                target_date: targetDate,
            }).catch(() => ({ data: null }));
            if (response.data) {
                setSelectedPrediction(response.data);
            }
        }
        catch (err) {
            console.error('Failed to generate prediction', err);
        }
        finally {
            setLoading(false);
        }
    };
    const getRecommendationColor = (recommendation) => {
        switch (recommendation) {
            case 'STRONG_BUY':
                return 'bg-green-900 text-green-200';
            case 'BUY':
                return 'bg-emerald-900 text-emerald-200';
            case 'HOLD':
                return 'bg-gray-700 text-gray-200';
            case 'SELL':
                return 'bg-orange-900 text-orange-200';
            case 'STRONG_SELL':
                return 'bg-red-900 text-red-200';
            default:
                return 'bg-gray-700 text-gray-200';
        }
    };
    const getProviderColor = (prov) => {
        switch (prov) {
            case 'anthropic':
                return 'bg-blue-900 text-blue-200';
            case 'openai':
                return 'bg-purple-900 text-purple-200';
            case 'xai':
                return 'bg-red-900 text-red-200';
            default:
                return 'bg-gray-700 text-gray-200';
        }
    };
    return (_jsx("div", { className: "min-h-screen bg-gray-900 p-8", children: _jsxs("div", { className: "max-w-7xl mx-auto", children: [_jsxs("div", { className: "mb-8", children: [_jsx("h1", { className: "text-4xl font-bold text-white mb-2", children: "AI Release Predictor" }), _jsx("p", { className: "text-gray-400", children: "Predict when Claude, GPT, and Grok will be released. Trade on Polymarket with edge." })] }), _jsxs("div", { className: "bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700", children: [_jsx("h2", { className: "text-xl font-semibold text-white mb-4", children: "Generate Prediction" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4", children: [_jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-300 mb-2", children: "AI Provider" }), _jsxs("select", { value: provider, onChange: (e) => setProvider(e.target.value), className: "w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none", children: [_jsx("option", { value: "anthropic", children: "Anthropic (Claude)" }), _jsx("option", { value: "openai", children: "OpenAI (GPT)" }), _jsx("option", { value: "xai", children: "xAI (Grok)" })] })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-300 mb-2", children: "Model Name" }), _jsx("input", { type: "text", value: modelName, onChange: (e) => setModelName(e.target.value), placeholder: "e.g., Claude 4", className: "w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-300 mb-2", children: "Target Date" }), _jsx("input", { type: "date", value: targetDate, onChange: (e) => setTargetDate(e.target.value), className: "w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none" })] }), _jsx("div", { className: "flex items-end", children: _jsx("button", { onClick: handlePredict, disabled: loading, className: "w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded transition-colors", children: loading ? 'Predicting...' : 'Predict' }) })] }), selectedPrediction && (_jsx("div", { className: "mt-6 bg-gray-700 rounded p-4 border border-gray-600", children: _jsxs("div", { className: "grid grid-cols-2 md:grid-cols-5 gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-gray-400 text-sm", children: "Model Probability" }), _jsxs("p", { className: "text-white font-bold text-lg", children: [(selectedPrediction.predicted_probability * 100).toFixed(1), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400 text-sm", children: "Market Price" }), _jsxs("p", { className: "text-white font-bold text-lg", children: [(selectedPrediction.polymarket_price * 100).toFixed(1), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400 text-sm", children: "Edge" }), _jsxs("p", { className: `font-bold text-lg ${selectedPrediction.edge >= 0 ? 'text-green-400' : 'text-red-400'}`, children: [(selectedPrediction.edge * 100).toFixed(2), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400 text-sm", children: "Recommendation" }), _jsx("span", { className: `inline-block px-3 py-1 rounded text-sm font-medium ${getRecommendationColor(selectedPrediction.recommendation)}`, children: selectedPrediction.recommendation })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400 text-sm", children: "Confidence" }), _jsxs("p", { className: "text-white font-bold text-lg", children: [(selectedPrediction.confidence * 100).toFixed(1), "%"] })] })] }) }))] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-8", children: [_jsxs("div", { className: "bg-gray-800 rounded-lg p-6 border border-gray-700", children: [_jsx("h2", { className: "text-xl font-semibold text-white mb-4", children: "Example Predictions" }), examples.length > 0 ? (_jsx("div", { className: "space-y-4", children: examples.map((pred, idx) => (_jsxs("div", { onClick: () => setSelectedPrediction(pred), className: "bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-600 transition-colors border border-gray-600", children: [_jsxs("div", { className: "flex items-start justify-between mb-2", children: [_jsxs("div", { children: [_jsx("p", { className: "text-white font-medium", children: pred.model_name }), _jsx("span", { className: `inline-block px-2 py-1 rounded text-xs font-medium mt-1 ${getProviderColor(pred.provider)}`, children: pred.provider })] }), _jsx("span", { className: `inline-block px-2 py-1 rounded text-xs font-medium ${getRecommendationColor(pred.recommendation)}`, children: pred.recommendation })] }), _jsxs("div", { className: "grid grid-cols-3 gap-2 text-sm", children: [_jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Prob" }), _jsxs("p", { className: "text-white font-bold", children: [(pred.predicted_probability * 100).toFixed(1), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Price" }), _jsxs("p", { className: "text-white font-bold", children: [(pred.polymarket_price * 100).toFixed(1), "%"] })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Edge" }), _jsxs("p", { className: `font-bold ${pred.edge >= 0 ? 'text-green-400' : 'text-red-400'}`, children: [(pred.edge * 100).toFixed(2), "%"] })] })] })] }, idx))) })) : (_jsx("p", { className: "text-gray-400", children: "No examples available" }))] }), _jsxs("div", { className: "bg-gray-800 rounded-lg p-6 border border-gray-700", children: [_jsx("h2", { className: "text-xl font-semibold text-white mb-4", children: "About AI Releases" }), _jsxs("div", { className: "space-y-4 text-gray-300", children: [_jsx("p", { children: "Trade predictions on when new AI models will be released. Anthropic (Claude), OpenAI (GPT), and xAI (Grok) are the primary markets." }), _jsxs("div", { children: [_jsx("h3", { className: "text-white font-semibold mb-2", children: "How it works:" }), _jsxs("ul", { className: "list-disc list-inside space-y-1 text-sm", children: [_jsx("li", { children: "Select AI provider and target release date" }), _jsx("li", { children: "Model generates probability prediction" }), _jsx("li", { children: "Compare with Polymarket prices for edge" }), _jsx("li", { children: "Trade on Polymarket or other prediction markets" })] })] }), _jsxs("div", { children: [_jsx("h3", { className: "text-white font-semibold mb-2", children: "Model inputs:" }), _jsxs("ul", { className: "list-disc list-inside space-y-1 text-sm", children: [_jsx("li", { children: "Historical release cadences" }), _jsx("li", { children: "Company announcements and timelines" }), _jsx("li", { children: "Industry trends and competitive pressure" }), _jsx("li", { children: "Market sentiment from social media" })] })] })] })] })] })] }) }));
};
