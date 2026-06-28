import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import './MLBStrikeoutPredictor.css';
export const MLBStrikeoutPredictor = () => {
    const [predictions, setPredictions] = useState([]);
    const [modelStatus, setModelStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [training, setTraining] = useState(false);
    const [error, setError] = useState(null);
    const [strikeoutLine, setStrikeoutLine] = useState(5.5);
    const [edgeThreshold, setEdgeThreshold] = useState(8.0);
    const [filterDirection, setFilterDirection] = useState('ALL');
    // Fetch model status on mount
    useEffect(() => {
        fetchModelStatus();
        fetchPredictions();
    }, []);
    const fetchModelStatus = async () => {
        try {
            const response = await fetch(`/api/verticals/mlb/status`);
            if (response.ok) {
                const data = await response.json();
                setModelStatus(data);
            }
        }
        catch (err) {
            console.error('Error fetching model status:', err);
        }
    };
    const trainModel = async () => {
        setTraining(true);
        setError(null);
        try {
            const response = await fetch(`/api/verticals/mlb/train`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: '2026-06-01',
                    end_date: '2026-06-10',
                    force_retrain: true
                })
            });
            if (!response.ok) {
                throw new Error(`Training failed: ${response.statusText}`);
            }
            await fetchModelStatus();
            await fetchPredictions();
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Training error');
        }
        finally {
            setTraining(false);
        }
    };
    const fetchPredictions = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/verticals/mlb/predictions/today?strikeout_line=${strikeoutLine}&min_edge=${edgeThreshold}`);
            if (!response.ok) {
                if (response.status === 400) {
                    setError('Model not trained. Click "Train Model" to start.');
                    setPredictions([]);
                    setLoading(false);
                    return;
                }
                throw new Error(`Failed to fetch predictions: ${response.statusText}`);
            }
            const data = await response.json();
            setPredictions(data.predictions || []);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Prediction error');
            setPredictions([]);
        }
        finally {
            setLoading(false);
        }
    };
    const filteredPredictions = predictions.filter(pred => {
        if (filterDirection === 'ALL')
            return true;
        return pred.direction === filterDirection;
    });
    const stats = {
        totalPlays: filteredPredictions.length,
        avgEdge: filteredPredictions.length > 0
            ? (filteredPredictions.reduce((sum, p) => sum + p.edge_pct, 0) / filteredPredictions.length).toFixed(2)
            : '0.00',
        bestEdge: filteredPredictions.length > 0
            ? Math.max(...filteredPredictions.map(p => Math.abs(p.edge_pct))).toFixed(2)
            : '0.00',
        overCount: filteredPredictions.filter(p => p.direction === 'OVER').length,
        underCount: filteredPredictions.filter(p => p.direction === 'UNDER').length
    };
    const getEdgeColor = (edge) => {
        if (Math.abs(edge) > 15)
            return '#2ecc71'; // Strong green
        if (Math.abs(edge) > 10)
            return '#3498db'; // Medium blue
        if (Math.abs(edge) > 5)
            return '#f39c12'; // Orange
        return '#95a5a6'; // Gray
    };
    const getDirectionBadge = (direction) => {
        return direction === 'OVER' ? 'badge-over' : 'badge-under';
    };
    return (_jsxs("div", { className: "mlb-strikeout-predictor", children: [_jsxs("div", { className: "predictor-header", children: [_jsx("h1", { children: "MLB Strikeout Predictor" }), _jsx("p", { children: "Poisson Regression Model | DraftKings Comparison" })] }), modelStatus && (_jsxs("div", { className: "status-card", children: [_jsxs("div", { className: "status-left", children: [_jsx("h3", { children: "Model Status" }), modelStatus.trained ? (_jsxs("div", { className: "status-trained", children: [_jsx("span", { className: "status-badge trained", children: "\u2713 TRAINED" }), _jsxs("p", { children: ["Last trained: ", new Date(modelStatus.last_trained || '').toLocaleDateString()] }), _jsxs("p", { children: ["Data: ", modelStatus.training_data_records?.toLocaleString(), " records"] }), _jsxs("p", { children: ["Pitchers: ", modelStatus.unique_pitchers] })] })) : (_jsxs("div", { className: "status-not-trained", children: [_jsx("span", { className: "status-badge not-trained", children: "\u26A0 NOT TRAINED" }), _jsx("p", { children: "Click \"Train Model\" to initialize predictions" })] }))] }), _jsx("button", { className: "btn btn-train", onClick: trainModel, disabled: training, children: training ? 'Training...' : 'Train Model' })] })), _jsxs("div", { className: "controls-section", children: [_jsxs("div", { className: "control-group", children: [_jsx("label", { children: "Strikeout Line:" }), _jsx("input", { type: "number", min: "0", step: "0.5", value: strikeoutLine, onChange: (e) => setStrikeoutLine(parseFloat(e.target.value)), disabled: loading })] }), _jsxs("div", { className: "control-group", children: [_jsx("label", { children: "Min Edge %:" }), _jsx("input", { type: "number", min: "0", step: "0.5", value: edgeThreshold, onChange: (e) => setEdgeThreshold(parseFloat(e.target.value)), disabled: loading })] }), _jsxs("div", { className: "control-group", children: [_jsx("label", { children: "Direction:" }), _jsxs("select", { value: filterDirection, onChange: (e) => setFilterDirection(e.target.value), disabled: loading, children: [_jsx("option", { value: "ALL", children: "All" }), _jsx("option", { value: "OVER", children: "Over Only" }), _jsx("option", { value: "UNDER", children: "Under Only" })] })] }), _jsx("button", { className: "btn btn-refresh", onClick: fetchPredictions, disabled: loading || !modelStatus?.trained, children: loading ? 'Loading...' : 'Refresh' })] }), error && (_jsx("div", { className: "error-card", children: _jsx("p", { children: error }) })), !loading && filteredPredictions.length > 0 && (_jsxs("div", { className: "stats-summary", children: [_jsxs("div", { className: "stat-box", children: [_jsx("span", { className: "stat-label", children: "Total Plays" }), _jsx("span", { className: "stat-value", children: stats.totalPlays })] }), _jsxs("div", { className: "stat-box", children: [_jsx("span", { className: "stat-label", children: "Avg Edge" }), _jsxs("span", { className: "stat-value", children: [stats.avgEdge, "%"] })] }), _jsxs("div", { className: "stat-box", children: [_jsx("span", { className: "stat-label", children: "Best Edge" }), _jsxs("span", { className: "stat-value", children: [stats.bestEdge, "%"] })] }), _jsxs("div", { className: "stat-box", children: [_jsx("span", { className: "stat-label", children: "OVER / UNDER" }), _jsxs("span", { className: "stat-value", children: [stats.overCount, " / ", stats.underCount] })] })] })), _jsxs("div", { className: "predictions-section", children: [_jsxs("h2", { children: ["Predictions (", filteredPredictions.length, ")"] }), loading && (_jsxs("div", { className: "loading-spinner", children: [_jsx("div", { className: "spinner" }), _jsx("p", { children: "Loading predictions..." })] })), !loading && filteredPredictions.length === 0 ? (_jsx("div", { className: "empty-state", children: _jsx("p", { children: modelStatus?.trained
                                ? 'No predictions with edge > ' + edgeThreshold + '%'
                                : 'Train model to see predictions' }) })) : (_jsx("div", { className: "predictions-table", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Pitcher" }), _jsx("th", { children: "Opponent" }), _jsx("th", { children: "Game Date" }), _jsx("th", { children: "Line" }), _jsx("th", { children: "Expected K" }), _jsx("th", { children: "Model %" }), _jsx("th", { children: "Book %" }), _jsx("th", { children: "Edge %" }), _jsx("th", { children: "Confidence" })] }) }), _jsx("tbody", { children: filteredPredictions.map((pred, idx) => (_jsxs("tr", { className: "prediction-row", children: [_jsx("td", { children: _jsxs("div", { className: "pitcher-info", children: [_jsx("span", { className: "pitcher-name", children: pred.pitcher_name }), _jsxs("span", { className: "pitcher-id", children: ["ID: ", pred.pitcher_id] })] }) }), _jsx("td", { children: pred.opponent }), _jsx("td", { children: pred.game_date }), _jsx("td", { children: _jsxs("span", { className: getDirectionBadge(pred.direction), children: [pred.direction, " ", pred.strikeout_line] }) }), _jsx("td", { className: "lambda-value", children: pred.lambda.toFixed(2) }), _jsx("td", { className: "model-prob", children: _jsxs("span", { className: "prob-value", children: [(pred.model_prob_pct).toFixed(1), "%"] }) }), _jsx("td", { className: "book-prob", children: _jsxs("span", { className: "prob-value", children: [(pred.book_prob_pct).toFixed(1), "%"] }) }), _jsx("td", { children: _jsxs("span", { className: "edge-badge", style: { backgroundColor: getEdgeColor(pred.edge_pct) }, children: [pred.edge_pct > 0 ? '+' : '', pred.edge_pct.toFixed(1), "%"] }) }), _jsxs("td", { className: "confidence-value", children: [pred.confidence.toFixed(0), "%"] })] }, idx))) })] }) }))] }), filteredPredictions.length > 0 && (_jsxs("div", { className: "example-card", children: [_jsx("h3", { children: "Example Format" }), _jsxs("div", { className: "example-content", children: [_jsx("p", { children: _jsx("strong", { children: filteredPredictions[0].pitcher_name }) }), _jsxs("p", { children: ["Over ", filteredPredictions[0].strikeout_line, " Ks"] }), _jsxs("p", { children: ["Model ", _jsxs("strong", { children: [filteredPredictions[0].model_prob_pct.toFixed(1), "%"] }), " | Book ", _jsxs("strong", { children: [filteredPredictions[0].book_prob_pct.toFixed(1), "%"] }), " | Edge ", _jsxs("strong", { style: { color: getEdgeColor(filteredPredictions[0].edge_pct) }, children: [filteredPredictions[0].edge_pct > 0 ? '+' : '', filteredPredictions[0].edge_pct.toFixed(1), "%"] })] })] })] }))] }));
};
export default MLBStrikeoutPredictor;
