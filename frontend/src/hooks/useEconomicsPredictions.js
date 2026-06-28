import { useState, useEffect, useCallback } from 'react';
export const useEconomicsPredictions = (autoRefresh = 60000) => {
    const [cpiPrediction, setCPIPrediction] = useState(null);
    const [rateCutPrediction, setRateCutPrediction] = useState(null);
    const [modelMetrics, setModelMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
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
        }
        catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setError(message);
        }
        finally {
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
        }
        catch (err) {
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
