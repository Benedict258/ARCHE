/**
 * ARCHE Backend API Service
 * Connects frontend to backend endpoints: /v1/recommend, /v1/explain, /v1/health
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface IngestPayload {
  user_token: string;
  signal: {
    event_type: string;
    item_token?: string;
    item_category?: string;
    session_context?: Record<string, unknown>;
    engagement_depth?: number;
    dwell_time_seconds?: number;
    sequence_position?: number;
  };
}

export interface RecommendPayload {
  user_token: string;
  n?: number;
  context?: Record<string, unknown>;
}

export interface ExplainPayload {
  recommendation_id: string;
  user_token: string;
}

export interface RecommendationResponse {
  user_token: string;
  simulation_basis: string;
  recommendations: Array<{
    recommendation_id: string;
    item_name: string;
    item_category: string;
    confidence: number;
    recommendation_type: string;
    exploration_factor: string;
    explanation: string;
  }>;
}

export interface ExplanationResponse {
  user_token: string;
  recommendation_id: string;
  simulation: {
    user_token: string;
    simulated_at: string;
    behavioral_snapshot: {
      current_intent: string;
      preference_cluster: string;
      top_affinities: string[];
      rejection_signals: string[];
      engagement_mode: string;
      exploration_readiness: number;
      purchase_probability: number;
    };
    context_modifiers: {
      time_boosts: string[];
      suppressed_categories: string[];
      active_context: string;
    };
    cold_start_confidence: number;
    simulation_basis: string;
    memory_sources: string[];
  };
  recommendation: {
    recommendation_id: string;
    item_name: string;
    item_category: string;
    confidence: number;
    recommendation_type: string;
    exploration_factor: string;
    explanation: string;
  };
  alternatives_considered: Array<{
    recommendation_id: string;
    item_name: string;
    item_category: string;
    confidence: number;
    recommendation_type: string;
    exploration_factor: string;
    explanation: string;
  }>;
  trace: string;
}

export interface HealthResponse {
  status: string;
  version?: string;
}

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/health`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Ingest endpoint - send signals to backend
 */
export async function ingestSignal(payload: IngestPayload): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/v1/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Ingest failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Simulate endpoint - get behavioral snapshot
 */
export async function simulate(userToken: string): Promise<{ historical_memory: Record<string, unknown> }> {
  const response = await fetch(`${API_BASE_URL}/v1/simulate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_token: userToken }),
  });

  if (!response.ok) {
    throw new Error(`Simulate failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Recommend endpoint - get personalized recommendations
 */
export async function getRecommendations(payload: RecommendPayload): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_token: payload.user_token,
      n: payload.n || 5,
      context: payload.context || {},
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Recommend failed: ${error.detail || response.statusText}`);
  }

  return response.json();
}

/**
 * Explain endpoint - get explanation for a recommendation
 */
export async function explainRecommendation(payload: ExplainPayload): Promise<ExplanationResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/explain`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Explain failed: ${error.detail || response.statusText}`);
  }

  return response.json();
}
