import { useState, useEffect } from 'react';
import { api } from '../api/client';

interface ReleasePrediction {
  provider: string;
  model_name: string;
  prediction_date: string;
  target_date: string;
  predicted_probability: number;
  polymarket_price: number;
  edge: number;
  edge_pct: number;
  recommendation: string;
  confidence: number;
  features: Record<string, any>;
}

export const AIReleasesPage: React.FC = () => {
  const [provider, setProvider] = useState('anthropic');
  const [modelName, setModelName] = useState('Claude 4');
  const [targetDate, setTargetDate] = useState(
    new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [selectedPrediction, setSelectedPrediction] = useState<ReleasePrediction | null>(null);
  const [examples, setExamples] = useState<ReleasePrediction[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadExamples();
  }, []);

  const loadExamples = async () => {
    try {
      const response = await api.get('/verticals/ai-releases/examples').catch(() => ({ data: { predictions: [] } }));
      setExamples(response.data.predictions || []);
    } catch (err) {
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
    } catch (err) {
      console.error('Failed to generate prediction', err);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (recommendation: string) => {
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

  const getProviderColor = (prov: string) => {
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

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">AI Release Predictor</h1>
          <p className="text-gray-400">
            Predict when Claude, GPT, and Grok will be released. Trade on Polymarket with edge.
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Generate Prediction</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                AI Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openai">OpenAI (GPT)</option>
                <option value="xai">xAI (Grok)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Model Name
              </label>
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g., Claude 4"
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Target Date
              </label>
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={handlePredict}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                {loading ? 'Predicting...' : 'Predict'}
              </button>
            </div>
          </div>

          {selectedPrediction && (
            <div className="mt-6 bg-gray-700 rounded p-4 border border-gray-600">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <p className="text-gray-400 text-sm">Model Probability</p>
                  <p className="text-white font-bold text-lg">
                    {(selectedPrediction.predicted_probability * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Market Price</p>
                  <p className="text-white font-bold text-lg">
                    {(selectedPrediction.polymarket_price * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Edge</p>
                  <p
                    className={`font-bold text-lg ${
                      selectedPrediction.edge >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {(selectedPrediction.edge * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Recommendation</p>
                  <span
                    className={`inline-block px-3 py-1 rounded text-sm font-medium ${getRecommendationColor(
                      selectedPrediction.recommendation
                    )}`}
                  >
                    {selectedPrediction.recommendation}
                  </span>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Confidence</p>
                  <p className="text-white font-bold text-lg">
                    {(selectedPrediction.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">Example Predictions</h2>

            {examples.length > 0 ? (
              <div className="space-y-4">
                {examples.map((pred: ReleasePrediction, idx: number) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedPrediction(pred)}
                    className="bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-600 transition-colors border border-gray-600"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-white font-medium">{pred.model_name}</p>
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs font-medium mt-1 ${getProviderColor(
                            pred.provider
                          )}`}
                        >
                          {pred.provider}
                        </span>
                      </div>
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-medium ${getRecommendationColor(
                          pred.recommendation
                        )}`}
                      >
                        {pred.recommendation}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <p className="text-gray-400">Prob</p>
                        <p className="text-white font-bold">
                          {(pred.predicted_probability * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-400">Price</p>
                        <p className="text-white font-bold">
                          {(pred.polymarket_price * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-400">Edge</p>
                        <p
                          className={`font-bold ${
                            pred.edge >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {(pred.edge * 100).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">No examples available</p>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">About AI Releases</h2>

            <div className="space-y-4 text-gray-300">
              <p>
                Trade predictions on when new AI models will be released. Anthropic (Claude),
                OpenAI (GPT), and xAI (Grok) are the primary markets.
              </p>

              <div>
                <h3 className="text-white font-semibold mb-2">How it works:</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>Select AI provider and target release date</li>
                  <li>Model generates probability prediction</li>
                  <li>Compare with Polymarket prices for edge</li>
                  <li>Trade on Polymarket or other prediction markets</li>
                </ul>
              </div>

              <div>
                <h3 className="text-white font-semibold mb-2">Model inputs:</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>Historical release cadences</li>
                  <li>Company announcements and timelines</li>
                  <li>Industry trends and competitive pressure</li>
                  <li>Market sentiment from social media</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
