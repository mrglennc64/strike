import { useState, useEffect } from 'react';

interface Prediction {
  metric: string;
  predicted_probability: number;
  market_probability: number;
  edge: EdgeData;
  latest_value?: number;
  threshold?: number;
  next_meeting?: any;
  current_rate?: number;
}

interface EdgeData {
  edge: number;
  edge_pct: number;
  ev_yes: number;
  ev_no: number;
  best_side: string;
  kelly_fraction: number;
}

interface EdgeOpportunity {
  metric: string;
  direction: string;
  edge_percentage: number;
  model_prediction: number;
  market_price: number;
  kelly_fraction: number;
  confidence: string;
}

interface FOCMMeeting {
  description: string;
  date: string;
  decision_date: string;
}

export const EconomicsDashboard: React.FC = () => {
  const [cpiPrediction, setCPIPrediction] = useState<Prediction | null>(null);
  const [rateCutPrediction, setRateCutPrediction] = useState<Prediction | null>(null);
  const [edgeOpportunities, setEdgeOpportunities] = useState<EdgeOpportunity[]>([]);
  const [fomc, setFOmc] = useState<FOCMMeeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading economics data...</div>;
  }

  return (
    <div className="p-8 bg-gray-50">
      <h1 className="text-4xl font-bold mb-8 text-gray-900">Fed/Economics Predictor</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* CPI Prediction */}
        <CPIPredictionCard prediction={cpiPrediction} />

        {/* Rate Cut Prediction */}
        <RateCutPredictionCard prediction={rateCutPrediction} />
      </div>

      {/* Edge Opportunities */}
      {edgeOpportunities.length > 0 && (
        <EdgeOpportunitiesPanel opportunities={edgeOpportunities} />
      )}

      {/* FOMC Schedule */}
      {fomc.length > 0 && (
        <FOCMSchedulePanel meetings={fomc} />
      )}
    </div>
  );
};

