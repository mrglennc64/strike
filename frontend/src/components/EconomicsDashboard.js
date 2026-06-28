import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
export const EconomicsDashboard = () => {
    const [cpiPrediction, setCPIPrediction] = useState(null);
    const [rateCutPrediction, setRateCutPrediction] = useState(null);
    const [edgeOpportunities, setEdgeOpportunities] = useState([]);
    const [fomc, setFOmc] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);
    const fetchData = async () => {
        try {
            setLoading(true);
            const [cpiRes, rateRes, edgeRes, fomcRes] = await Promise.all([
                fetch('/api/verticals/economics/predict-cpi'),
                fetch('/api/verticals/economics/predict-rate-cut'),
                fetch('/api/verticals/economics/edge-opportunities'),
                fetch('/api/verticals/economics/fomc-schedule'),
            ]);
            if (cpiRes.ok) {
                const cpiData = await cpiRes.json();
                setCPIPrediction(cpiData.data);
            }
            if (rateRes.ok) {
                const rateData = await rateRes.json();
                setRateCutPrediction(rateData.data);
            }
            if (edgeRes.ok) {
                const edgeData = await edgeRes.json();
                setEdgeOpportunities(edgeData.data || []);
            }
            if (fomcRes.ok) {
                const fomcData = await fomcRes.json();
                setFOmc(fomcData.data || []);
            }
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch data');
        }
        finally {
            setLoading(false);
        }
    };
    if (loading) {
        return _jsx("div", { className: "p-8 text-center text-gray-500", children: "Loading economics data..." });
    }
    return (_jsxs("div", { className: "p-8 bg-gray-50", children: [_jsx("h1", { className: "text-4xl font-bold mb-8 text-gray-900", children: "Fed/Economics Predictor" }), error && (_jsx("div", { className: "mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700", children: error })), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8", children: [_jsx(CPIPredictionCard, { prediction: cpiPrediction }), _jsx(RateCutPredictionCard, { prediction: rateCutPrediction })] }), edgeOpportunities.length > 0 && (_jsx(EdgeOpportunitiesPanel, { opportunities: edgeOpportunities })), fomc.length > 0 && (_jsx(FOCMSchedulePanel, { meetings: fomc }))] }));
};
const CPIPredictionCard = ({ prediction }) => {
    if (!prediction) {
        return (_jsxs("div", { className: "bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500", children: [_jsx("h2", { className: "text-xl font-semibold mb-4 text-gray-900", children: "CPI Prediction" }), _jsx("p", { className: "text-gray-500", children: "Unable to load CPI prediction" })] }));
    }
    const { edge } = prediction;
    const edgeColor = edge.edge > 0 ? 'text-green-600' : 'text-red-600';
    const bgColor = edge.edge > 0 ? 'bg-green-50' : 'bg-red-50';
    return (_jsxs("div", { className: `${bgColor} p-6 rounded-lg shadow-md border-l-4 border-blue-500`, children: [_jsx("h2", { className: "text-xl font-semibold mb-4 text-gray-900", children: "CPI Prediction" }), _jsxs("div", { className: "mb-4", children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsx("span", { className: "text-gray-600", children: "Threshold" }), _jsxs("span", { className: "font-semibold text-lg", children: [prediction.threshold, "%"] })] }), _jsxs("div", { className: "flex justify-between items-center mt-2", children: [_jsx("span", { className: "text-gray-600", children: "Latest Value" }), _jsxs("span", { className: "font-semibold text-lg", children: [prediction.latest_value?.toFixed(2), "%"] })] })] }), _jsxs("div", { className: "grid grid-cols-2 gap-4 mb-4", children: [_jsxs("div", { className: "bg-white p-3 rounded", children: [_jsx("div", { className: "text-sm text-gray-600", children: "Model Prediction" }), _jsxs("div", { className: "text-2xl font-bold text-blue-600", children: [(prediction.predicted_probability * 100).toFixed(1), "%"] })] }), _jsxs("div", { className: "bg-white p-3 rounded", children: [_jsx("div", { className: "text-sm text-gray-600", children: "Market Price" }), _jsxs("div", { className: "text-2xl font-bold text-gray-700", children: [(prediction.market_probability * 100).toFixed(1), "%"] })] })] }), _jsxs("div", { className: "bg-white p-3 rounded mb-4", children: [_jsxs("div", { className: `text-sm font-semibold ${edgeColor}`, children: ["Edge: ", edge.edge.toFixed(3), " (", edge.edge_pct.toFixed(1), "%)"] }), _jsxs("div", { className: "text-sm text-gray-600 mt-1", children: ["Kelly: ", (edge.kelly_fraction * 100).toFixed(1), "%"] }), _jsxs("div", { className: "text-sm text-gray-600", children: ["Best Side: ", edge.best_side] })] }), _jsx("button", { className: "w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition", children: "View Details" })] }));
};
const RateCutPredictionCard = ({ prediction }) => {
    if (!prediction) {
        return (_jsxs("div", { className: "bg-white p-6 rounded-lg shadow-md border-l-4 border-green-500", children: [_jsx("h2", { className: "text-xl font-semibold mb-4 text-gray-900", children: "Rate Cut Prediction" }), _jsx("p", { className: "text-gray-500", children: "Unable to load rate cut prediction" })] }));
    }
    const { edge } = prediction;
    const edgeColor = edge.edge > 0 ? 'text-green-600' : 'text-red-600';
    const bgColor = edge.edge > 0 ? 'bg-green-50' : 'bg-red-50';
    return (_jsxs("div", { className: `${bgColor} p-6 rounded-lg shadow-md border-l-4 border-green-500`, children: [_jsx("h2", { className: "text-xl font-semibold mb-4 text-gray-900", children: "Rate Cut Prediction" }), _jsxs("div", { className: "mb-4", children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsx("span", { className: "text-gray-600", children: "Current Fed Rate" }), _jsxs("span", { className: "font-semibold text-lg", children: [prediction.current_rate?.toFixed(2), "%"] })] }), prediction.next_meeting && (_jsxs("div", { className: "flex justify-between items-center mt-2", children: [_jsx("span", { className: "text-gray-600", children: "Next Meeting" }), _jsx("span", { className: "font-semibold text-lg", children: new Date(prediction.next_meeting.date).toLocaleDateString() })] }))] }), _jsxs("div", { className: "grid grid-cols-2 gap-4 mb-4", children: [_jsxs("div", { className: "bg-white p-3 rounded", children: [_jsx("div", { className: "text-sm text-gray-600", children: "Model Prediction" }), _jsxs("div", { className: "text-2xl font-bold text-green-600", children: [(prediction.predicted_probability * 100).toFixed(1), "%"] })] }), _jsxs("div", { className: "bg-white p-3 rounded", children: [_jsx("div", { className: "text-sm text-gray-600", children: "Market Price" }), _jsxs("div", { className: "text-2xl font-bold text-gray-700", children: [(prediction.market_probability * 100).toFixed(1), "%"] })] })] }), _jsxs("div", { className: "bg-white p-3 rounded mb-4", children: [_jsxs("div", { className: `text-sm font-semibold ${edgeColor}`, children: ["Edge: ", edge.edge.toFixed(3), " (", edge.edge_pct.toFixed(1), "%)"] }), _jsxs("div", { className: "text-sm text-gray-600 mt-1", children: ["Kelly: ", (edge.kelly_fraction * 100).toFixed(1), "%"] }), _jsxs("div", { className: "text-sm text-gray-600", children: ["Best Side: ", edge.best_side] })] }), _jsx("button", { className: "w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition", children: "View Details" })] }));
};
const EdgeOpportunitiesPanel = ({ opportunities }) => {
    const sorted = [...opportunities].sort((a, b) => b.edge_percentage - a.edge_percentage);
    return (_jsxs("div", { className: "bg-white p-6 rounded-lg shadow-md mb-8", children: [_jsx("h2", { className: "text-2xl font-semibold mb-4 text-gray-900", children: "Edge Opportunities" }), _jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "w-full", children: [_jsx("thead", { className: "bg-gray-50 border-b", children: _jsxs("tr", { children: [_jsx("th", { className: "px-4 py-2 text-left text-sm font-semibold text-gray-700", children: "Metric" }), _jsx("th", { className: "px-4 py-2 text-left text-sm font-semibold text-gray-700", children: "Direction" }), _jsx("th", { className: "px-4 py-2 text-right text-sm font-semibold text-gray-700", children: "Edge %" }), _jsx("th", { className: "px-4 py-2 text-right text-sm font-semibold text-gray-700", children: "Model" }), _jsx("th", { className: "px-4 py-2 text-right text-sm font-semibold text-gray-700", children: "Market" }), _jsx("th", { className: "px-4 py-2 text-right text-sm font-semibold text-gray-700", children: "Kelly" }), _jsx("th", { className: "px-4 py-2 text-left text-sm font-semibold text-gray-700", children: "Confidence" })] }) }), _jsx("tbody", { children: sorted.map((opp, idx) => (_jsxs("tr", { className: "border-b hover:bg-gray-50", children: [_jsx("td", { className: "px-4 py-3 text-sm text-gray-900", children: opp.metric }), _jsx("td", { className: "px-4 py-3 text-sm", children: _jsx("span", { className: `px-2 py-1 rounded text-white text-xs font-semibold ${opp.direction === 'YES' ? 'bg-green-500' : 'bg-red-500'}`, children: opp.direction }) }), _jsxs("td", { className: "px-4 py-3 text-sm text-right font-semibold", children: [opp.edge_percentage.toFixed(2), "%"] }), _jsxs("td", { className: "px-4 py-3 text-sm text-right text-gray-700", children: [(opp.model_prediction * 100).toFixed(1), "%"] }), _jsxs("td", { className: "px-4 py-3 text-sm text-right text-gray-700", children: [(opp.market_price * 100).toFixed(1), "%"] }), _jsxs("td", { className: "px-4 py-3 text-sm text-right text-gray-700", children: [(opp.kelly_fraction * 100).toFixed(2), "%"] }), _jsx("td", { className: "px-4 py-3 text-sm", children: _jsx("span", { className: `px-2 py-1 rounded text-xs font-semibold ${opp.confidence === 'high'
                                                ? 'bg-green-100 text-green-800'
                                                : opp.confidence === 'medium'
                                                    ? 'bg-yellow-100 text-yellow-800'
                                                    : 'bg-gray-100 text-gray-800'}`, children: opp.confidence }) })] }, idx))) })] }) })] }));
};
const FOCMSchedulePanel = ({ meetings }) => {
    return (_jsxs("div", { className: "bg-white p-6 rounded-lg shadow-md", children: [_jsx("h2", { className: "text-2xl font-semibold mb-4 text-gray-900", children: "FOMC Meeting Schedule" }), _jsx("div", { className: "space-y-2", children: meetings.slice(0, 5).map((meeting, idx) => (_jsxs("div", { className: "flex justify-between items-center p-3 border rounded hover:bg-gray-50", children: [_jsxs("div", { children: [_jsx("div", { className: "font-semibold text-gray-900", children: meeting.description }), _jsxs("div", { className: "text-sm text-gray-600", children: ["Meeting: ", new Date(meeting.date).toLocaleDateString(), " | Decision: ", new Date(meeting.decision_date).toLocaleDateString()] })] }), _jsx("button", { className: "px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition text-sm font-semibold", children: "View Market" })] }, idx))) })] }));
};
export default EconomicsDashboard;
