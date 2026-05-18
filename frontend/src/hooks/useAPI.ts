/**
 * Custom React hooks for ARCHE API integration
 */

import { useState, useCallback } from "react";
import {
  getRecommendations,
  explainRecommendation,
  RecommendationResponse,
  ExplanationResponse,
  RecommendPayload,
  ExplainPayload,
} from "../services/api";

export function useRecommendations() {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (payload: RecommendPayload) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getRecommendations(payload);
      setData(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch recommendations";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetch };
}

export function useExplanation() {
  const [data, setData] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (payload: ExplainPayload) => {
    setLoading(true);
    setError(null);
    try {
      const response = await explainRecommendation(payload);
      setData(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch explanation";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetch };
}
