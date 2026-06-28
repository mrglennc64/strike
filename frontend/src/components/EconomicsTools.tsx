import React from 'react';

interface KellyCalculatorProps {
  predictedProbability: number;
  marketPrice: number;
  onCalculate?: (fraction: number) => void;
}

export const KellyCalculator: React.FC<KellyCalculatorProps> = ({
  predictedProbability,
  marketPrice,
  onCalculate,
}) => {
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

  return (
    <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
      <h3 className="text-lg font-semibold mb-3 text-gray-900">Kelly Criterion</h3>

      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-700">Model Probability</span>
          <span className="font-semibold">{(predictedProbability * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Market Probability</span>
          <span className="font-semibold">{(marketPrice * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-700">Edge</span>
          <span className="font-semibold text-green-600">
            {((predictedProbability - marketPrice) * 100).toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded">
        <div className="text-sm text-gray-600">Kelly Fraction (25% cap)</div>
        <div className="text-3xl font-bold text-purple-600">
          {(kelly * 100).toFixed(2)}%
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Expected Value: {ev > 0 ? '+' : ''}{ev.toFixed(4)}
        </div>
      </div>
    </div>
  );
};

interface EdgeVisualizerProps {
  modelProbability: number;
  marketProbability: number;
}

export const EdgeVisualizer: React.FC<EdgeVisualizerProps> = ({
  modelProbability,
  marketProbability,
}) => {
  const width = 200;
  const modelX = modelProbability * width;
  const marketX = marketProbability * width;
  const edge = modelProbability - marketProbability;

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-3 text-gray-900">Edge Visualization</h3>

      <div className="space-y-4">
        {/* Probability scale */}
        <div>
          <div className="text-sm font-semibold text-gray-700 mb-2">0% - 100%</div>
          <div className="relative h-12 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded opacity-30" />

          {/* Model prediction marker */}
          <div className="relative h-6 mb-1">
            <div
              className="absolute h-6 w-1 bg-blue-600 rounded"
              style={{ left: `${modelX}px` }}
            />
            <div className="text-xs text-blue-600 font-semibold">Model: {(modelProbability * 100).toFixed(1)}%</div>
          </div>

          {/* Market price marker */}
          <div className="relative h-6">
            <div
              className="absolute h-6 w-1 bg-red-600 rounded"
              style={{ left: `${marketX}px` }}
            />
            <div className="text-xs text-red-600 font-semibold">Market: {(marketProbability * 100).toFixed(1)}%</div>
          </div>
        </div>

        {/* Edge indicator */}
        <div className={`p-3 rounded ${edge > 0 ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className={`text-sm font-semibold ${edge > 0 ? 'text-green-700' : 'text-red-700'}`}>
            {edge > 0 ? '✓ Positive Edge' : '✗ Negative Edge'}
          </div>
          <div className={`text-2xl font-bold ${edge > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {edge > 0 ? '+' : ''}{(edge * 100).toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  );
};

interface ProbabilityGaugeProps {
  value: number;
  label: string;
  threshold?: number;
}

export const ProbabilityGauge: React.FC<ProbabilityGaugeProps> = ({
  value,
  label,
  threshold,
}) => {
  const percentage = value * 100;
  const color =
    value < 0.33 ? '#ef4444' : value < 0.67 ? '#eab308' : '#22c55e';

  return (
    <div className="bg-white p-4 rounded-lg shadow text-center">
      <div className="text-sm text-gray-600 font-semibold mb-3">{label}</div>

      <svg className="w-32 h-32 mx-auto" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="3"
        />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeDasharray={`${percentage * 2.51} 251`}
          strokeLinecap="round"
        />
        <text
          x="50"
          y="55"
          textAnchor="middle"
          fontSize="24"
          fontWeight="bold"
          fill="currentColor"
        >
          {percentage.toFixed(0)}%
        </text>
      </svg>

      {threshold && (
        <div className="mt-2 text-xs text-gray-600">
          Threshold: {(threshold * 100).toFixed(1)}%
        </div>
      )}
    </div>
  );
};

interface ModelPerformanceProps {
  metrics: {
    auc_score?: number;
    brier_score?: number;
    accuracy?: number;
    precision?: number;
    recall?: number;
    training_duration_seconds?: number;
  };
}

export const ModelPerformance: React.FC<ModelPerformanceProps> = ({ metrics }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-3 text-gray-900">Model Performance</h3>

      <div className="space-y-2">
        {metrics.auc_score !== undefined && (
          <div className="flex justify-between items-center pb-2 border-b">
            <span className="text-gray-700">AUC Score</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500"
                  style={{ width: `${Math.min(metrics.auc_score * 100, 100)}%` }}
                />
              </div>
              <span className="font-semibold text-blue-600">
                {metrics.auc_score.toFixed(3)}
              </span>
            </div>
          </div>
        )}

        {metrics.brier_score !== undefined && (
          <div className="flex justify-between items-center pb-2 border-b">
            <span className="text-gray-700">Brier Score (lower is better)</span>
            <span className="font-semibold text-gray-900">
              {metrics.brier_score.toFixed(4)}
            </span>
          </div>
        )}

        {metrics.accuracy !== undefined && (
          <div className="flex justify-between items-center pb-2 border-b">
            <span className="text-gray-700">Accuracy</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${metrics.accuracy * 100}%` }}
                />
              </div>
              <span className="font-semibold text-green-600">
                {(metrics.accuracy * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {metrics.training_duration_seconds && (
          <div className="flex justify-between items-center text-sm text-gray-600 mt-4 pt-2 border-t">
            <span>Training Duration</span>
            <span className="font-semibold">
              {metrics.training_duration_seconds.toFixed(1)}s
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default {
  KellyCalculator,
  EdgeVisualizer,
  ProbabilityGauge,
  ModelPerformance,
};
