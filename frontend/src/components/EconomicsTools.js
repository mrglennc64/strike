import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React from 'react';
export const KellyCalculator = ({ predictedProbability, marketPrice, onCalculate, }) => {
    const calculateKelly = () => {
        if (marketPrice <= 0 || marketPrice >= 1) {
            return 0;
        }
        const b = (1 - marketPrice) / marketPrice;
        const f = (marketPrice * b - (1 - marketPrice)) / b;
        // Cap at 25% Kelly
        return Math.max(0, Math.min(f, 0.25));
    };
    const kelly = calculateKelly();
    const ev = predictedProbability * (1 / marketPrice - 1) - (1 - predictedProbability);
    React.useEffect(() => {
        if (onCalculate) {
            onCalculate(kelly);
        }
    }, [kelly, onCalculate]);
    return (_jsxs("div", { className: "bg-white p-4 rounded-lg shadow border-l-4 border-purple-500", children: [_jsx("h3", { className: "text-lg font-semibold mb-3 text-gray-900", children: "Kelly Criterion" }), _jsxs("div", { className: "space-y-2", children: [_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-700", children: "Model Probability" }), _jsxs("span", { className: "font-semibold", children: [(predictedProbability * 100).toFixed(1), "%"] })] }), _jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-700", children: "Market Probability" }), _jsxs("span", { className: "font-semibold", children: [(marketPrice * 100).toFixed(1), "%"] })] }), _jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-700", children: "Edge" }), _jsxs("span", { className: "font-semibold text-green-600", children: [((predictedProbability - marketPrice) * 100).toFixed(2), "%"] })] })] }), _jsxs("div", { className: "mt-4 p-3 bg-gray-50 rounded", children: [_jsx("div", { className: "text-sm text-gray-600", children: "Kelly Fraction (25% cap)" }), _jsxs("div", { className: "text-3xl font-bold text-purple-600", children: [(kelly * 100).toFixed(2), "%"] }), _jsxs("div", { className: "text-xs text-gray-500 mt-1", children: ["Expected Value: ", ev > 0 ? '+' : '', ev.toFixed(4)] })] })] }));
};
export const EdgeVisualizer = ({ modelProbability, marketProbability, }) => {
    const width = 200;
    const modelX = modelProbability * width;
    const marketX = marketProbability * width;
    const edge = modelProbability - marketProbability;
    return (_jsxs("div", { className: "bg-white p-4 rounded-lg shadow", children: [_jsx("h3", { className: "text-lg font-semibold mb-3 text-gray-900", children: "Edge Visualization" }), _jsxs("div", { className: "space-y-4", children: [_jsxs("div", { children: [_jsx("div", { className: "text-sm font-semibold text-gray-700 mb-2", children: "0% - 100%" }), _jsx("div", { className: "relative h-12 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded opacity-30" }), _jsxs("div", { className: "relative h-6 mb-1", children: [_jsx("div", { className: "absolute h-6 w-1 bg-blue-600 rounded", style: { left: `${modelX}px` } }), _jsxs("div", { className: "text-xs text-blue-600 font-semibold", children: ["Model: ", (modelProbability * 100).toFixed(1), "%"] })] }), _jsxs("div", { className: "relative h-6", children: [_jsx("div", { className: "absolute h-6 w-1 bg-red-600 rounded", style: { left: `${marketX}px` } }), _jsxs("div", { className: "text-xs text-red-600 font-semibold", children: ["Market: ", (marketProbability * 100).toFixed(1), "%"] })] })] }), _jsxs("div", { className: `p-3 rounded ${edge > 0 ? 'bg-green-50' : 'bg-red-50'}`, children: [_jsx("div", { className: `text-sm font-semibold ${edge > 0 ? 'text-green-700' : 'text-red-700'}`, children: edge > 0 ? '✓ Positive Edge' : '✗ Negative Edge' }), _jsxs("div", { className: `text-2xl font-bold ${edge > 0 ? 'text-green-600' : 'text-red-600'}`, children: [edge > 0 ? '+' : '', (edge * 100).toFixed(2), "%"] })] })] })] }));
};
export const ProbabilityGauge = ({ value, label, threshold, }) => {
    const percentage = value * 100;
    const color = value < 0.33 ? '#ef4444' : value < 0.67 ? '#eab308' : '#22c55e';
    return (_jsxs("div", { className: "bg-white p-4 rounded-lg shadow text-center", children: [_jsx("div", { className: "text-sm text-gray-600 font-semibold mb-3", children: label }), _jsxs("svg", { className: "w-32 h-32 mx-auto", viewBox: "0 0 100 100", children: [_jsx("circle", { cx: "50", cy: "50", r: "40", fill: "none", stroke: "#e5e7eb", strokeWidth: "3" }), _jsx("circle", { cx: "50", cy: "50", r: "40", fill: "none", stroke: color, strokeWidth: "3", strokeDasharray: `${percentage * 2.51} 251`, strokeLinecap: "round" }), _jsxs("text", { x: "50", y: "55", textAnchor: "middle", fontSize: "24", fontWeight: "bold", fill: "currentColor", children: [percentage.toFixed(0), "%"] })] }), threshold && (_jsxs("div", { className: "mt-2 text-xs text-gray-600", children: ["Threshold: ", (threshold * 100).toFixed(1), "%"] }))] }));
};
export const ModelPerformance = ({ metrics }) => {
    return (_jsxs("div", { className: "bg-white p-4 rounded-lg shadow", children: [_jsx("h3", { className: "text-lg font-semibold mb-3 text-gray-900", children: "Model Performance" }), _jsxs("div", { className: "space-y-2", children: [metrics.auc_score !== undefined && (_jsxs("div", { className: "flex justify-between items-center pb-2 border-b", children: [_jsx("span", { className: "text-gray-700", children: "AUC Score" }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("div", { className: "w-32 h-2 bg-gray-200 rounded-full overflow-hidden", children: _jsx("div", { className: "h-full bg-blue-500", style: { width: `${Math.min(metrics.auc_score * 100, 100)}%` } }) }), _jsx("span", { className: "font-semibold text-blue-600", children: metrics.auc_score.toFixed(3) })] })] })), metrics.brier_score !== undefined && (_jsxs("div", { className: "flex justify-between items-center pb-2 border-b", children: [_jsx("span", { className: "text-gray-700", children: "Brier Score (lower is better)" }), _jsx("span", { className: "font-semibold text-gray-900", children: metrics.brier_score.toFixed(4) })] })), metrics.accuracy !== undefined && (_jsxs("div", { className: "flex justify-between items-center pb-2 border-b", children: [_jsx("span", { className: "text-gray-700", children: "Accuracy" }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("div", { className: "w-32 h-2 bg-gray-200 rounded-full overflow-hidden", children: _jsx("div", { className: "h-full bg-green-500", style: { width: `${metrics.accuracy * 100}%` } }) }), _jsxs("span", { className: "font-semibold text-green-600", children: [(metrics.accuracy * 100).toFixed(1), "%"] })] })] })), metrics.training_duration_seconds && (_jsxs("div", { className: "flex justify-between items-center text-sm text-gray-600 mt-4 pt-2 border-t", children: [_jsx("span", { children: "Training Duration" }), _jsxs("span", { className: "font-semibold", children: [metrics.training_duration_seconds.toFixed(1), "s"] })] }))] })] }));
};
export default {
    KellyCalculator,
    EdgeVisualizer,
    ProbabilityGauge,
    ModelPerformance,
};
