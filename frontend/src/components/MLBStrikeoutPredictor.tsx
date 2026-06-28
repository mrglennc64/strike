import { useState, useEffect } from 'react';
import './MLBStrikeoutPredictor.css';

interface Prediction {
  pitcher_id: number;
  pitcher_name: string;
  opponent: string;
  game_date: string;
  strikeout_line: number;
  model_prob: number;
  model_prob_pct: number;
  book_prob: number;
  book_prob_pct: number;
  edge_pct: number;
  lambda: number;
  batters_faced: number;
  direction: 'OVER' | 'UNDER';
  confidence: number;
}

interface ModelStatus {
  trained: boolean;
  last_trained: string | null;
  training_data_records: number;
  unique_pitchers: number;
  unique_games: number;
  date_range_start: string | null;
  date_range_end: string | null;
}

export const MLBStrikeoutPredictor: React.FC = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strikeoutLine, setStrikeoutLine] = useState(5.5);
  const [edgeThreshold, setEdgeThreshold] = useState(8.0);
  const [filterDirection, setFilterDirection] = useState<'ALL' | 'OVER' | 'UNDER'>('ALL');

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
    } catch (err) {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Training error');
    } finally {
      setTraining(false);
    }
  };

  const fetchPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/verticals/mlb/predictions/today?strikeout_line=${strikeoutLine}&min_edge=${edgeThreshold}`
      );

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction error');
      setPredictions([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredPredictions = predictions.filter(pred => {
    if (filterDirection === 'ALL') return true;
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

  const getEdgeColor = (edge: number): string => {
    if (Math.abs(edge) > 15) return '#2ecc71'; // Strong green
    if (Math.abs(edge) > 10) return '#3498db'; // Medium blue
    if (Math.abs(edge) > 5) return '#f39c12'; // Orange
    return '#95a5a6'; // Gray
  };

  const getDirectionBadge = (direction: string): string => {
    return direction === 'OVER' ? 'badge-over' : 'badge-under';
  };

  return (
    <div className="mlb-strikeout-predictor">
      {/* Header */}
      <div className="predictor-header">
        <h1>MLB Strikeout Predictor</h1>
        <p>Poisson Regression Model | DraftKings Comparison</p>
      </div>

      {/* Model Status Card */}
      {modelStatus && (
        <div className="status-card">
          <div className="status-left">
            <h3>Model Status</h3>
            {modelStatus.trained ? (
              <div className="status-trained">
                <span className="status-badge trained">✓ TRAINED</span>
                <p>Last trained: {new Date(modelStatus.last_trained || '').toLocaleDateString()}</p>
                <p>Data: {modelStatus.training_data_records?.toLocaleString()} records</p>
                <p>Pitchers: {modelStatus.unique_pitchers}</p>
              </div>
            ) : (
              <div className="status-not-trained">
                <span className="status-badge not-trained">⚠ NOT TRAINED</span>
                <p>Click "Train Model" to initialize predictions</p>
              </div>
            )}
          </div>
          <button
            className="btn btn-train"
            onClick={trainModel}
            disabled={training}
          >
            {training ? 'Training...' : 'Train Model'}
          </button>
        </div>
      )}

      {/* Controls */}
      <div className="controls-section">
        <div className="control-group">
          <label>Strikeout Line:</label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={strikeoutLine}
            onChange={(e) => setStrikeoutLine(parseFloat(e.target.value))}
            disabled={loading}
          />
        </div>

        <div className="control-group">
          <label>Min Edge %:</label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={edgeThreshold}
            onChange={(e) => setEdgeThreshold(parseFloat(e.target.value))}
            disabled={loading}
          />
        </div>

        <div className="control-group">
          <label>Direction:</label>
          <select
            value={filterDirection}
            onChange={(e) => setFilterDirection(e.target.value as 'ALL' | 'OVER' | 'UNDER')}
            disabled={loading}
          >
            <option value="ALL">All</option>
            <option value="OVER">Over Only</option>
            <option value="UNDER">Under Only</option>
          </select>
        </div>

        <button
          className="btn btn-refresh"
          onClick={fetchPredictions}
          disabled={loading || !modelStatus?.trained}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-card">
          <p>{error}</p>
        </div>
      )}

      {/* Stats Summary */}
      {!loading && filteredPredictions.length > 0 && (
        <div className="stats-summary">
          <div className="stat-box">
            <span className="stat-label">Total Plays</span>
            <span className="stat-value">{stats.totalPlays}</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Avg Edge</span>
            <span className="stat-value">{stats.avgEdge}%</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Best Edge</span>
            <span className="stat-value">{stats.bestEdge}%</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">OVER / UNDER</span>
            <span className="stat-value">{stats.overCount} / {stats.underCount}</span>
          </div>
        </div>
      )}

      {/* Predictions Table */}
      <div className="predictions-section">
        <h2>
          Predictions ({filteredPredictions.length})
        </h2>

        {loading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading predictions...</p>
          </div>
        )}

        {!loading && filteredPredictions.length === 0 ? (
          <div className="empty-state">
            <p>
              {modelStatus?.trained
                ? 'No predictions with edge > ' + edgeThreshold + '%'
                : 'Train model to see predictions'}
            </p>
          </div>
        ) : (
          <div className="predictions-table">
            <table>
              <thead>
                <tr>
                  <th>Pitcher</th>
                  <th>Opponent</th>
                  <th>Game Date</th>
                  <th>Line</th>
                  <th>Expected K</th>
                  <th>Model %</th>
                  <th>Book %</th>
                  <th>Edge %</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredPredictions.map((pred, idx) => (
                  <tr key={idx} className="prediction-row">
                    <td>
                      <div className="pitcher-info">
                        <span className="pitcher-name">{pred.pitcher_name}</span>
                        <span className="pitcher-id">ID: {pred.pitcher_id}</span>
                      </div>
                    </td>
                    <td>{pred.opponent}</td>
                    <td>{pred.game_date}</td>
                    <td>
                      <span className={getDirectionBadge(pred.direction)}>
                        {pred.direction} {pred.strikeout_line}
                      </span>
                    </td>
                    <td className="lambda-value">{pred.lambda.toFixed(2)}</td>
                    <td className="model-prob">
                      <span className="prob-value">{(pred.model_prob_pct).toFixed(1)}%</span>
                    </td>
                    <td className="book-prob">
                      <span className="prob-value">{(pred.book_prob_pct).toFixed(1)}%</span>
                    </td>
                    <td>
                      <span
                        className="edge-badge"
                        style={{ backgroundColor: getEdgeColor(pred.edge_pct) }}
                      >
                        {pred.edge_pct > 0 ? '+' : ''}{pred.edge_pct.toFixed(1)}%
                      </span>
                    </td>
                    <td className="confidence-value">
                      {pred.confidence.toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Example Output Format */}
      {filteredPredictions.length > 0 && (
        <div className="example-card">
          <h3>Example Format</h3>
          <div className="example-content">
            <p>
              <strong>{filteredPredictions[0].pitcher_name}</strong>
            </p>
            <p>
              Over {filteredPredictions[0].strikeout_line} Ks
            </p>
            <p>
              Model <strong>{filteredPredictions[0].model_prob_pct.toFixed(1)}%</strong> |
              Book <strong>{filteredPredictions[0].book_prob_pct.toFixed(1)}%</strong> |
              Edge <strong style={{ color: getEdgeColor(filteredPredictions[0].edge_pct) }}>
                {filteredPredictions[0].edge_pct > 0 ? '+' : ''}{filteredPredictions[0].edge_pct.toFixed(1)}%
              </strong>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MLBStrikeoutPredictor;
