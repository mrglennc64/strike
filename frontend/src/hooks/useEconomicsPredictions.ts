import { useState, useEffect, useCallback } from 'react';

interface Prediction {
  metric: string;
  predicted_probability: number;
  market_probability: number;
  edge: any;
  latest_value?: number;
  threshold?: number;
}

interface ModelMetrics {
  auc_score: number;
  brier_score: number;
  train_size: number;
  test_size: number;
  created_at: string;
}

interface UseEconomicsPredictionsResult {
  cpiPrediction: Prediction | null;
  rateCutPrediction: Prediction | null;
  modelMetrics: ModelMetrics[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  trainModels: () => Promise<any>;
}

export const useEconomicsPredictions = (
  autoRefresh: number = 60000
): UseEconomicsPredictionsResult => {
  const [cpiPrediction, setCPIPrediction] = useState<Prediction | null>(null);
  const [rateCutPrediction, setRateCutPrediction] = useState<Prediction | null>(null);
  const [modelMetrics, setModelMetrics] = useState<ModelMetrics[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      setLoading(true);
      const [cpiRes, rateRes, metricsRes] = await Promise.all([
        fetch('/api/verticals/economics/predict-cpi'),
        fetch('/api/verticals/economics/predict-rate-cut'),
        fetch('/api/verticals/economics/model-metrics'),
      ]);

      if (!cpiRes.ok || !rateRes.ok) {
        throw new Error('Failed to fetch predictions');
      }

      const cpiData = await cpiRes.json();
      const rateData = await rateRes.json();

      setCPIPrediction(cpiData.data);
      setRateCutPrediction(rateData.data);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setModelMetrics(metricsData.data);
      }

      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const trainModels = useCallback(async () => {
    try {
      const res = await fetch('/api/verticals/economics/train-models', {
        method: 'POST',
      });

      if (!res.ok) {
        throw new Error('Failed to train models');
      }

      const data = await res.json();
      await refetch();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    }
  }, [refetch]);

  useEffect(() => {
    refetch();

    if (autoRefresh > 0) {
      const interval = setInterval(refetch, autoRefresh);
      return () => clearInterval(interval);
    }
  }, [refetch, autoRefresh]);

  return {
    cpiPrediction,
    rateCutPrediction,
    modelMetrics,
    loading,
    error,
    refetch,
    trainModels,
  };
};