const CPIPredictionCard: React.FC<{ prediction: Prediction | null }> = ({ prediction }) => {
  if (!prediction) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">CPI Prediction</h2>
        <p className="text-gray-500">Unable to load CPI prediction</p>
      </div>
    );
  }

  const { edge } = prediction;
  const edgeColor = edge.edge > 0 ? 'text-green-600' : 'text-red-600';
  const bgColor = edge.edge > 0 ? 'bg-green-50' : 'bg-red-50';

  return (
    <div className={`${bgColor} p-6 rounded-lg shadow-md border-l-4 border-blue-500`}>
      <h2 className="text-xl font-semibold mb-4 text-gray-900">CPI Prediction</h2>

      <div className="mb-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Threshold</span>
          <span className="font-semibold text-lg">{prediction.threshold}%</span>
        </div>
        <div className="flex justify-between items-center mt-2">
          <span className="text-gray-600">Latest Value</span>
          <span className="font-semibold text-lg">{prediction.latest_value?.toFixed(2)}%</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white p-3 rounded">
          <div className="text-sm text-gray-600">Model Prediction</div>
          <div className="text-2xl font-bold text-blue-600">
            {(prediction.predicted_probability * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white p-3 rounded">
          <div className="text-sm text-gray-600">Market Price</div>
          <div className="text-2xl font-bold text-gray-700">
            {(prediction.market_probability * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="bg-white p-3 rounded mb-4">
        <div className={`text-sm font-semibold ${edgeColor}`}>
          Edge: {edge.edge.toFixed(3)} ({edge.edge_pct.toFixed(1)}%)
        </div>
        <div className="text-sm text-gray-600 mt-1">
          Kelly: {(edge.kelly_fraction * 100).toFixed(1)}%
        </div>
        <div className="text-sm text-gray-600">
          Best Side: {edge.best_side}
        </div>
      </div>

      <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">
        View Details
      </button>
    </div>
  );
};

const RateCutPredictionCard: React.FC<{ prediction: Prediction | null }> = ({ prediction }) => {
  if (!prediction) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-500">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">Rate Cut Prediction</h2>
        <p className="text-gray-500">Unable to load rate cut prediction</p>
      </div>
    );
  }

  const { edge } = prediction;
  const edgeColor = edge.edge > 0 ? 'text-green-600' : 'text-red-600';
  const bgColor = edge.edge > 0 ? 'bg-green-50' : 'bg-red-50';

  return (
    <div className={`${bgColor} p-6 rounded-lg shadow-md border-l-4 border-green-500`}>
      <h2 className="text-xl font-semibold mb-4 text-gray-900">Rate Cut Prediction</h2>

      <div className="mb-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Current Fed Rate</span>
          <span className="font-semibold text-lg">{prediction.current_rate?.toFixed(2)}%</span>
        </div>
        {prediction.next_meeting && (
          <div className="flex justify-between items-center mt-2">
            <span className="text-gray-600">Next Meeting</span>
            <span className="font-semibold text-lg">
              {new Date(prediction.next_meeting.date).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white p-3 rounded">
          <div className="text-sm text-gray-600">Model Prediction</div>
          <div className="text-2xl font-bold text-green-600">
            {(prediction.predicted_probability * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white p-3 rounded">
          <div className="text-sm text-gray-600">Market Price</div>
          <div className="text-2xl font-bold text-gray-700">
            {(prediction.market_probability * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="bg-white p-3 rounded mb-4">
        <div className={`text-sm font-semibold ${edgeColor}`}>
          Edge: {edge.edge.toFixed(3)} ({edge.edge_pct.toFixed(1)}%)
        </div>
        <div className="text-sm text-gray-600 mt-1">
          Kelly: {(edge.kelly_fraction * 100).toFixed(1)}%
        </div>
        <div className="text-sm text-gray-600">
          Best Side: {edge.best_side}
        </div>
      </div>

      <button className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition">
        View Details
      </button>
    </div>
  );
};

const EdgeOpportunitiesPanel: React.FC<{ opportunities: EdgeOpportunity[] }> = ({ opportunities }) => {
  const sorted = [...opportunities].sort((a, b) => b.edge_percentage - a.edge_percentage);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 className="text-2xl font-semibold mb-4 text-gray-900">Edge Opportunities</h2>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Metric</th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Direction</th>
              <th className="px-4 py-2 text-right text-sm font-semibold text-gray-700">Edge %</th>
              <th className="px-4 py-2 text-right text-sm font-semibold text-gray-700">Model</th>
              <th className="px-4 py-2 text-right text-sm font-semibold text-gray-700">Market</th>
              <th className="px-4 py-2 text-right text-sm font-semibold text-gray-700">Kelly</th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((opp, idx) => (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">{opp.metric}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-white text-xs font-semibold ${
                    opp.direction === 'YES' ? 'bg-green-500' : 'bg-red-500'
                  }`}>
                    {opp.direction}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right font-semibold">
                  {opp.edge_percentage.toFixed(2)}%
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-700">
                  {(opp.model_prediction * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-700">
                  {(opp.market_price * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-700">
                  {(opp.kelly_fraction * 100).toFixed(2)}%
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    opp.confidence === 'high'
                      ? 'bg-green-100 text-green-800'
                      : opp.confidence === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {opp.confidence}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const FOCMSchedulePanel: React.FC<{ meetings: FOCMMeeting[] }> = ({ meetings }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-gray-900">FOMC Meeting Schedule</h2>

      <div className="space-y-2">
        {meetings.slice(0, 5).map((meeting, idx) => (
          <div key={idx} className="flex justify-between items-center p-3 border rounded hover:bg-gray-50">
            <div>
              <div className="font-semibold text-gray-900">{meeting.description}</div>
              <div className="text-sm text-gray-600">
                Meeting: {new Date(meeting.date).toLocaleDateString()} |
                Decision: {new Date(meeting.decision_date).toLocaleDateString()}
              </div>
            </div>
            <button className="px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition text-sm font-semibold">
              View Market
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EconomicsDashboard;
